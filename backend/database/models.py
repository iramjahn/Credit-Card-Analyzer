# backend/database/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from backend.database.connection import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)   # dining, groceries, travel, etc.
    merchant = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
