from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models import RevokedToken, User

password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "researchgpt"


def _secret_key() -> str:
    secret = settings.jwt_secret_key
    if len(secret) < 32 or secret.startswith("replace-with-"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set JWT_SECRET_KEY to at least 32 random characters.",
        )
    return secret


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user: User) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    jti = str(uuid4())
    payload = {
        "sub": str(user.id),
        "jti": jti,
        "iat": now,
        "exp": expires_at,
        "iss": JWT_ISSUER,
    }
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM), jti, expires_at


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            _secret_key(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "jti", "iss"]},
        )
    except jwt.InvalidTokenError:
        raise unauthorized from None
    if db.get(RevokedToken, payload["jti"]) is not None:
        raise unauthorized
    return payload


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    try:
        user_id = UUID(payload["sub"])
        user = db.get(User, user_id)
    except (ValueError, TypeError):
        user = None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
