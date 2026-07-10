# backend/ml/evaluate.py
#
# Offline evaluation of the recommendation strategies on held-out synthetic
# users (a different random seed than training):
#
#   cluster  — LEGACY path (pre-July 2026): assign the user to a KMeans
#              cluster, then recommend the best card for the CLUSTER CENTER.
#              This evaluation is what justified replacing it.
#   direct   — score cards against the user's OWN spending vector (optimal
#              under our value model, by construction — the oracle). This is
#              now the production path in CardRecommender.
#   one-size — non-personalized baseline: the single card that's best on
#              average across all users, recommended to everyone.
#
# Metrics: how often each strategy picks the oracle card, and the annual
# dollar value lost when it doesn't (regret).
#
# Run:  python -m backend.ml.evaluate

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from collections import Counter, defaultdict

from backend.core.card_database import CARD_DATABASE
from backend.core.annual_calculator import calculate_annual_value
from backend.ml.recommender import CardRecommender, MONTHLY_SPEND
from backend.ml.seed_data import generate_seed_profiles

HELDOUT_SEED = 1337   # training uses 42; evaluation must not
N_PER_ARCHETYPE = 60  # 300 held-out users


def annual_net_value(card, vector: dict) -> float:
    monthly = {cat: MONTHLY_SPEND * frac for cat, frac in vector.items()}
    return calculate_annual_value(card, monthly).net_value


def best_card_direct(vector: dict):
    return max(CARD_DATABASE, key=lambda c: annual_net_value(c, vector))


def evaluate():
    users = generate_seed_profiles(n_per_archetype=N_PER_ARCHETYPE, seed=HELDOUT_SEED)

    recommender = CardRecommender()
    recommender.train()

    # Non-personalized baseline: the card with the best mean value across users
    mean_value = {
        card.id: sum(annual_net_value(card, u["vector"]) for u in users) / len(users)
        for card in CARD_DATABASE
    }
    one_size_card = max(CARD_DATABASE, key=lambda c: mean_value[c.id])

    stats = {
        "cluster": {"match": 0, "regret": []},
        "one-size": {"match": 0, "regret": []},
    }
    per_archetype = defaultdict(lambda: {"match": 0, "n": 0})
    cluster_picks = Counter()
    oracle_picks = Counter()

    for user in users:
        vector = user["vector"]
        oracle = best_card_direct(vector)
        oracle_value = annual_net_value(oracle, vector)
        oracle_picks[oracle.id] += 1

        # Legacy strategy, reconstructed explicitly (production is now direct)
        center = recommender.clusterer.cluster_centers()[recommender.clusterer.predict(vector)]
        cluster_pick = max(CARD_DATABASE, key=lambda c: annual_net_value(c, center))
        cluster_pick_id = cluster_pick.id
        cluster_picks[cluster_pick_id] += 1

        # Sanity check: the production path must agree with the oracle
        production_pick = recommender.recommend_for_vector(vector)["card_id"]
        assert production_pick == oracle.id, (
            f"production path diverged from direct scoring: {production_pick} != {oracle.id}"
        )
        cluster_regret = oracle_value - annual_net_value(cluster_pick, vector)
        stats["cluster"]["regret"].append(cluster_regret)
        if cluster_pick_id == oracle.id:
            stats["cluster"]["match"] += 1
            per_archetype[user["archetype"]]["match"] += 1
        per_archetype[user["archetype"]]["n"] += 1

        one_size_regret = oracle_value - annual_net_value(one_size_card, vector)
        stats["one-size"]["regret"].append(one_size_regret)
        if one_size_card.id == oracle.id:
            stats["one-size"]["match"] += 1

    n = len(users)
    print(f"Held-out users: {n} (seed {HELDOUT_SEED}, {N_PER_ARCHETYPE}/archetype)")
    print(f"Value model: cap-aware annual net value at ${MONTHLY_SPEND:,.0f}/month total spend")
    print(f"One-size-fits-all baseline card: {one_size_card.name}\n")

    header = f"{'strategy':<12} {'oracle match':>12} {'mean regret':>12} {'max regret':>11}"
    print(header)
    print("-" * len(header))
    for name in ("cluster", "one-size"):
        s = stats[name]
        mean_r = sum(s["regret"]) / n
        max_r = max(s["regret"])
        print(f"{name:<12} {s['match']/n:>11.1%} {mean_r:>11.2f}$ {max_r:>10.2f}$")
    print(f"{'direct':<12} {'100.0%':>12} {'0.00$':>12} {'0.00$':>11}   (oracle by construction)")

    print("\nCluster-strategy oracle match by archetype:")
    for archetype, s in sorted(per_archetype.items()):
        print(f"  {archetype:<20} {s['match']}/{s['n']} ({s['match']/s['n']:.0%})")

    print("\nCard chosen (cluster vs oracle):")
    for card_id in sorted(set(cluster_picks) | set(oracle_picks)):
        print(f"  {card_id:<26} cluster={cluster_picks.get(card_id, 0):>3}  oracle={oracle_picks.get(card_id, 0):>3}")

    return stats


if __name__ == "__main__":
    evaluate()
