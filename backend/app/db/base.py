import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
url = settings.DATABASE_URL
if url.startswith("sqlite:///"):
    path = url.replace("sqlite:///", "", 1)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    pass
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
