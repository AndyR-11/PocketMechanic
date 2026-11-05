from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi import Cookie, Response
from app.schemas.user import UserLogin
from app.services.auth_service import (
    login_user, logout_user, get_current_user
)
from app.models.user import User

from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    return register_user(db, user_data)


@router.post("/login", response_model=UserResponse)
def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    session = login_user(
        db, credentials.email, credentials.password
    )

    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        secure=False,  # Local HTTP development only
        samesite="lax",
        max_age=7 * 24 * 60 * 60
    )

    return db.get(User, session.user_id)


@router.post("/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
):
    logout_user(db, session_id)
    response.delete_cookie("session_id")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
