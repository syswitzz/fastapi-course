#-----------------------------------------------------------------------------------------
# PUT - replace entire resource. if some fields are missing they will be replaced with default values or null
# PATCH - update specific fields of a resource. only the fields provided in the request will be updated.
# DELETE - we ideally return HTTP 204 - NO CONTENT response. So there will be no response model but a status code

# 200 OK - Successful GET, PUT, PATCH
# 201 CREATED - Successful POST
# 204 NO CONTENT - Successful DELETE
# 400 BAD REQUEST - Duplicate username/email
# 401 UNAUTHORIZED - Not authorized (logged in)
# 403 FORBIDDEN - When a user is not allowed to delete/edit another user
# 404 NOT FOUND - Resource doesnt exist
# 422 UNPROCESSABLE ENTITY - Validation error (automatic from Pydantic)
#-----------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------
# ASYNC:- allows program to handle multiple tasks concurrently
# we are using async to avoid waiting for something exteral like
# 1. Database req., 2. Network response (ext. API calls), 3. File to read - I/O Bound Tasks
# because we can do other work during that time. 
# ASYNC does not help with Computing bound operations like image processing, heavy calculations.
# So async isnt always faster. Its benefits show up when you have concurrent load
# Dont use sync database sessions in async routes
# Dont use something like request library in async routes. as Requests is sync library.

# FASTAPI ASYNC:- fastapi automatically runs the normal "def" functions in seperate threadpool.
# this prevents the function from blocking the main even loop.
# fastapi runs "async def" directly in main event loop which is more efficient
# but it means you must "await" for any I/O operations. eg, on database operations
# because blocking main even loop is much worse than using regular "def"
# aiosqlite = provides async driver for sqlalchemy

# Lazy-Loading :-  It is the probably the biggest diff. between sync and async sqlalchemy
# lazyloading lets us access relationships (eg, post.author) by automatically running a query to load that author.
# in Async Sqlalchemy :_ we get an error when we try to access (post.author) without loading it
# happens because lazyloading would require running a sync query in an async context which is not allowed
# solution - eagerloading with selectandload(). any query where we access relationship, we need to add eagerloading 
#-----------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------
# Pydantic:- is a data validation library that uses python typehint. used for validation, serialization and documentation
# pydantic enforces typehint at runtime and give detailed when something doesnt add up
# pydantic decide what we accept and return from api endpoints
# our frontent template routes work exactly like before, theyre using dicts, they dont know about pydantic
# the schemas only apply to api endpoint where we set response model

# Sqlite:- is built into python and doesnt require any seperate server installation
# sqlalchemy is the most popular ORM for python.
# benefit of ORM - is we can switch databases with just configuration changes
# we create pydantic schemas and database models seperately but sqlmodels library can fix that
# though we are not using that here to better understand how they work seperately and most industry standard apps dont use them anyway
#-----------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------
# AUTHENTICATION - Who are you
# AUTHORIZATION - What are you allowed to do

# "pwdlib[argon2]":- for password hashing, argon2 is most secure algorithm

# pyjwt (json web tokens):- for authentication and authorization we will use JWTs. 
# they are like encrypted cookies that store user info and permissions. 
# they are stateless and can be used across different servers without needing a shared session store. 
# they are also more secure than traditional cookies because they are signed and can have an expiration time.

# pydantic-settings (over python-dotenv):- it centralizes all our configuration module in one settings module
# clear errors and validate automatically with pydantic, 
# uses secret strings from pydantic so less risk of data leak
#-----------------------------------------------------------------------------------------
