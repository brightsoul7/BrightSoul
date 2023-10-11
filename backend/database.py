from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

USER_NAME=os.getenv("USER_NAME")
PASSWORD=os.getenv("PASSWORD")
POSTGRES_SERVER=os.getenv("POSTGRES_SERVER")
DB_NAME=os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql://{USER_NAME}:{PASSWORD}@{POSTGRES_SERVER}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
