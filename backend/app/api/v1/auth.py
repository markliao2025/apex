"""Authentication endpoints — register, login, refresh, me."""

import uuid

from fastapi import APIRouter, HTTPException, status
import jwt

from app.api.dependencies import CurrentUser, DbSession
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
)
from app.models import (
    Constellation,
    Organization,
    OrganizationMembership,
    User,
)
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenPair

router = APIRouter()


def _user_to_out(user: User) -> UserOut:
    """Convert a User ORM instance to a UserOut schema."""
    return UserOut(
        id=str(user.id),
        email=user.email,
        name=user.name,
        plan=user.plan,
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def register(body: UserCreate, db: DbSession) -> UserOut:
    """Register a new user account."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    db.flush()
    org_slug = f"personal-{str(user.id)[:12]}"
    organization = Organization(
        id=uuid.uuid4(),
        slug=org_slug,
        name=f"{body.name or body.email}'s workspace",
    )
    db.add(organization)
    db.flush()
    db.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
        )
    )
    db.add(
        Constellation(
            organization_id=organization.id,
            slug="default",
            name="Default constellation",
            description="Created automatically during registration.",
        )
    )
    db.commit()
    db.refresh(user)
    return _user_to_out(user)


@router.post("/login", response_model=TokenPair, tags=["Authentication"])
async def login(body: UserLogin, db: DbSession) -> TokenPair:
    """Authenticate and return JWT tokens."""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_out(user),
    )


@router.post("/refresh", response_model=TokenPair, tags=["Authentication"])
async def refresh(body: dict, db: DbSession) -> TokenPair:
    """Refresh an access token using a valid refresh token."""
    from app.core.config import get_settings

    settings = get_settings()
    try:
        payload = jwt.decode(
            body.get("refresh_token", ""),
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id_str: str | None = payload.get("sub")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid user ID in token")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token({"sub": str(user.id)})

    return TokenPair(
        access_token=access_token,
        refresh_token=new_refresh,
        user=_user_to_out(user),
    )


@router.get("/me", response_model=UserOut, tags=["Authentication"])
async def get_me(current_user: CurrentUser) -> UserOut:
    """Return the currently authenticated user's profile."""
    return _user_to_out(current_user)
