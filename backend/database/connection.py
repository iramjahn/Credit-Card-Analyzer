# backend/database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Override with CARDOPTIMIZER_DB (used by the test suite for an isolated DB).
DB_PATH = os.getenv(
    "CARDOPTIMIZER_DB",
    os.path.join(os.path.dirname(__file__), "cardoptimizer.db"),
)
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from backend.database import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
