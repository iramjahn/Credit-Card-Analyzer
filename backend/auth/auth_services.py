# backend/auth/auth_services.py

import bcrypt
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from backend.database.models import User
from backend.auth.jwt_handler import JWTHandler
from backend.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS


def _get_jwt_handler() -> JWTHandler:
    return JWTHandler(secret_key=JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def signup(
    db: Session,
    email: str,
    password: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[User]]:
    if not email or "@" not in email:
        return False, "Invalid email address", None
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters", None

    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        return False, "Email already registered", None

    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return True, None, user


def login(
    db: Session, email: str, password: str
) -> Tuple[bool, Optional[str], Optional[str]]:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        return False, "Invalid email or password", None

    token = _get_jwt_handler().create_token(user.id, expires_in_days=JWT_EXPIRE_DAYS)
    return True, None, token


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()
