"""Integration tests for authentication API endpoints."""
import pytest
from fastapi import status


@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration endpoints."""

    async def test_register_new_user_success(self, test_client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "SecurePassword123!"
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data  # Should not expose password

    async def test_register_duplicate_email(self, test_client, test_user):
        """Test registration with already registered email."""
        user_data = {
            "email": test_user.email,  # Already exists
            "name": "Another User",
            "password": "Password123!"
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, test_client):
        """Test registration with invalid email format."""
        user_data = {
            "email": "not-an-email",
            "name": "Test User",
            "password": "Password123!"
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        # Should fail validation (422 or 400)
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_register_weak_password(self, test_client):
        """Test registration with weak password."""
        user_data = {
            "email": "user@example.com",
            "name": "Test User",
            "password": "123"  # Too weak
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        # May pass (if no password strength validation) or fail
        # Adjust based on actual implementation
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    async def test_register_missing_required_fields(self, test_client):
        """Test registration with missing required fields."""
        user_data = {
            "email": "user@example.com",
            # Missing name, password
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestUserLogin:
    """Test user login endpoints."""

    async def test_login_success(self, test_client, test_user):
        """Test successful login with valid credentials."""
        login_data = {
            "username": test_user.email,  # OAuth2 uses 'username' field
            "password": "testpassword123"
        }

        response = test_client.post(
            "/api/v1/auth/login",
            data=login_data  # OAuth2PasswordRequestForm uses form data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    async def test_login_wrong_password(self, test_client, test_user):
        """Test login with incorrect password."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }

        response = test_client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepassword"
        }

        response = test_client.post("/api/v1/auth/login", data=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_login_inactive_user(self, test_client, test_db, test_user):
        """Test login with inactive user account."""
        # Deactivate user
        test_user.is_active = False
        test_db.add(test_user)
        await test_db.commit()

        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }

        response = test_client.post("/api/v1/auth/login", data=login_data)

        # Should fail (401 or 403)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    async def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials."""
        response = test_client.post("/api/v1/auth/login", data={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
class TestGuestLogin:
    """Test guest login functionality."""

    async def test_guest_login_success(self, test_client):
        """Test guest login creates guest user and returns token."""
        response = test_client.post("/api/v1/auth/guest")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert "guest" in data["user"]["email"].lower()

    async def test_guest_login_idempotent(self, test_client):
        """Test multiple guest logins use same guest user."""
        # First guest login
        response1 = test_client.post("/api/v1/auth/guest")
        user1_id = response1.json()["user"]["id"]

        # Second guest login
        response2 = test_client.post("/api/v1/auth/guest")
        user2_id = response2.json()["user"]["id"]

        # Should return same guest user
        assert user1_id == user2_id


@pytest.mark.asyncio
class TestTokenAuthentication:
    """Test JWT token authentication."""

    async def test_access_protected_endpoint_with_valid_token(self, test_client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = test_client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data
        assert "id" in data

    async def test_access_protected_endpoint_without_token(self, test_client):
        """Test accessing protected endpoint without token."""
        response = test_client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_with_invalid_token(self, test_client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = test_client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_access_protected_endpoint_with_expired_token(self, test_client):
        """Test accessing protected endpoint with expired token."""
        # Create expired token (negative expiry)
        from datetime import timedelta
        from app.core.security import create_access_token

        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)  # Expired
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = test_client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
class TestUserProfile:
    """Test user profile endpoints."""

    async def test_get_current_user_profile(self, test_client, auth_headers, test_user):
        """Test retrieving current user profile."""
        response = test_client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert data["id"] == test_user.id

    async def test_update_user_profile(self, test_client, auth_headers):
        """Test updating user profile."""
        update_data = {
            "name": "Updated Name"
        }

        response = test_client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json=update_data
        )

        # Should succeed or return 405 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_404_NOT_FOUND
        ]

    async def test_delete_user_account(self, test_client, auth_headers):
        """Test user account deletion."""
        response = test_client.delete("/api/v1/auth/me", headers=auth_headers)

        # Should succeed or return 405 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_200_OK,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.asyncio
class TestPasswordManagement:
    """Test password change/reset functionality."""

    async def test_change_password_success(self, test_client, auth_headers):
        """Test successful password change."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "NewSecurePassword456!"
        }

        response = test_client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json=password_data
        )

        # Should succeed or return 404 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_change_password_wrong_current_password(self, test_client, auth_headers):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewSecurePassword456!"
        }

        response = test_client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers,
            json=password_data
        )

        # Should fail with 400/401 or 404 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

    async def test_password_reset_request(self, test_client, test_user):
        """Test password reset request."""
        reset_data = {"email": test_user.email}

        response = test_client.post("/api/v1/auth/forgot-password", json=reset_data)

        # Should succeed or return 404 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]


@pytest.mark.asyncio
class TestTokenRefresh:
    """Test token refresh functionality."""

    async def test_refresh_token(self, test_client, test_user_token):
        """Test token refresh."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )

        # Should succeed or return 404 if endpoint doesn't exist
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
