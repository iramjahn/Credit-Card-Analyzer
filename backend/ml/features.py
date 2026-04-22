# backend/ml/features.py

from typing import List, Dict

CATEGORIES = [
    "dining", "groceries", "travel", "flights", "hotels",
    "streaming", "transit", "drugstores", "other"
]

def build_spending_vector(transactions: List[Dict]) -> Dict[str, float]:
    """
    Convert a list of transactions into a normalized spending vector.
    Each key is a category; each value is its fraction of total spend.
    Returns all-zeros if no transactions.
    """
    totals = {cat: 0.0 for cat in CATEGORIES}
    for tx in transactions:
        cat = tx["category"] if tx["category"] in totals else "other"
        totals[cat] += tx["amount"]

    total_spend = sum(totals.values())
    if total_spend == 0:
        return totals

    return {cat: amount / total_spend for cat, amount in totals.items()}
