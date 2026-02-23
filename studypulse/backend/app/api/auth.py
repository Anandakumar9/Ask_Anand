"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import httpx

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, TokenResponse
from app.middleware.rate_limiter import limiter, auth_limit, guest_limit

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/guest", response_model=TokenResponse)
@limiter.limit(guest_limit)
async def guest_login(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Auto-login as guest user. Creates a guest user if it doesn't exist.
    
    This allows the mobile app to work without requiring registration.
    Returns a valid JWT token for API access.
    """
    # Check if guest user exists
    result = await db.execute(select(User).where(User.email == "guest@studypulse.com"))
    guest = result.scalar_one_or_none()
    
    if not guest:
        # Create guest user
        guest = User(
            email="guest@studypulse.com",
            name="Guest User",
            hashed_password=get_password_hash("guest-no-login-required"),
            is_active=True,
            total_stars=0
        )
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(guest.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(guest)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(auth_limit)
async def register(request: Request, user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **name**: User's display name
    - **password**: Strong password
    - **phone**: Optional phone number
    - **target_exam_id**: Optional target exam ID
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists (if provided)
    if user_data.phone:
        result = await db.execute(select(User).where(User.phone == user_data.phone))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Validate password strength
    from app.core.security import validate_password_strength

    valid, msg = validate_password_strength(user_data.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        target_exam_id=user_data.target_exam_id
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit(auth_limit)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    Use email as username in the form.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    update_data = user_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Note: Since we use JWT, actual logout is handled client-side
    by deleting the token. This endpoint is for future features.
    """
    return {"message": "Successfully logged out"}


@router.post("/google", response_model=TokenResponse)
@limiter.limit(auth_limit)
async def google_auth(
    request: Request,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with Google via Supabase access token.

    Client passes the Supabase access_token obtained after Google OAuth.
    We verify it with Supabase, extract the user's email + name, then
    create-or-fetch our own User record and return a StudyPulse JWT.
    """
    supabase_token = payload.get("access_token")
    if not supabase_token:
        raise HTTPException(status_code=400, detail="access_token required")

    supabase_url = getattr(settings, "SUPABASE_URL", None)
    if not supabase_url:
        raise HTTPException(status_code=501, detail="Google auth not configured on server")

    # Verify token with Supabase and get user info
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{supabase_url}/auth/v1/user",
            headers={"Authorization": f"Bearer {supabase_token}",
                     "apikey": getattr(settings, "SUPABASE_SERVICE_KEY", "")},
            timeout=10,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    supa_user = resp.json()
    email: str = supa_user.get("email", "")
    name: str = (
        supa_user.get("user_metadata", {}).get("full_name")
        or supa_user.get("user_metadata", {}).get("name")
        or email.split("@")[0]
    )
    avatar_url: str = supa_user.get("user_metadata", {}).get("avatar_url", "")

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name=name,
            hashed_password=get_password_hash(supa_user.get("id", email)),  # unusable password
            avatar_url=avatar_url,
            is_active=True,
            total_stars=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


async def _ensure_supabase_user(email: str, supabase_url: str, service_key: str) -> Optional[str]:
    """Create or find user in Supabase auth. Returns their Supabase UID or None on failure."""
    headers = {"Authorization": f"Bearer {service_key}", "apikey": service_key}
    async with httpx.AsyncClient() as client:
        # Check if user already exists in Supabase
        search = await client.get(
            f"{supabase_url}/auth/v1/admin/users",
            headers=headers,
            params={"page": 1, "per_page": 1, "filter": email},
            timeout=10,
        )
        if search.status_code == 200:
            users = search.json().get("users", [])
            existing = next((u for u in users if u.get("email") == email), None)
            if existing:
                return existing["id"]

        # Create new Supabase auth user (email_confirm=True skips email verification)
        create = await client.post(
            f"{supabase_url}/auth/v1/admin/users",
            headers=headers,
            json={"email": email, "email_confirm": True, "password": None},
            timeout=10,
        )
        if create.status_code in (200, 201):
            return create.json().get("id")
    return None


@router.post("/forgot-password")
@limiter.limit(auth_limit)
async def forgot_password(
    request: Request,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset.
    Syncs user to Supabase auth (creates them if needed), then triggers Supabase recovery email.
    Always returns success to prevent email enumeration.
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="email required")

    supabase_url = getattr(settings, "SUPABASE_URL", None)
    service_key = getattr(settings, "SUPABASE_SERVICE_KEY", None)

    if not supabase_url or not service_key:
        raise HTTPException(status_code=501, detail="Password reset not configured on server")

    # Only process if user exists in our DB (silent success if not, to prevent enumeration)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Ensure user exists in Supabase auth so recovery email can be sent
        await _ensure_supabase_user(email, supabase_url, service_key)

        # Trigger Supabase recovery email
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{supabase_url}/auth/v1/recover",
                headers={"apikey": service_key, "Content-Type": "application/json"},
                json={"email": email},
                timeout=10,
            )

    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit(auth_limit)
async def reset_password(
    request: Request,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete password reset.
    Receives Supabase recovery access_token + new_password.
    Verifies token with Supabase, then updates our DB password hash.
    """
    access_token = payload.get("access_token")
    new_password = payload.get("new_password")

    if not access_token or not new_password:
        raise HTTPException(status_code=400, detail="access_token and new_password required")

    supabase_url = getattr(settings, "SUPABASE_URL", None)
    service_key = getattr(settings, "SUPABASE_SERVICE_KEY", None)

    if not supabase_url or not service_key:
        raise HTTPException(status_code=501, detail="Password reset not configured")

    # Verify the recovery token and get user email from Supabase
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{supabase_url}/auth/v1/user",
            headers={"Authorization": f"Bearer {access_token}", "apikey": service_key},
            timeout=10,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired reset token")

    email = resp.json().get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Could not verify identity")

    # Validate new password
    from app.core.security import validate_password_strength
    valid, msg = validate_password_strength(new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # Update password in our DB
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(new_password)
    await db.commit()

    return {"message": "Password updated successfully"}
