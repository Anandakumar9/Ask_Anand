"""Security utilities for authentication and authorization."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from .config import settings
import re


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength based on security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check minimum length
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters long"

    # Check for at least one digit
    if settings.REQUIRE_PASSWORD_DIGIT and not re.search(r"\d", password):
        return False, "Password must contain at least one digit (0-9)"

    # Check for at least one special character
    if settings.REQUIRE_PASSWORD_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"

    # Check for at least one letter
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter"

    return True, ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash - uses bcrypt directly."""
    # Bcrypt has a 72-byte limit, truncate the password to 72 bytes
    password_bytes = plain_password[:72].encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storing - uses bcrypt directly."""
    # Bcrypt has a 72-byte limit, truncate the password to 72 bytes
    password_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
