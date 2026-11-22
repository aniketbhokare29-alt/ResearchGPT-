from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, get_token_payload, hash_password, verify_password
from app.database.session import get_db
from app.models import RevokedToken, User
from app.schemas.auth import AuthResponse, LoginRequest, ProfileUpdate, RegisterRequest, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])


def _auth_response(user: User, token: str | None = None) -> AuthResponse:
    if token is None:
        token, _jti, _expires_at = create_access_token(user)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = User(email=email, password_hash=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    try:
        db.flush()
        token, _jti, _expires_at = create_access_token(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    db.refresh(user)
    return _auth_response(user, token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _auth_response(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: dict = Depends(get_token_payload),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(timezone.utc)))
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    db.add(RevokedToken(jti=payload["jti"], user_id=user.id, expires_at=expires_at))
    db.commit()


@router.get("/me", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.full_name = payload.full_name
    db.commit()
    db.refresh(user)
    return user
