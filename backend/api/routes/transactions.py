# backend/api/routes/transactions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from backend.database.connection import get_db
from backend.database.models import Transaction
from backend.core.categories import SPENDING_CATEGORY_SET as VALID_CATEGORIES

router = APIRouter(prefix="/transactions", tags=["transactions"])

class TransactionIn(BaseModel):
    user_id: str
    amount: float
    category: str
    merchant: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    user_id: str
    amount: float
    category: str
    merchant: Optional[str]

    class Config:
        from_attributes = True

@router.post("/", response_model=TransactionOut)
def add_transaction(tx: TransactionIn, db: Session = Depends(get_db)):
    if tx.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid category '{tx.category}'. Valid: {sorted(VALID_CATEGORIES)}")
    record = Transaction(user_id=tx.user_id, amount=tx.amount, category=tx.category, merchant=tx.merchant)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/{user_id}", response_model=List[TransactionOut])
def get_transactions(user_id: str, db: Session = Depends(get_db)):
    return db.query(Transaction).filter(Transaction.user_id == user_id).all()
