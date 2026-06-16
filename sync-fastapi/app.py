from fastapi import FastAPI, Request
# from fastapi.responses import HTMLResponse - we do not need htmlresponse because were using jinja2tem..

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate

from fastapi import Depends     # this is how we inject database sessions in our routes
from typing import Annotated
from sqlalchemy import select   # Sqlalchemy v2 style for data querying
from sqlalchemy.orm import Session  # for Typehints
import models
from database import Base, engine, get_db   # Base, engine - creating tables. get_db - provides DB sessions

Base.metadata.create_all(bind=engine)   # Looks all of models that inherit from Base and Creates table if they dont exist


#1 uv run python3 -m fastapi dev main.py
app = FastAPI()


#2 templates allow for serving html pages to user while still maintaining json endpoints for the backend api
# templates let us write proper html files and just pass in our dynamic data because containing all html in a python string would be horrible
templates = Jinja2Templates(directory="templates")
staticfiles = StaticFiles(directory="static")

app.mount("/static", staticfiles, name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


# @app.get('/html', response_class=HTMLResponse)
# def html_page():
#     return "<h1>Hello World in HTML</h1>"


#2 urlfor - proper way to generate url in templates. it is useful when we change the mountpath /static to something else then all the links will update automatically
# i. route links (navigation)
# ii. static files (css, js, img) 

# @app.get('/', include_in_schema=False, name='home') #url_for points to this and not /posts because we named it home
# @app.get('/posts', include_in_schema=False, name='posts')
# def home(request: Request):     # we need to take in request when using jinja2template
#     return templates.TemplateResponse(
#         request, 
#         "home.html", 
#         {"posts": posts, "title": "Home"}
#     )  # passing posts as context to use in the html


# @app.get('/posts/{post_id}', include_in_schema=False)
# def post(request: Request, post_id: int):
#     for post in posts:
#         if post.get('id') == post_id:
#             return templates.TemplateResponse(
#                 request, 
#                 "post.html", 
#                 {"post": post, "title": post['title'][0:50]}
#             )  # passing posts as context dictionary to use in the html
#     # 3. raising an HTTPException feels like crashing the program but instead Fastapi handles it as a response
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)



# @app.get('/api/posts', response_model=list[PostResponse])     # response_model- extra data is filtered out and less data throws error
# def get_posts():
#     return posts


#3. we can use path parameters to grab specific posts from our list of posts and display them on a separate page.
# A path parameter in FastAPI is a dynamic part of the URL path used to identify a specific resource

# type validation - (handled by fastapi). handles /api/posts/hello scenarios

# @app.get('/api/posts/{post_id}', response_model=PostResponse)
# def get_post(post_id: int):     # type validation 
#     for post in posts:
#         if post.get('id') == post_id:
#             return post
#     # return {"error": "Post not found!"}  is not convenient because it tell the client request OK i.e., 200. which does not help the client (handle) the error
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")


# 3. we need to handle errors differently depending on whether the request is to frontend or API
# fastapi is built on top of starlette and when a user goes to a route that doesnt exist it is handled by starlette. 

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
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


# 3. validation errors are not HTTPExceptions so we have to handle them in seperate function

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):

    if request.url.path.startswith("/api"):
        # we cannot craft a simple custom message or detail like in HTTPException because Validation error have a list of detailed error information
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,  # request validation dont have 'exception.status_code'  
            content={"detail": exception.errors()},
        )
    
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


#-----------------------------------------------------------------------------------------

#4. pydantic is a data validation library that uses python typehint. used for validation, serialization and documentation
# pydantic enforces typehint at runtime and give detailed when something doesnt add up
# pydantic decide what we accept and return from api endpoints

# @app.post(
#     '/api/posts',
#     response_model = PostResponse,
#     status_code= status.HTTP_201_CREATED,
# )
# def create_post(post: PostCreate):      # post: PostCreate if ro request body validation
#     new_id = max(i['id'] for i in posts)+1 if posts else 1
#     new_post = {
#         'id': new_id,
#         'author': post.author,
#         'content': post.content,
#         'title': post.title,
#         'date_posted': 'March 19, 2026'
#     }
#     posts.append(new_post)
#     return new_post

# 4. our template route work exactly like before, theyre using dicts, they dont know about pydantic
# the schemas only apply to api endpoint where we set response model


#-----------------------------------------------------------------------------------------

#5. sqlite is built into python and doesnt require any seperate server installation
# sqlalchemy is the most popular ORM for python.
# benefit of ORM - is we can switch databases with just configuration changes

#5. we create pydantic schemas and database models seperately but sqlmodels library can fix that
# though we are not using that here to better understand how they work seperately and most industry standard apps dont use them anyway


@app.get('/', include_in_schema=False, name="home")
@app.get('/posts', include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.Post)
    )

    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "home.html",
        {'posts': posts, "title": "Home"}
    )



@app.get('/posts/{post_id}', include_in_schema=False)
def post(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]): 
    result = db.execute(
        select(models.Post).where(models.Post.id== post_id)
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
def user_posts(user_id:int, request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id ==  user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )

    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


@app.get('/api/posts', response_model=list[PostResponse])    
def get_posts(db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post))
    posts = result.scalars().all()

    return posts



@app.get('/api/posts/{post_id}', response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if post:
        return post
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")



@app.post('/api/posts', response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = user.id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post



@app.post(
    '/api/users',
    response_model = UserResponse,
    status_code= status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):  
    '''
    we use Annotated to combine typehinting and dependency injection.
    db: Annotated[Session, Depends(get_db)] calls get_db() gives a session to this route and cleans up.
    user: UserCreate is for request body validation
    '''    
    
    # check if username already exists - DB already has a unique constraint so its not like we can add a duplicate user anyway
    result = db.execute(
        select(models.User).where(models.User.username ==  user.username)
    )

    existing_user = result.scalars().first()  # gives first user object or None if no such user exist

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # check if email already exists
    result = db.execute(
        select(models.User).where(models.User.email ==  user.email)
    )

    existing_email = result.scalars().first() 

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    
    new_user = models.User(
        username = user.username,
        email = user.email,
    )

    db.add(new_user)    # stages the insert
    db.commit()     # executes and saves to the db
    db.refresh(new_user)    # reloads the object from db

    return new_user



@app.get('/api/users/{user_id}', response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
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



@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id:int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "User not found",
        )
    
    result = db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )
    posts = result.scalars().all()
    return posts


#-----------------------------------------------------------------------------------------


# PUT - replace entire resource. if some fields are missing they will be replaced with default values or null
# PATCH - update specific fields of a resource. only the fields provided in the request will be updated.

@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(post_id: int, post_data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if post.user_id != post_data.user_id:
        result = db.execute(select(models.User).where(models.User.id == post_data.user_id))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    db.commit()
    db.refresh(post)

    return post


@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(post_id: int, post_data: PostUpdate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    
    # To not override the DB with None values in Partial update we use post_data.model_dump(exclude_unset=True)
    update_data = post_data.model_dump(exclude_unset=True)
    for item, value in update_data.items():
        setattr(post, item, value)  # setting the value of item in post dict

    db.commit()
    db.refresh(post)
    return post


# DELETE - we ideally return HTTP 204 - NO CONTENT response. So there will be no response model but a status code

@app.delete('/api/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(
        select(models.Post).where(models.Post.id == post_id)
    )
    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found.")
    
    db.delete(post)
    db.commit()


# 200 OK - Successful GET, PUT, PATCH
# 201 CREATED - Successful POST
# 204 NO CONTENT - Successful DELETE
# 400 BAD REQUEST - Duplicate username/email
# 404 NOT FOUND - Resource doesnt exist
# 422 UNPROCESSABLE ENTITY - Validation error (automatic from Pydantic)



@app.patch('/api/users/{user_id}', response_model=UserResponse)
def update_user(
    user_id: int, 
    user_data: UserUpdate, 
    db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.username is not None and user_data.username != user.username:
        result = db.execute(select(models.User).where(models.User.username== user_data.username))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        
        user.username = user_data.username
        
    if user_data.email is not None and user_data.email != user.email:
        result = db.execute(select(models.User).where(models.User.email== user_data.email))
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")
        
        user.email = user_data.email

    if user_data.image_file is not None:
        user.image_file = user_data.image_file

    db.commit()
    db.refresh(user)
    return user


# If a user is deleted what happens to their posts? 
# 1. Prevent deletion if user has posts 
# 2. Delete user and cascade delete their posts. (Most real world apps use this)

@app.delete('/api/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    '''This function also cascade deletes the User's posts'''

    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()


#-----------------------------------------------------------------------------------------


# ASYNC - allows program to handle multiple tasks concurrently
# we are using async to avoid waiting for something exteral like
# 1. Database req., 2. Network response (ext. API calls), 3. File to read - I/O Bound Tasks
# because we can do other work during that time. 
# ASYNC does not help with Computing bound operations like image processing, heavy calculations.
# So async isnt always faster. Its benefits show up when you have concurrent load

# FASTAPI ASYNC - fastapi automatically runs the normal "def" functions in seperate threadpool.
# this prevents the function from blocking the main even loop.
# fastapi runs "async def" directly in main event loop which is more efficient
# but it means you must "await" for any I/O operations. eg, on database operations
# because blocking main even loop is much worse than using regular "def"
# aiosqlite = provides async driver for sqlalchemy