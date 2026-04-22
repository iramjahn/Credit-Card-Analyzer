# backend/api/routes/ml.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Transaction
from backend.ml.recommender import get_recommender

router = APIRouter(prefix="/ml", tags=["ml"])

MIN_TRANSACTIONS = 3

@router.get("/recommend/{user_id}")
def recommend_card(user_id: str, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    if not transactions:
        raise HTTPException(status_code=404, detail=f"No transactions found for user '{user_id}'.")

    if len(transactions) < MIN_TRANSACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough transaction history. Need at least {MIN_TRANSACTIONS} transactions, found {len(transactions)}."
        )

    tx_dicts = [{"category": tx.category, "amount": tx.amount} for tx in transactions]
    recommender = get_recommender()
    return recommender.recommend_for_user(tx_dicts)
