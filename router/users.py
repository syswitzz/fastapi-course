from typing import Annotated
from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select, func   # select - Sqlalchemy v2 style for data querying, func - for case-insensitive sql queries
from sqlalchemy.ext.asyncio import AsyncSession  # for Typehints
from sqlalchemy.orm import selectinload    # for eagerloading relationships which is imp for Async

import models
from database import get_db
from schemas import UserCreate, UserPublic, UserPrivate, Token, UserUpdate, PostResponse
from auth import hash_password, CurrentUser, create_access_token, verify_password
from config import settings

router = APIRouter()    # here, @router.get("/example") == @app.get("/api/users/example")


@router.post(
    '',
    response_model = UserPrivate,
    status_code= status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):  
    # we use Annotated to combine typehinting and dependency injection.
    # db: Annotated[Session, Depends(get_db)] calls get_db() gives a session to this route and cleans up.
    # user: UserCreate is for request body validation  
    
    # check if username already exists - DB already has a unique constraint so its not like we can add a duplicate user anyway
    result = await db.execute(
        select(models.User)
        .where(func.lower(models.User.username) ==  user.username.lower())  # we cannot directly use lower as its not a strs or func.lower() - case insensitive search for username
    )
    existing_user = result.scalars().first()  # gives first user object or None if no such user exist
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # check if email already exists
    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) ==  user.email.lower( ))
    )
    existing_email = result.scalars().first() 
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    
    new_user = models.User(
        username = user.username,   # we dont wanna lowercase username cuz if someone enters "Sam" we shouldnt show them "sam"
        email = user.email.lower(),
        password_hash= hash_password(user.password),
    )

    db.add(new_user)    # we dont use await here because it just adds the object to to session pending list. it doesnt do any I/O
    await db.commit()     # executes and saves to the db
    await db.refresh(new_user)    # reloads the object from db

    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Looks up user by email (case-insensitive)
    # OAuth2PasswordRequestForm uses "username" field, but treat is as email
    
    result = await db.execute(
        select(models.User).where(models.User.email == form_data.username.lower())
    )
    user = result.scalars().first()

    # Verify user and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data = {"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    return Token(token_type="bearer", access_token=access_token)


@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user

    
@router.get(
    '/{user_id}',
    response_model=UserPublic
)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if user:
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )



@router.get(
    "/{user_id}/posts",
    response_model=list[PostResponse]
)
async def get_user_posts(user_id:int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "User not found",
        )
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()
    return posts



@router.patch('/{user_id}', response_model=UserPrivate)
async def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user")
    
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.username is not None and user_data.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User)
            .where(func.lower(models.User.username) == user_data.username.lower())
        )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        user.username = user_data.username
        
    if user_data.email is not None and user_data.email.lower() != user.email.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.email) == user_data.email.lower()))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        user.email = user_data.email.lower()

    if user_data.image_file is not None:
        user.image_file = user_data.image_file

    await db.commit()
    await db.refresh(user)
    return user



@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    '''This function also cascade deletes the User's posts (Most real world routers use this)'''
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user."
        )
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)   # db.add() doesnt need await but db.delete() does
    await db.commit()