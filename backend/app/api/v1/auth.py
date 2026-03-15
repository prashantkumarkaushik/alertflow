import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models.team import Team
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def slugify(text: str) -> str:
    """Convert team name to URL-safe slug. e.g. 'My Team' -> 'my-team'"""
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, db: DBSession):
    """
    Register a new user and create their team.
    Each registration creates a fresh team — users join existing
    teams via invite (future feature).
    """
    # Check email not already taken
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create team
    slug = slugify(payload.team_name)

    # Ensure slug is unique
    result = await db.execute(select(Team).where(Team.slug == slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already taken",
        )

    team = Team(name=payload.team_name, slug=slug)
    db.add(team)
    await db.flush()  # flush to get team.id without committing

    # Create user
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        team_id=team.id,
        is_superuser=True,  # first user of a team is admin
    )
    db.add(user)
    await db.flush()

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
):
    """Login — accepts form data (works with Swagger UI Authorize button)."""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    token = create_access_token(user_id=user.id, team_id=user.team_id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Return the currently logged in user."""
    return current_user
