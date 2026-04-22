# backend/ml/recommender.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ml.features import CATEGORIES, build_spending_vector
from backend.ml.clustering import SpendingClusterer
from backend.ml.seed_data import generate_seed_profiles
from backend.core.card_database import CARD_DATABASE
from backend.core.calculator import calculate_rewards

# Assume each user spends $3,000/month total — used to estimate annual value
MONTHLY_SPEND = 3000.0

class CardRecommender:
    """
    Trains a SpendingClusterer on seed data, then recommends the best card
    for a given spending vector by scoring all cards against the cluster center.
    """

    def __init__(self, n_clusters: int = 5):
        self.clusterer = SpendingClusterer(n_clusters=n_clusters)

    def train(self) -> None:
        profiles = generate_seed_profiles()
        self.clusterer.fit(profiles)

    def _score_card(self, card, spending_vector: dict) -> float:
        """Estimate annual net value of a card given a spending distribution."""
        annual_value = 0.0
        for category, fraction in spending_vector.items():
            monthly_category_spend = MONTHLY_SPEND * fraction
            calc = calculate_rewards(card, monthly_category_spend, category)
            annual_value += calc.cash_value * 12
        annual_value -= card.annual_fee
        return annual_value

    def recommend_for_vector(self, vector: dict) -> dict:
        """Return the best card for a given spending vector."""
        if not self.clusterer.is_fitted:
            raise RuntimeError("Call train() before recommend_for_vector().")

        cluster_id = self.clusterer.predict(vector)
        cluster_center = self.clusterer.cluster_centers()[cluster_id]

        best_card = None
        best_value = float("-inf")
        for card in CARD_DATABASE:
            value = self._score_card(card, cluster_center)
            if value > best_value:
                best_value = value
                best_card = card

        return {
            "card_id": best_card.id,
            "card_name": best_card.name,
            "issuer": best_card.issuer,
            "annual_fee": best_card.annual_fee,
            "estimated_annual_value": round(best_value, 2),
            "cluster_id": cluster_id,
        }

    def recommend_for_user(self, user_transactions: list) -> dict:
        """Build a spending vector from raw transactions and recommend."""
        vector = build_spending_vector(user_transactions)
        return self.recommend_for_vector(vector)


# Module-level singleton — trained once at import time
_recommender: CardRecommender | None = None

def get_recommender() -> CardRecommender:
    global _recommender
    if _recommender is None:
        _recommender = CardRecommender()
        _recommender.train()
    return _recommender
