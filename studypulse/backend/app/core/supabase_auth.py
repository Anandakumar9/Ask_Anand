"""Supabase Auth integration for production authentication."""
from typing import Optional
from fastapi import HTTPException, status
from supabase import create_client, Client
from .config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseAuth:
    """Supabase authentication service."""

    def __init__(self):
        """Initialize Supabase client."""
        try:
            self.client: Client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    async def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify Supabase JWT token and return user data.

        Args:
            token: JWT token from client

        Returns:
            User data dict if valid, None if invalid
        """
        try:
            # Get user from token using Supabase
            user = self.client.auth.get_user(token)

            if user and user.user:
                return {
                    "id": user.user.id,
                    "email": user.user.email,
                    "email_confirmed_at": user.user.email_confirmed_at,
                    "phone": user.user.phone,
                    "created_at": user.user.created_at,
                    "user_metadata": user.user.user_metadata,
                    "app_metadata": user.user.app_metadata
                }
            return None
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    async def sign_up(self, email: str, password: str, metadata: dict = None) -> dict:
        """
        Register new user with email/password.

        Args:
            email: User email
            password: User password
            metadata: Additional user metadata

        Returns:
            User data and session
        """
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })

            if response.user:
                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed_at": response.user.email_confirmed_at
                    },
                    "session": {
                        "access_token": response.session.access_token if response.session else None,
                        "refresh_token": response.session.refresh_token if response.session else None
                    }
                }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        except Exception as e:
            logger.error(f"Sign up failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def sign_in(self, email: str, password: str) -> dict:
        """
        Sign in user with email/password.

        Args:
            email: User email
            password: User password

        Returns:
            User data and session tokens
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if response.session:
                return {
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "user_metadata": response.user.user_metadata
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    }
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        except Exception as e:
            logger.error(f"Sign in failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

    async def refresh_session(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token from previous session

        Returns:
            New session with fresh access token
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)

            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def sign_out(self, access_token: str) -> bool:
        """
        Sign out user and invalidate session.

        Args:
            access_token: Current access token

        Returns:
            True if successful
        """
        try:
            self.client.auth.sign_out()
            return True
        except Exception as e:
            logger.error(f"Sign out failed: {e}")
            return False

    async def get_oauth_url(self, provider: str, redirect_to: str) -> str:
        """
        Get OAuth URL for social authentication.

        Args:
            provider: OAuth provider (google, github, apple)
            redirect_to: URL to redirect after auth

        Returns:
            OAuth authorization URL
        """
        try:
            response = self.client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_to
                }
            })
            return response.url
        except Exception as e:
            logger.error(f"OAuth URL generation failed for {provider}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth setup failed for {provider}"
            )


# Global Supabase auth instance
supabase_auth = SupabaseAuth()
