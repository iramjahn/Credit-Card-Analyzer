# backend/ml/recommender.py

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.ml.features import CATEGORIES, build_spending_vector
from backend.ml.clustering import SpendingClusterer
from backend.ml.seed_data import generate_seed_profiles
from backend.core.card_database import CARD_DATABASE
from backend.core.annual_calculator import calculate_annual_value

# Assume each user spends $3,000/month total — used to estimate annual value
MONTHLY_SPEND = 3000.0

# Below this many transactions, blend the user's vector toward their cluster
# center (cold-start smoothing); above it, trust their own history fully.
COLD_START_TRANSACTIONS = 5

class CardRecommender:
    """
    Recommends the best card by scoring all cards directly against the user's
    own spending vector.

    Offline evaluation (backend/ml/evaluate.py, 300 held-out users) showed the
    previous cluster-center scoring matched the optimal card only 77.7% of the
    time (~$13/user/yr regret), while direct scoring is optimal by
    construction. KMeans clustering is retained for what it's actually good
    for: segment labeling ("frequent_traveler") and cold-start smoothing when
    transaction history is thin.
    """

    def __init__(self, n_clusters: int = 5):
        self.clusterer = SpendingClusterer(n_clusters=n_clusters)
        self._segment_labels: dict[int, str] = {}

    def train(self) -> None:
        profiles = generate_seed_profiles()
        self.clusterer.fit(profiles)
        self._segment_labels = self._label_clusters()

    def _label_clusters(self) -> dict[int, str]:
        """Name each cluster after the archetype its center is closest to."""
        from backend.ml.seed_data import ARCHETYPES

        labels = {}
        for i, center in enumerate(self.clusterer.cluster_centers()):
            best_name = min(
                ARCHETYPES.items(),
                key=lambda kv: sum(
                    (center.get(c, 0.0) - kv[1].get(c, 0.0)) ** 2 for c in CATEGORIES
                ),
            )[0]
            labels[i] = best_name
        return labels

    def _score_card(self, card, spending_vector: dict) -> float:
        """Estimate annual net value of a card given a spending distribution.

        Delegates to the cap-aware annual calculator so ML recommendations use
        the same value model as the rest of the product (spend caps,
        top-category semantics, annual fee).
        """
        monthly_spending = {
            category: MONTHLY_SPEND * fraction
            for category, fraction in spending_vector.items()
        }
        return calculate_annual_value(card, monthly_spending).net_value

    def recommend_for_vector(self, vector: dict) -> dict:
        """Return the best card for a given spending vector (direct scoring)."""
        if not self.clusterer.is_fitted:
            raise RuntimeError("Call train() before recommend_for_vector().")

        cluster_id = self.clusterer.predict(vector)

        best_card = None
        best_value = float("-inf")
        for card in CARD_DATABASE:
            value = self._score_card(card, vector)
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
            "segment": self._segment_labels.get(cluster_id),
        }

    def recommend_for_user(self, user_transactions: list) -> dict:
        """Build a spending vector from raw transactions and recommend.

        With thin history (< COLD_START_TRANSACTIONS), the vector is blended
        toward the user's cluster center so one lucky dinner out doesn't look
        like a heavy-diner profile.
        """
        vector = build_spending_vector(user_transactions)

        n = len(user_transactions)
        if 0 < n < COLD_START_TRANSACTIONS:
            center = self.clusterer.cluster_centers()[self.clusterer.predict(vector)]
            weight = n / COLD_START_TRANSACTIONS
            vector = {
                cat: weight * vector.get(cat, 0.0) + (1 - weight) * center.get(cat, 0.0)
                for cat in CATEGORIES
            }

        return self.recommend_for_vector(vector)


# Module-level singleton — trained once at import time
_recommender: CardRecommender | None = None

def get_recommender() -> CardRecommender:
    global _recommender
    if _recommender is None:
        _recommender = CardRecommender()
        _recommender.train()
    return _recommender
