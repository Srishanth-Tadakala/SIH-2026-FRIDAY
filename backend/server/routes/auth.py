"""Authentication & User Identity API Endpoints for F.R.I.D.A.Y. Platform.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.
"""

from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from ..auth import (
    LoginRequest,
    ROLE_HIERARCHY,
    TokenResponse,
    User,
    UserInDB,
    UserRole,
    _USERS_DB,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
)
from ..config import get_settings

router = APIRouter(prefix="/api/auth", tags=["Authentication & Identity"])


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.OPERATOR
    full_name: str | None = None
    station_id: str | None = None


@router.post("/login", response_model=TokenResponse)
def login_for_access_token(credentials: LoginRequest) -> TokenResponse:
    """Authenticate with username and password to receive a JWT access token."""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user)
    settings = get_settings()
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/token", response_model=TokenResponse)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """OAuth2 standard password request form for token retrieval."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(user)
    settings = get_settings()
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=User)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile and operational role of the currently authenticated user."""
    return current_user


@router.get("/roles")
def get_operational_roles() -> dict[str, Any]:
    """List all available operational roles and their permission hierarchies."""
    return {
        "roles": [r.value for r in UserRole],
        "hierarchy": {r.value: weight for r, weight in ROLE_HIERARCHY.items()},
        "descriptions": {
            "VIEWER": "Read-only telemetry and agent swarm status observation",
            "OPERATOR": "Simulation scenarios, telemetry ingestion, Tier 1 auto-governor operations",
            "ENGINEER": "Station maintenance, Tier 2 supervised actions, equipment parameter overrides",
            "COMMANDER": "Full expedition authority, Tier 3 emergency action authorization with PIN",
            "ADMIN": "Platform administration, user management, secret key rotation, system reset",
        },
    }


@router.post("/users", response_model=User, dependencies=[Depends(require_role(UserRole.ADMIN))])
def create_operational_user(new_user: UserCreateRequest) -> User:
    """Register a new operational user account (Requires ADMIN privileges)."""
    if new_user.username in _USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{new_user.username}' already exists.",
        )
    salt_hex, hash_hex = hash_password(new_user.password)
    user_db = UserInDB(
        username=new_user.username,
        role=new_user.role,
        full_name=new_user.full_name,
        station_id=new_user.station_id,
        is_active=True,
        salt_hex=salt_hex,
        password_hash_hex=hash_hex,
    )
    _USERS_DB[new_user.username] = user_db
    return User(
        username=user_db.username,
        role=user_db.role,
        station_id=user_db.station_id,
        is_active=user_db.is_active,
        full_name=user_db.full_name,
    )
