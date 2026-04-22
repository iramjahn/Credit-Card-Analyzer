# backend/tests/test_transactions.py
import pytest
from sqlalchemy import inspect
from backend.database.connection import engine, init_db

def test_init_db_creates_tables():
    init_db()
    inspector = inspect(engine)
    assert "transactions" in inspector.get_table_names()

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
