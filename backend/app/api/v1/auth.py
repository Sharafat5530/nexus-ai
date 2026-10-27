from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.database import get_db
from app.models.tenant import Organization, User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    role: str
    organization_id: str
    organization_name: str


def invalid_login() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == str(payload.email))
        .first()
    )

    if user is None:
        raise invalid_login()

    if not verify_password(payload.password, user.hashed_password):
        raise invalid_login()

    organization = (
        db.query(Organization)
        .filter(
            Organization.id == user.organization_id,
            Organization.is_active.is_(True),
        )
        .first()
    )

    if not user.is_active or organization is None:
        raise invalid_login()

    access_token = create_access_token(
        data={
            "sub": user.id,
            "org_id": organization.id,
        }
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role.value,
        organization_id=organization.id,
        organization_name=organization.name,
    )


@router.get("/me")
def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "organization_id": current_user.organization_id,
    }