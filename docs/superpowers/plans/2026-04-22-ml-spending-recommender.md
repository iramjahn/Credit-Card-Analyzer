# ML Spending Recommender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a machine learning layer that clusters users by spending habits and recommends the best credit card based on similar users' profiles.

**Architecture:** SQLite stores user transactions; a feature engineering step converts transactions into category-percentage vectors; K-Means clustering groups users by spending pattern; the card recommender reuses the existing `calculate_rewards` engine to score cards against each cluster's average spending mix.

**Tech Stack:** SQLAlchemy (SQLite), pandas, scikit-learn (KMeans), FastAPI, pytest

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `backend/requirements.txt` | Add missing deps |
| Modify | `backend/api/main.py` | Fix bugs, register new routers, init DB |
| Create | `backend/database/connection.py` | SQLAlchemy engine + session factory |
| Create | `backend/database/models.py` | Transaction ORM model |
| Create | `backend/api/routes/transactions.py` | CRUD endpoints for transactions |
| Create | `backend/ml/features.py` | Build spending vector from DB transactions |
| Create | `backend/ml/seed_data.py` | Synthetic user profiles to bootstrap clustering |
| Create | `backend/ml/clustering.py` | K-Means fit/predict on spending vectors |
| Create | `backend/ml/recommender.py` | Recommend best card for a user |
| Create | `backend/api/routes/ml.py` | GET /ml/recommend/{user_id} endpoint |
| Create | `backend/tests/test_transactions.py` | Transaction API tests |
| Create | `backend/tests/test_ml.py` | ML pipeline tests |

---

## Task 1: Fix main.py bugs and update requirements.txt

**Files:**
- Modify: `backend/api/main.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Update requirements.txt with all needed packages**

Replace the contents of `backend/requirements.txt` with:

```
bcrypt>=4.0.0
PyJWT>=2.0.0
requests>=2.28.0
beautifulsoup4>=4.11.0
fastapi>=0.110.0
uvicorn>=0.29.0
sqlalchemy>=2.0.0
pandas>=2.0.0
scikit-learn>=1.4.0
numpy>=1.26.0
pytest>=8.0.0
httpx>=0.27.0
```

- [ ] **Step 2: Install new dependencies**

```bash
pip install -r backend/requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 3: Fix main.py — remove typo and broken plaid import**

Replace `backend/api/main.py` with:

```python
# backend/api/main.py

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.cards import router as cards_router
from backend.database.connection import init_db

app = FastAPI(
    title="CardOptimizer API",
    description="Credit card rewards optimization platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(cards_router)

@app.get("/")
def read_root():
    return {"message": "CardOptimizer API", "version": "1.0.0", "status": "running", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 4: Verify the app starts without errors**

```bash
cd C:/Users/iramj/OneDrive/Credit_Card_Analyzer
python -m uvicorn backend.api.main:app --port 8000
```

Expected: `Application startup complete.` with no import errors. Stop with Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/api/main.py
git commit -m "fix: correct main.py typo and broken plaid import, add ML dependencies"
```

---

## Task 2: Database connection

**Files:**
- Create: `backend/database/connection.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_transactions.py`:

```python
# backend/tests/test_transactions.py
import pytest
from sqlalchemy import inspect
from backend.database.connection import engine, init_db

def test_init_db_creates_tables():
    init_db()
    inspector = inspect(engine)
    assert "transactions" in inspector.get_table_names()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:/Users/iramj/OneDrive/Credit_Card_Analyzer
python -m pytest backend/tests/test_transactions.py::test_init_db_creates_tables -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.database.connection'`

- [ ] **Step 3: Create backend/database/connection.py**

```python
# backend/database/connection.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cardoptimizer.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    from backend.database import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Run test — still fails (models not defined yet, expected)**

```bash
python -m pytest backend/tests/test_transactions.py::test_init_db_creates_tables -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'backend.database.models'` — that's fine, next task fixes it.

---

## Task 3: Transaction database model

**Files:**
- Create: `backend/database/models.py`

- [ ] **Step 1: Create backend/database/models.py**

```python
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
```

- [ ] **Step 2: Create backend/database/__init__.py**

```python
# backend/database/__init__.py
```

(Empty file — makes it a proper package.)

- [ ] **Step 3: Run the DB test — should pass now**

```bash
python -m pytest backend/tests/test_transactions.py::test_init_db_creates_tables -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/database/connection.py backend/database/models.py backend/database/__init__.py backend/tests/test_transactions.py
git commit -m "feat: add SQLite database layer with Transaction model"
```

---

## Task 4: Transaction API routes

**Files:**
- Create: `backend/api/routes/transactions.py`
- Modify: `backend/api/main.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_transactions.py`:

```python
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_add_transaction():
    response = client.post("/transactions/", json={
        "user_id": "user_1",
        "amount": 45.00,
        "category": "dining",
        "merchant": "Chipotle"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_1"
    assert data["category"] == "dining"
    assert "id" in data

def test_get_user_transactions():
    client.post("/transactions/", json={"user_id": "user_2", "amount": 120.0, "category": "groceries", "merchant": "Whole Foods"})
    response = client.get("/transactions/user_2")
    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) >= 1
    assert transactions[0]["user_id"] == "user_2"

def test_invalid_category_rejected():
    response = client.post("/transactions/", json={
        "user_id": "user_1",
        "amount": 50.0,
        "category": "not_a_real_category",
        "merchant": "Nowhere"
    })
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_transactions.py -v
```

Expected: FAIL with 404 (routes don't exist yet)

- [ ] **Step 3: Create backend/api/routes/transactions.py**

```python
# backend/api/routes/transactions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from backend.database.connection import get_db
from backend.database.models import Transaction

VALID_CATEGORIES = {
    "dining", "groceries", "travel", "flights", "hotels",
    "streaming", "transit", "drugstores", "other"
}

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
```

- [ ] **Step 4: Register the router in main.py**

In `backend/api/main.py`, add after the cards_router import:

```python
from backend.api.routes.transactions import router as transactions_router
```

And after `app.include_router(cards_router)`:

```python
app.include_router(transactions_router)
```

- [ ] **Step 5: Run all transaction tests**

```bash
python -m pytest backend/tests/test_transactions.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/routes/transactions.py backend/api/main.py backend/tests/test_transactions.py
git commit -m "feat: add transaction CRUD endpoints with category validation"
```

---

## Task 5: Feature engineering

**Files:**
- Create: `backend/ml/features.py`
- Create: `backend/ml/__init__.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/test_ml.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest backend/tests/test_ml.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create backend/ml/__init__.py**

```python
# backend/ml/__init__.py
```

- [ ] **Step 4: Create backend/ml/features.py**

```python
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
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest backend/tests/test_ml.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/ml/__init__.py backend/ml/features.py backend/tests/test_ml.py
git commit -m "feat: add spending vector feature engineering for ML pipeline"
```

---

## Task 6: Synthetic seed data

**Files:**
- Create: `backend/ml/seed_data.py`

- [ ] **Step 1: Write failing test**

Add to `backend/tests/test_ml.py`:

```python
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
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest backend/tests/test_ml.py::test_seed_profiles_have_correct_shape backend/tests/test_ml.py::test_seed_profiles_have_distinct_archetypes -v
```

Expected: FAIL

- [ ] **Step 3: Create backend/ml/seed_data.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest backend/tests/test_ml.py::test_seed_profiles_have_correct_shape backend/tests/test_ml.py::test_seed_profiles_have_distinct_archetypes -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/ml/seed_data.py backend/tests/test_ml.py
git commit -m "feat: add synthetic spending profiles for K-Means bootstrapping"
```

---

## Task 7: K-Means clustering

**Files:**
- Create: `backend/ml/clustering.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_ml.py`:

```python
from backend.ml.clustering import SpendingClusterer
from backend.ml.seed_data import generate_seed_profiles

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
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest backend/tests/test_ml.py::test_clusterer_fits_without_error backend/tests/test_ml.py::test_clusterer_predicts_cluster_id backend/tests/test_ml.py::test_clusterer_cluster_centers_shape -v
```

Expected: FAIL

- [ ] **Step 3: Create backend/ml/clustering.py**

```python
# backend/ml/clustering.py

import numpy as np
from sklearn.cluster import KMeans
from backend.ml.features import CATEGORIES

class SpendingClusterer:
    """
    Fits K-Means on user spending vectors and predicts which cluster
    a new user belongs to.
    """

    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self._kmeans: KMeans | None = None

    @property
    def is_fitted(self) -> bool:
        return self._kmeans is not None

    def _to_matrix(self, profiles: list) -> np.ndarray:
        return np.array([[p["vector"][cat] for cat in CATEGORIES] for p in profiles])

    def fit(self, profiles: list) -> None:
        """Train on a list of {user_id, vector} dicts."""
        X = self._to_matrix(profiles)
        self._kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init="auto")
        self._kmeans.fit(X)

    def predict(self, vector: dict) -> int:
        """Return the cluster ID for a single spending vector."""
        if not self.is_fitted:
            raise RuntimeError("Clusterer must be fitted before predicting.")
        row = np.array([[vector.get(cat, 0.0) for cat in CATEGORIES]])
        return int(self._kmeans.predict(row)[0])

    def cluster_centers(self) -> list[dict]:
        """Return each cluster center as a normalized spending vector dict."""
        if not self.is_fitted:
            raise RuntimeError("Clusterer must be fitted before accessing centers.")
        centers = []
        for row in self._kmeans.cluster_centers_:
            row = np.clip(row, 0, None)
            total = row.sum() or 1.0
            centers.append({cat: float(row[i] / total) for i, cat in enumerate(CATEGORIES)})
        return centers
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest backend/tests/test_ml.py::test_clusterer_fits_without_error backend/tests/test_ml.py::test_clusterer_predicts_cluster_id backend/tests/test_ml.py::test_clusterer_cluster_centers_shape -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add backend/ml/clustering.py backend/tests/test_ml.py
git commit -m "feat: add K-Means spending clusterer"
```

---

## Task 8: Card recommender

**Files:**
- Create: `backend/ml/recommender.py`

- [ ] **Step 1: Write failing tests**

Add to `backend/tests/test_ml.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest backend/tests/test_ml.py::test_recommender_returns_card_id backend/tests/test_ml.py::test_recommender_favors_dining_card_for_heavy_diner -v
```

Expected: FAIL

- [ ] **Step 3: Create backend/ml/recommender.py**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest backend/tests/test_ml.py::test_recommender_returns_card_id backend/tests/test_ml.py::test_recommender_favors_dining_card_for_heavy_diner -v
```

Expected: PASS

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest backend/tests/ -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/ml/recommender.py backend/tests/test_ml.py
git commit -m "feat: add card recommender using K-Means cluster centers and existing reward engine"
```

---

## Task 9: ML API endpoint

**Files:**
- Create: `backend/api/routes/ml.py`
- Modify: `backend/api/main.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_ml_api.py`:

```python
# backend/tests/test_ml_api.py
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def _add_transactions(user_id, txns):
    for tx in txns:
        client.post("/transactions/", json={"user_id": user_id, **tx})

def test_recommend_endpoint_returns_card():
    _add_transactions("ml_user_1", [
        {"amount": 400, "category": "dining", "merchant": "Chipotle"},
        {"amount": 200, "category": "groceries", "merchant": "Trader Joes"},
        {"amount": 100, "category": "streaming", "merchant": "Netflix"},
    ])
    response = client.get("/ml/recommend/ml_user_1")
    assert response.status_code == 200
    data = response.json()
    assert "card_id" in data
    assert "card_name" in data
    assert "estimated_annual_value" in data

def test_recommend_endpoint_unknown_user_returns_404():
    response = client.get("/ml/recommend/nonexistent_user_xyz")
    assert response.status_code == 404

def test_recommend_endpoint_insufficient_data_returns_400():
    # User with only 1 transaction — not enough signal
    _add_transactions("ml_user_sparse", [
        {"amount": 10, "category": "dining", "merchant": "Coffee Shop"},
    ])
    response = client.get("/ml/recommend/ml_user_sparse")
    assert response.status_code == 400
```

- [ ] **Step 2: Run to verify they fail**

```bash
python -m pytest backend/tests/test_ml_api.py -v
```

Expected: FAIL with 404 (route not registered)

- [ ] **Step 3: Create backend/api/routes/ml.py**

```python
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
```

- [ ] **Step 4: Register ml router in main.py**

In `backend/api/main.py`, add after the transactions import:

```python
from backend.api.routes.ml import router as ml_router
```

And add after `app.include_router(transactions_router)`:

```python
app.include_router(ml_router)
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest backend/tests/ -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/routes/ml.py backend/api/main.py backend/tests/test_ml_api.py
git commit -m "feat: add ML card recommendation endpoint GET /ml/recommend/{user_id}"
```

---

## Task 10: Smoke test the running API

- [ ] **Step 1: Start the server**

```bash
cd C:/Users/iramj/OneDrive/Credit_Card_Analyzer
python -m uvicorn backend.api.main:app --port 8000 --reload
```

- [ ] **Step 2: Add some transactions (new terminal)**

```bash
curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo", "amount": 500, "category": "dining", "merchant": "Nobu"}'

curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo", "amount": 300, "category": "dining", "merchant": "Sushi Place"}'

curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo", "amount": 200, "category": "groceries", "merchant": "Whole Foods"}'
```

- [ ] **Step 3: Get recommendation**

```bash
curl http://localhost:8000/ml/recommend/demo
```

Expected output (card will vary):
```json
{
  "card_id": "amex-gold",
  "card_name": "American Express Gold",
  "issuer": "American Express",
  "annual_fee": 250,
  "estimated_annual_value": 312.50,
  "cluster_id": 2
}
```

- [ ] **Step 4: Check interactive docs**

Open browser: `http://localhost:8000/docs`

Expected: All three route groups visible — `cards`, `transactions`, `ml`.

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete ML spending recommender — transactions, clustering, card recommendation"
```

---

## Self-Review

**Spec coverage:**
- [x] Track user spending habits → Transaction model + CRUD API
- [x] Compare with other users → K-Means clusters trained on synthetic profiles
- [x] Recommend cards based on similar users → cluster center used for card scoring
- [x] Reuse existing reward engine → `calculate_rewards` called in recommender

**Placeholder scan:** None found. All steps contain actual code.

**Type consistency:**
- `build_spending_vector` returns `Dict[str, float]` — used consistently in clustering.py and recommender.py
- `generate_seed_profiles` returns `list[dict]` with keys `user_id`, `archetype`, `vector` — matches what `SpendingClusterer.fit()` expects
- `Transaction` ORM model fields (`user_id`, `amount`, `category`, `merchant`) match `TransactionIn` Pydantic model
