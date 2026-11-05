from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from fastapi import Cookie, Depends
from app.db.database import get_db
from app.models.user_session import UserSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

password_hasher = PasswordHash.recommended()


def update_user_info(db: Session, user_id: int, data: UserUpdate) -> User:
    # Contract 1 (UpdateUserInfo)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Precondition: Email must not belong to another user.
    changes = data.model_dump(exclude_unset=True)
    new_email = changes.get("email")
    if new_email is not None:
        existing_user = db.scalar(
            select(User).where(User.email == new_email, User.id != user_id)
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered"
            )

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    # Postcondition: The stored name and email match the request.
    return user


def register_user(db: Session, user_data: UserCreate) -> User:
    # Contract 3 (RegisterUser)
    # Precondition: Email must not already be registered.
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # Hash password before storing it.
    hashed_password = password_hasher.hash(user_data.password)

    user = User(
        name=user_data.name.strip(),
        email=user_data.email,
        password_hash=hashed_password
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    # Postcondition: User has an ID and a stored password hash.
    return user


def login_user(db: Session, email: str, password: str) -> UserSession:
    # Contract 4 (LoginUser): invalid credentials raise a 401.
    user = db.scalar(select(User).where(User.email == email))

    if user is None or not password_hasher.verify(
        password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    session = UserSession(
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db)
) -> User:
    # Contracts 2 (GetUserInfo) and 6 (GetCurrentUser)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session = db.get(UserSession, session_id)

    if session is None or session.expires_at.replace(
        tzinfo=timezone.utc
    ) <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )

    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def logout_user(db: Session, session_id: str | None):
    # Contract 5 (LogoutUser)
    if session_id:
        session = db.get(UserSession, session_id)
        if session:
            db.delete(session)
            db.commit()