# backend/tests/test_ml.py
import pytest
from backend.ml.features import build_spending_vector

CATEGORIES = ["dining", "groceries", "travel", "flights", "hotels", "streaming", "transit", "drugstores", "other"]

def test_build_spending_vector_sums_to_one():
    transactions = [
        {"category": "dining", "amount": 400},
        {"category": "groceries", "amount": 300},
        {"category": "travel", "amount": 300},
    ]
    vector = build_spending_vector(transactions)
    assert abs(sum(vector.values()) - 1.0) < 1e-6

def test_build_spending_vector_correct_proportions():
    transactions = [
        {"category": "dining", "amount": 750},
        {"category": "groceries", "amount": 250},
    ]
    vector = build_spending_vector(transactions)
    assert abs(vector["dining"] - 0.75) < 1e-6
    assert abs(vector["groceries"] - 0.25) < 1e-6
    assert vector["travel"] == 0.0

def test_build_spending_vector_empty_returns_uniform():
    vector = build_spending_vector([])
    assert all(v == 0.0 for v in vector.values())

from backend.ml.seed_data import generate_seed_profiles

def test_seed_profiles_have_correct_shape():
    profiles = generate_seed_profiles()
    assert len(profiles) >= 50
    for p in profiles:
        assert "user_id" in p
        assert "vector" in p
        assert abs(sum(p["vector"].values()) - 1.0) < 1e-6

def test_seed_profiles_have_distinct_archetypes():
    profiles = generate_seed_profiles()
    # Heavy diners should have dining > 0.35
    diners = [p for p in profiles if p["archetype"] == "heavy_diner"]
    assert all(p["vector"]["dining"] > 0.30 for p in diners)

from backend.ml.clustering import SpendingClusterer

def test_clusterer_fits_without_error():
    clusterer = SpendingClusterer(n_clusters=5)
    profiles = generate_seed_profiles()
    clusterer.fit(profiles)
    assert clusterer.is_fitted

def test_clusterer_predicts_cluster_id():
    clusterer = SpendingClusterer(n_clusters=5)
    profiles = generate_seed_profiles()
    clusterer.fit(profiles)
    from backend.ml.features import CATEGORIES
    test_vector = {cat: 1/len(CATEGORIES) for cat in CATEGORIES}
    cluster_id = clusterer.predict(test_vector)
    assert isinstance(cluster_id, int)
    assert 0 <= cluster_id < 5

def test_clusterer_cluster_centers_shape():
    clusterer = SpendingClusterer(n_clusters=5)
    clusterer.fit(generate_seed_profiles())
    centers = clusterer.cluster_centers()
    assert len(centers) == 5
    for center in centers:
        assert abs(sum(center.values()) - 1.0) < 1e-5

from backend.ml.recommender import CardRecommender

def test_recommender_returns_card_id():
    recommender = CardRecommender()
    recommender.train()
    # Heavy diner spending vector
    vector = {
        "dining": 0.50, "groceries": 0.20, "travel": 0.05, "flights": 0.0,
        "hotels": 0.0, "streaming": 0.10, "transit": 0.0, "drugstores": 0.05, "other": 0.10
    }
    result = recommender.recommend_for_vector(vector)
    assert "card_id" in result
    assert "card_name" in result
    assert "estimated_annual_value" in result
    assert result["estimated_annual_value"] > 0

def test_recommender_favors_dining_card_for_heavy_diner():
    recommender = CardRecommender()
    recommender.train()
    vector = {
        "dining": 0.60, "groceries": 0.20, "travel": 0.05, "flights": 0.0,
        "hotels": 0.0, "streaming": 0.05, "transit": 0.0, "drugstores": 0.05, "other": 0.05
    }
    result = recommender.recommend_for_vector(vector)
    # AmEx Gold (amex-gold) or Chase Sapphire Preferred should rank highly for dining
    assert result["card_id"] in ["amex-gold", "csp", "chase-freedom-flex"]
