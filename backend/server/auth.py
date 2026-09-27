"""Authentication and Role-Based Access Control (RBAC) System for F.R.I.D.A.Y.

Part of SIH 2026 Project SIH26060: F.R.I.D.A.Y.
Digital Platform for Efficient Remote Management of Indian Antarctic Research Stations.

Security Architecture:
- Cryptographic JWT bearer tokens (HS256 signed)
- Multi-tier RBAC hierarchy: VIEWER -> OPERATOR -> ENGINEER -> COMMANDER -> ADMIN
- Salted PBKDF2-HMAC-SHA256 password hashing
- Station-specific operational scoping
- FastAPI dependency injection guards
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import hmac
import os
import secrets
from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
import jwt

from .config import get_settings


class UserRole(str, Enum):
    """Hierarchical operational roles for Antarctic station remote management."""
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    ENGINEER = "ENGINEER"
    COMMANDER = "COMMANDER"
    ADMIN = "ADMIN"


ROLE_HIERARCHY: Dict[UserRole, int] = {
    UserRole.VIEWER: 1,
    UserRole.OPERATOR: 2,
    UserRole.ENGINEER: 3,
    UserRole.COMMANDER: 4,
    UserRole.ADMIN: 5,
}


class User(BaseModel):
    """Authenticated user representation in memory/tokens."""
    username: str
    role: UserRole = UserRole.VIEWER
    station_id: Optional[str] = None  # None = dual station access
    is_active: bool = True
    full_name: Optional[str] = None


class UserInDB(User):
    """User representation with stored password salt and hash."""
    salt_hex: str
    password_hash_hex: str


class TokenResponse(BaseModel):
    """JWT Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: User


class LoginRequest(BaseModel):
    """Login credentials schema."""
    username: str
    password: str


# In-memory user directory for station operations
_USERS_DB: Dict[str, UserInDB] = {}


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Generate salted PBKDF2-HMAC-SHA256 hash and return (salt_hex, hash_hex)."""
    if salt is None:
        salt = secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex(), pw_hash.hex()


def verify_password(plain_password: str, salt_hex: str, hash_hex: str) -> bool:
    """Constant-time PBKDF2 password verification."""
    try:
        salt = bytes.fromhex(salt_hex)
        candidate = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(candidate.hex(), hash_hex)
    except Exception:
        return False


def _seed_default_users() -> None:
    """Seed initial operational accounts into in-memory store."""
    default_accounts = [
        ("viewer", "viewer123", UserRole.VIEWER, "Antarctic Science Observer"),
        ("operator", "operator123", UserRole.OPERATOR, "Station Duty Operations Officer"),
        ("engineer", "engineer123", UserRole.ENGINEER, "Station Life-Support Systems Engineer"),
        ("commander", "commander123", UserRole.COMMANDER, "Station Commander / Expedition Leader"),
        ("admin", "admin123", UserRole.ADMIN, "F.R.I.D.A.Y. Mission Systems Administrator"),
    ]
    for username, password, role, full_name in default_accounts:
        if username not in _USERS_DB:
            salt_hex, hash_hex = hash_password(password)
            _USERS_DB[username] = UserInDB(
                username=username,
                role=role,
                full_name=full_name,
                is_active=True,
                salt_hex=salt_hex,
                password_hash_hex=hash_hex,
            )


# Initialize default user store
_seed_default_users()


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token for the given user."""
    settings = get_settings()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": user.username,
        "role": user.role.value,
        "station_id": user.station_id,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please authenticate again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
            headers={"WWW-Authenticate": "Bearer"},
        )


http_bearer = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> Optional[User]:
    """Retrieve current user from bearer token, or None if unauthenticated."""
    if not credentials or not credentials.credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    role_str = payload.get("role", UserRole.VIEWER.value)
    station_id = payload.get("station_id")

    if username and username in _USERS_DB:
        user_db = _USERS_DB[username]
        return User(
            username=user_db.username,
            role=user_db.role,
            station_id=user_db.station_id,
            is_active=user_db.is_active,
            full_name=user_db.full_name,
        )

    # Allow custom token payload if validly signed
    try:
        role = UserRole(role_str)
    except ValueError:
        role = UserRole.VIEWER

    return User(
        username=username or "anonymous",
        role=role,
        station_id=station_id,
        is_active=True,
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> User:
    """Enforce valid authentication and return the current user."""
    user = get_current_user_optional(credentials)
    if user:
        return user

    # If in development or testing mode and no token was provided, allow fallback to test user
    settings = get_settings()
    if settings.ENVIRONMENT in ("development", "testing") and not credentials:
        # Fallback to default engineer in dev/test to maintain backwards compatibility
        return User(
            username="dev_engineer",
            role=UserRole.ENGINEER,
            full_name="Local Dev Engineer",
            is_active=True,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(minimum_role: UserRole) -> Callable[[User], User]:
    """FastAPI dependency factory enforcing a minimum hierarchical role."""
    def dependency(user: User = Depends(get_current_user)) -> User:
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires at least '{minimum_role.value}' role, user has '{user.role.value}'.",
            )
        return user

    return dependency


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Verify username and password against user directory."""
    user_db = _USERS_DB.get(username)
    if not user_db or not user_db.is_active:
        return None
    if verify_password(password, user_db.salt_hex, user_db.password_hash_hex):
        return User(
            username=user_db.username,
            role=user_db.role,
            station_id=user_db.station_id,
            is_active=user_db.is_active,
            full_name=user_db.full_name,
        )
    return None
