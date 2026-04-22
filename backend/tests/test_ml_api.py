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
    _add_transactions("ml_user_sparse_UNIQUE123", [
        {"amount": 10, "category": "dining", "merchant": "Coffee Shop"},
    ])
    response = client.get("/ml/recommend/ml_user_sparse_UNIQUE123")
    assert response.status_code == 400
