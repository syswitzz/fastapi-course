import jwt
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from pwdlib import PasswordHash
from config import settings

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from datetime import UTC, datetime, timedelta

import models
from database import get_db


# Why hashing and not encryption?
# Encryption is reversible, Hashing is not. even if db is stolen password can be recovered from hashes
# argon2 generates random salt for same password. each is unique. 


password_hasher = PasswordHash.recommended()
# OAuth2PasswordBearer extracts the token from authorization header. it also enables auth button in docs
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")  # token url has to match login endpoint path


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data:dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes = settings.access_token_expire_minutes,
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),   # since secret_key is a SecretStr, we need to call get_secret_value() to get the actual string value
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_access_token(token:str) -> str | None:   # None if token is invalid 
    """Verifies a JWT token and returns the user id if it is valid"""

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["exp", "sub"]}     # we will store user id in 'sub' 
        )
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> models.User:
    '''Any route that uses this Dependency will automatically require a valid token and get access to the full User object'''
     
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    result = await db.execute(
        select(models.User).where(models.User.id == user_id),
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[models.User, Depends(get_current_user)]

# Annotated - is for typehinting it tells that "CurrentUser" is a "models.User" object
# Depends - and the metadata for the "models.User" depends on "get_current_user" 