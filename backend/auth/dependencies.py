from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db_utils import get_db
from models.user import User

from .auth_utils import verify_token

# For required authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# For optional authentication (allows anonymous access)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated and active user.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_optional_user(
    token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
) -> Union[User, None]:
    """
    Get the current user if authenticated, otherwise return None.
    This allows endpoints to work with both authenticated and anonymous users.
    """
    if not token:
        return None

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None or not user.is_active:
            return None
        return user
    except Exception:
        # Invalid token, return None for anonymous access
        return None
