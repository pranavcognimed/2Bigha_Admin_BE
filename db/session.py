# app/db/session.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from core.config import settings

# Create engine using URL from settings
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

# Dependency for getting DB session
def get_db_session():
    try:
        db = SessionLocal()
        yield db
        print("connected @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    except OperationalError as e:
        print("❌ Error connecting to the database:", e)
        raise e
    finally:
        db.close()
