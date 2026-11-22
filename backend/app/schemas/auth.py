from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str | None = Field(default=None, max_length=160)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str | None):
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)

    @field_validator("full_name")
    @classmethod
    def trim_name(cls, value: str | None):
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
