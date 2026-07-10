# Credit Card Analyzer

## Project Overview

CardOptimizer — a credit card rewards optimization platform that helps users
find the best card for a purchase, estimate a card's annual value, track
spending, and get ML-based card recommendations.

## Stack

- **Backend**: FastAPI (Python), Pydantic, JWT auth (PyJWT), bcrypt, scikit-learn, BeautifulSoup4
- **Frontend**: Single Plaid demo HTML file (no framework)
- **Storage**: SQLAlchemy 2 over SQLite (`backend/database/cardoptimizer.db`), created on startup

## Structure

- `backend/api/` — FastAPI app (`main.py`) + routes (`auth`, `cards`, `transactions`, `ml`, `plaid`) + Pydantic models
- `backend/core/` — calculation engine, card database (10 built-in cards), comparator, annual calculator, and `categories.py` (the single source of truth for spending categories)
- `backend/auth/` — JWT + bcrypt auth, wired into routes
- `backend/services/` — custom card service (DB-backed), validators, benefits tracker, web scraper
- `backend/ml/` — KMeans spending recommender (features, clustering, seed data, recommender)
- `backend/database/` — SQLAlchemy connection + ORM models (`User`, `Transaction`, `CustomCard`, `CardCandidate`)
- `backend/integrations/card_ingest/` — card ingestion agent: fetcher (robots-aware), pluggable extractors (free rule-based default; optional Claude LLM extractor via `ANTHROPIC_API_KEY`), staging pipeline with human review via `/ingest` routes
- `backend/core/card_catalog.py` — live catalog = built-in cards + approved ingest candidates; all card read paths go through it
- `backend/tests/` — pytest suites (transactions, ML, ML API, ingest); `conftest.py` isolates tests onto a temp DB via the `CARDOPTIMIZER_DB` env var
- `backend/utils/` — empty placeholder

## Conventions

- Spending categories live ONLY in `backend/core/categories.py`. Transactions,
  the ML feature vector, and the card validator import from it — don't redefine
  category lists elsewhere.
- Run from the repo root: `python -m backend.api.main` or `uvicorn backend.api.main:app`.

## Notes / known gaps

- **Plaid is mocked** — `api/routes/plaid.py` returns canned data; the `plaid`
  SDK is not a dependency. Real integration is the main remaining gap.
- Benefit *usage* tracking (`services/benefits_tracker.py`) is not persisted;
  only the read-only parse view (`GET /cards/{id}/benefits`) is exposed.
- `JWT_SECRET` defaults to a dev value and CORS is open (`*`) — tighten before production.
