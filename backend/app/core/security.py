from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.tenant import Organization, User, UserRole


bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[Session, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if not 12 <= len(password_bytes) <= 72:
        raise ValueError(
            "Password must contain between 12 and 72 UTF-8 bytes."
        )

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    password_bytes = plain_password.encode("utf-8")

    if len(password_bytes) > 72:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    claims = {
        **data,
        "iat": now,
        "exp": now + lifetime,
    }

    return jwt.encode(
        claims,
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session is invalid or has expired. Sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: BearerCredentials,
    db: DatabaseSession,
) -> User:
    if credentials is None:
        raise authentication_error()

    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "require": ["exp", "iat", "sub", "org_id"],
            },
        )
    except InvalidTokenError as error:
        raise authentication_error() from error

    user_id = claims.get("sub")
    organization_id = claims.get("org_id")

    if (
        not isinstance(user_id, str)
        or not isinstance(organization_id, str)
    ):
        raise authentication_error()

    user = (
        db.query(User)
        .join(
            Organization,
            Organization.id == User.organization_id,
        )
        .filter(
            User.id == user_id,
            User.organization_id == organization_id,
            User.is_active.is_(True),
            Organization.is_active.is_(True),
        )
        .first()
    )

    if user is None:
        raise authentication_error()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_operator(user: CurrentUser) -> User:
    permitted_roles = {
        UserRole.ADMIN,
        UserRole.AGENT_OPERATOR,
    }

    if user.role not in permitted_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An operator account is required.",
        )

    return user


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An administrator account is required.",
        )

    return user