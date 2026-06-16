from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select   # Sqlalchemy v2 style for data querying
from sqlalchemy.ext.asyncio import AsyncSession  # for Typehints
from sqlalchemy.orm import selectinload    # for eagerloading relationships which is imp for Async

import models
from auth import CurrentUser
from schemas import PostCreate, PostResponse, PostUpdate
from database import get_db


router = APIRouter()    # its a fastapi tool for organizing routes and modules


@router.get('', response_model=list[PostResponse])    
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())   # this tell sqlalchemy to order by date posted in descending order
    )
    posts = result.scalars().all()

    return posts



@router.post(
    '', 
    response_model=PostResponse, 
    status_code=status.HTTP_201_CREATED
)
async def create_post(
    post: PostCreate,
    current_user: CurrentUser,  # if someone calls this endpoint without a valid token they get an Unathorized error even before function begins 
    db: Annotated[AsyncSession, Depends(get_db)],
):  
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = current_user.id,
    )

    db.add(new_post)
    await db.commit()
     # attribute_names loads the relationship as we are returning new_post and it contains author.
     # it removes thhe need for doing select and loading manually
    await db.refresh(new_post, attribute_names=["author"]) 

    return new_post



@router.get(
    '/{post_id}', 
    response_model=PostResponse
)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if post:
        return post
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")



@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, 
    post_data: PostCreate, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
        # 401 means you are not authenticated
        # 403 means user is auhenticated but not Authorized to do this action
    

    post.title = post_data.title
    post.content = post_data.content

    await db.commit()
    await db.refresh(post, attribute_names=["author"])

    return post



@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int, 
    post_data: PostUpdate, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this post")
    
    # To not override the DB with None values in Partial update we use post_data.model_dump(exclude_unset=True)
    update_data = post_data.model_dump(exclude_unset=True)
    for item, value in update_data.items():
        setattr(post, item, value)  # setting the value of item in post dict

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post



@router.delete('/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):

    result = await db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this post")
    
    await db.delete(post)
    await db.commit()