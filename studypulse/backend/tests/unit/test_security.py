"""Unit tests for security utilities (password hashing, JWT tokens)."""
from datetime import timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test that passwords are hashed correctly."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        # Hash should not equal plain password
        assert hashed != password

        # Hash should be non-empty string
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_password_verification_success(self):
        """Test successful password verification."""
        password = "TestPassword456!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self):
        """Test failed password verification with wrong password."""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "SamePassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_empty_password(self):
        """Test handling of empty password."""
        # Should still hash (though not recommended in production)
        hashed = get_password_hash("")
        assert isinstance(hashed, str)

    def test_long_password_handling(self):
        """Test Password truncation at 72 bytes for bcrypt compatibility."""
        # Bcrypt has 72-byte limit
        long_password = "a" * 100
        hashed = get_password_hash(long_password)

        # Should verify with full password
        assert verify_password(long_password, hashed)

        # Should also verify with truncated password (first 72 bytes)
        truncated = long_password[:72]
        assert verify_password(truncated, hashed)

    def test_unicode_password(self):
        """Test password with unicode characters."""
        password = "Пароль123!@#"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_success(self):
        """Test successful token decoding."""
        email = "user@example.com"
        data = {"sub": email}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == email
        assert "exp" in decoded  # Expiration timestamp

    def test_decode_access_token_failure(self):
        """Test token decoding with invalid token."""
        invalid_token = "invalid.token.string"
        decoded = decode_access_token(invalid_token)

        assert decoded is None

    def test_token_expiration(self):
        """Test token with custom expiration."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert "exp" in decoded

    def test_token_with_additional_claims(self):
        """Test token with multiple claims."""
        data = {
            "sub": "user@example.com",
            "role": "admin",
            "user_id": 123
        }

        token = create_access_token(data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == data["sub"]
        assert decoded["role"] == data["role"]
        assert decoded["user_id"] == data["user_id"]

    def test_decode_token_wrong_secret(self):
        """Test decoding token with wrong secret key."""
        data = {"sub": "test@example.com"}

        # Create token with correct secret
        token = jwt.encode(data, "wrong_secret", algorithm=settings.ALGORITHM)

        # Try to decode with app's secret (should fail)
        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_token_wrong_algorithm(self):
        """Test decoding token with wrong algorithm."""
        data = {"sub": "test@example.com"}

        # Create token with different algorithm
        token = jwt.encode(data, settings.SECRET_KEY, algorithm="HS512")

        # Try to decode (should fail due to algorithm mismatch)
        decoded = decode_access_token(token)
        assert decoded is None

    def test_token_without_expiration(self):
        """Test that tokens always have expiration."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert "exp" in decoded
        assert decoded["exp"] > 0


class TestSecurityIntegration:
    """Integration tests for security functions."""

    def test_password_hash_verify_roundtrip(self):
        """Test complete password hash and verify cycle."""
        passwords = [
            "simple",
            "Complex123!@#",
            "Pass with spaces",
            "🔐SecureEmoji",
            "a" * 72  # Max bcrypt length
        ]

        for password in passwords:
            hashed = get_password_hash(password)
            assert verify_password(password, hashed), f"Failed for password: {password}"

    def test_token_create_decode_roundtrip(self):
        """Test complete token creation and decoding cycle."""
        test_data = [
            {"sub": "user1@example.com"},
            {"sub": "user2@example.com", "role": "admin"},
            {"sub": "user3@example.com", "id": 123, "permissions": ["read", "write"]},
        ]

        for data in test_data:
            token = create_access_token(data)
            decoded = decode_access_token(token)

            assert decoded is not None
            for key, value in data.items():
                assert decoded[key] == value
