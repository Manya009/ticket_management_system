from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

#1. Load environment variables from .env file
load_dotenv()
# DB_URL = os.getenv("DATABASE_URL_LOCAL") #for local development, use DATABASE_URL_DOCKER for docker deployment.
DB_URL = os.getenv("DATABASE_URL_DOCKER") #for docker deployment, use DATABASE_URL_LOCAL for local development.

#2. Set up SQLAlchemy engine and session
engine = create_engine(DB_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#3. Base class for our models. All models will inherit from this. 
Base = declarative_base()

#4. Dependency to get DB session for FastAPI routes. This will create a new session for each request and close it after the request is done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#use get_db as a dependency in your routes to access the database session. For example:
# from fastapi import Depends
# from .database import get_db
# @app.get("/items/")
# def read_items(db: Session = Depends(get_db)): #here Session is imported from sqlalchemy.orm
#     items = db.query(Item).all()
#     return items



