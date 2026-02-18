"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Body
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
async def guest_login(db: AsyncSession = Depends(get_db)):
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
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
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
async def login(
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
async def google_auth(
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
