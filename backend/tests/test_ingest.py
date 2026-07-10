# backend/tests/test_ingest.py
#
# End-to-end tests for the card ingestion agent — fully offline (the fixture
# HTML page stands in for a fetched card page).

import os

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.database.connection import SessionLocal
from backend.integrations.card_ingest.pipeline import ingest_card_from_url
from backend.integrations.card_ingest.extractors import RuleBasedExtractor

client = TestClient(app)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_card.html")
SOURCE_URL = "https://www.chase.com/personal/credit-cards/sapphire-preferred"


@pytest.fixture()
def sample_html():
    with open(FIXTURE, encoding="utf-8") as f:
        return f.read()


@pytest.fixture()
def auth_headers():
    """Sign up (or log in) a reviewer and return Bearer headers."""
    creds = {"email": "reviewer@test.com", "password": "reviewpass123"}
    response = client.post("/auth/signup", json=creds)
    if response.status_code != 201:  # already exists from a previous test
        response = client.post("/auth/login", json=creds)
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ── Extractor ────────────────────────────────────────────────────────────────

def test_rule_based_extractor_parses_fixture(sample_html):
    ok, payload, error = RuleBasedExtractor().extract(sample_html, SOURCE_URL)
    assert ok, error
    assert payload["name"] == "Sapphire Preferred"
    assert payload["issuer"] == "Chase"
    assert payload["annual_fee"] == 95
    assert payload["rewards"]["dining"] == 3.0
    assert payload["rewards"]["streaming"] == 3.0
    assert payload["rewards"]["default"] == 1.0
    # gas is recognized but not a canonical category — flagged, not published
    assert payload["unmapped_rewards"].get("gas") == 2.0
    assert payload["signup_bonus"] == {"amount": 75000, "spend_requirement": 5000}
    assert any("foreign transaction" in b.lower() for b in payload["benefits"])


# ── Pipeline ─────────────────────────────────────────────────────────────────

def test_pipeline_stages_pending_candidate(sample_html):
    db = SessionLocal()
    try:
        ok, candidate, error = ingest_card_from_url(db, SOURCE_URL, html_override=sample_html)
        assert ok, error
        assert candidate.status == "pending"
        assert candidate.card_id.startswith("ingest-chase-sapphire-preferred")
        assert candidate.extractor == "rule-based"
        assert candidate.diff is None  # first version of this card
    finally:
        db.close()


# ── Review API + catalog integration ────────────────────────────────────────

def test_ingest_requires_auth():
    response = client.post("/ingest/candidates", json={"url": SOURCE_URL})
    assert response.status_code in (401, 403)


def test_approve_flow_publishes_card(sample_html, auth_headers):
    # Stage directly through the pipeline (offline)
    db = SessionLocal()
    try:
        ok, candidate, error = ingest_card_from_url(
            db, SOURCE_URL + "?v=approve-flow", html_override=sample_html
        )
        assert ok, error
        candidate_id = candidate.id
        card_id = candidate.card_id
    finally:
        db.close()

    # Not in the catalog while pending
    assert client.get(f"/cards/{card_id}").status_code == 404

    # Approve via the API
    response = client.post(
        f"/ingest/candidates/{candidate_id}/approve",
        json={"note": "verified against fixture"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    # Now live in the catalog
    response = client.get(f"/cards/{card_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Sapphire Preferred"

    # And eligible for recommendations (3x streaming ranks in the top 5)
    response = client.post("/cards/recommend", json={"amount": 100, "category": "streaming"})
    assert response.status_code == 200
    assert any(r["card_id"] == card_id for r in response.json())


def test_reject_flow_keeps_card_out(sample_html, auth_headers):
    db = SessionLocal()
    try:
        ok, candidate, error = ingest_card_from_url(
            db,
            "https://www.discover.com/credit-cards/cash-back/it-card",
            html_override=sample_html.replace("Sapphire Preferred", "Discover it Test"),
        )
        assert ok, error
        candidate_id = candidate.id
        card_id = candidate.card_id
    finally:
        db.close()

    response = client.post(
        f"/ingest/candidates/{candidate_id}/reject",
        json={"note": "extraction quality too low"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert client.get(f"/cards/{card_id}").status_code == 404
