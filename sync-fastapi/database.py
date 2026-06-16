from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # sqllite normally only allows 1 thread but fastapi handles multiple. no need to do this with Postgres or Mysql
)

# sessionmaker is a factory that creates db session which is essentially an transaction with the db
# each request gets its own session

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)     # we set false because we wanna control when changes are commited


class Base(DeclarativeBase):
    pass


# fastapi dependency injection calls this function for each request and handles the cleanup automatically
def get_db():   
    '''its a generator that provides session to our routes which ensures cleanup even if error occurs'''
    with SessionLocal() as db:
        yield db 