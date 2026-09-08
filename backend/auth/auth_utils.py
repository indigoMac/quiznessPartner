from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic_settings import BaseSettings

BCRYPT_MAX_PASSWORD_BYTES = 72


class AuthSettings(BaseSettings):
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    class Config:
        env_file = ".env"


settings = AuthSettings()


def _password_bytes(password: str) -> bytes:
    """bcrypt only uses the first 72 bytes of a password."""
    return password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        _password_bytes(plain_password), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
