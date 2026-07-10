# backend/ml/features.py

from typing import List, Dict

from backend.core.categories import SPENDING_CATEGORIES, DEFAULT_SPENDING_CATEGORY

# Feature-vector dimensions, in canonical order (see backend/core/categories.py).
CATEGORIES = SPENDING_CATEGORIES

def build_spending_vector(transactions: List[Dict]) -> Dict[str, float]:
    """
    Convert a list of transactions into a normalized spending vector.
    Each key is a category; each value is its fraction of total spend.
    Returns all-zeros if no transactions.
    """
    totals = {cat: 0.0 for cat in CATEGORIES}
    for tx in transactions:
        cat = tx["category"] if tx["category"] in totals else DEFAULT_SPENDING_CATEGORY
        totals[cat] += tx["amount"]

    total_spend = sum(totals.values())
    if total_spend == 0:
        return totals

    return {cat: amount / total_spend for cat, amount in totals.items()}
