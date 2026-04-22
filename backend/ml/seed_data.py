# backend/ml/seed_data.py

import random
from backend.ml.features import CATEGORIES, build_spending_vector

# 5 spending archetypes — each is a base distribution over categories
ARCHETYPES = {
    "heavy_diner":        {"dining": 0.45, "groceries": 0.20, "streaming": 0.10, "travel": 0.05, "other": 0.20},
    "frequent_traveler":  {"travel": 0.30, "flights": 0.25, "hotels": 0.20, "dining": 0.15, "other": 0.10},
    "grocery_shopper":    {"groceries": 0.55, "dining": 0.15, "streaming": 0.10, "transit": 0.10, "other": 0.10},
    "streaming_homebody": {"streaming": 0.35, "groceries": 0.30, "dining": 0.20, "other": 0.15},
    "commuter":           {"transit": 0.35, "dining": 0.25, "drugstores": 0.15, "groceries": 0.15, "other": 0.10},
}

def _jitter(base: dict, noise: float = 0.08) -> dict:
    """Add small random noise to a spending distribution and renormalize."""
    raw = {}
    for cat in CATEGORIES:
        base_val = base.get(cat, 0.0)
        raw[cat] = max(0.0, base_val + random.uniform(-noise, noise))
    total = sum(raw.values()) or 1.0
    return {cat: v / total for cat, v in raw.items()}

def generate_seed_profiles(n_per_archetype: int = 20, seed: int = 42) -> list:
    """
    Generate synthetic user spending profiles.
    Returns a list of dicts: {user_id, archetype, vector}
    """
    random.seed(seed)
    profiles = []
    for archetype, base in ARCHETYPES.items():
        for i in range(n_per_archetype):
            user_id = f"seed_{archetype}_{i}"
            vector = _jitter(base)
            profiles.append({"user_id": user_id, "archetype": archetype, "vector": vector})
    return profiles
