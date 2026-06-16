from pydantic import BaseModel, ConfigDict, Field
from pydantic import EmailStr
from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

    # author: str = Field(min_length=1, max_length=50) : Author field now comes from relationship

    # even though there is '= Field ()' but we havent given any default value so all of these parameters are required


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)

    # user_id is not included because typically we dont want to change the owner of the post. use PUT or dedicated endpoints


class PostResponse(PostBase):
    # in pydantic v2, we configure models with ConfigDict instead of Config
    # from_attributes=True tells it can read data from objects with attributes rather than just dict()
    model_config = ConfigDict(from_attributes=True)     # it allows 'post.title' and not just post['title']

    # usually we should avoid 'id' as it is a python built in keyword but for database models and api responses it is a standard

    id: int     # since this  is scope to the class so it wont conflict with global python function
    date_posted: datetime
    user_id: int
    author: UserPublic    # Gives author's info in nested JSON
    


class UserBase(BaseModel): 
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)     # we dont use min_lenght because EmailStr already verifies that its a valid email


class UserCreate(UserBase): # User create karne me kya kya chaiye
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    image_file: str | None = Field(default=None, min_length=1, max_length=200)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserPublic(BaseModel):   # API response me kya kya ayega
    model_config = ConfigDict(from_attributes=True)     # so that pydantic can read from SQLalchemy model

    id: int
    username: str
    image_file: str | None
    image_path: str     # this is already a property in user model so we dont need to define it here as well

class UserPrivate(UserPublic):
    email: EmailStr