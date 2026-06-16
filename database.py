from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"   # "+aiosqlite" tells which async driver to use

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # sqllite normally only allows 1 thread but fastapi handles multiple. no need to do this with Postgres or Mysql
)

# sessionmaker is a factory that creates db session which is essentially an transaction with the db
# each request gets its own session

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_= AsyncSession,
    expire_on_commit=False,     # prevents issues with Expired_objects after a commit
) 


class Base(DeclarativeBase):
    pass


# fastapi dependency injection calls this function for each request and handles the cleanup automatically
async def get_db():   
    '''its a generator that provides session to our routes which ensures cleanup even if error occurs'''
    async with AsyncSessionLocal() as session:
        yield session 