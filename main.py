from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException, status   # Depends - this is how we inject database sessions in our routes
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
# from fastapi.responses import JSONResponse :- we were using this in exception handlers. but now we are using default async exception handlers

from sqlalchemy import select   # Sqlalchemy v2 style for data querying
from sqlalchemy.ext.asyncio import AsyncSession  # for Typehints
from sqlalchemy.orm import selectinload    # for eagerloading relationships which is imp for Async

import models
from database import Base, engine, get_db   # Base, engine - creating tables. get_db - provides DB sessions
from router import users, posts


# Lifespan is a modern way in fastapi to handle startup and shutdown events. replaces older decoreator on_startup, on_shutdown
@asynccontextmanager
async def lifespan(_app: FastAPI):
    '''this function is only for creating databse tables'''
    # Startup
    async with engine.begin() as conn:  # engine.begin() - get an async connection
        await conn.run_sync(Base.metadata.create_all)   # this runs sync create_all inside our async context
    yield   # this is where our app actually runs

    # Shutdown
    await engine.dispose()



app = FastAPI(lifespan=lifespan)


# templates allow us to serve html files and just pass in our dynamic data 
# because containing all html in a python string would be horrible, 
# while still maintaining json endpoints for the backend api
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(users.router, prefix="/api/users", tags=['users'])   # tags organize the /docs page
app.include_router(posts.router, prefix="/api/posts", tags=['posts'])



#<------------------------------ FRONTEND ROUTES ---------------------------------->


@app.get('/', include_in_schema=False, name="home")
@app.get('/posts', include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
    )
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {'posts': posts, "title": "Home"}
    )



@app.get('/posts/{post_id}', include_in_schema=False)
async def post(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]): 

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id== post_id)
    )

    post = result.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title}
        )
        
    raise HTTPException(
        status_code= status.HTTP_404_NOT_FOUND,
        detail="Post not found"
    )



@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts(user_id:int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id ==  user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
    )

    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )



#<------------------------------ EXCEPTION HANDLERS ---------------------------------->


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):

    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)     # in sync we were using JSONResponse. but now we dont need "message" for the api route
    
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,      # if we dont pass this status code we will get 200 response in backend even though error is displayed
    )



# Validation Errors are not HTTPExceptions so we have to handle them in seperate function

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):

    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code= status.HTTP_422_UNPROCESSABLE_CONTENT,
    )


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )


@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    # we are not protecting this route like with api endpoints, because our token is stored in local storage
    # which is only accessible by JS running in the browser. 
    # so when someone navigates to /account, browser makes a regular get request and doesnt automatically include the token from local storage
    # server has no way to know if youre logged in when it renders the page
    # thats why instead its handled by js in the frontend which checks for token
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )