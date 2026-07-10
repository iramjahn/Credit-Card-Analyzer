# CardOptimizer — Backend

FastAPI service for the CardOptimizer credit-card rewards platform: card
recommendations, transaction tracking, ML-based card suggestions, auth, and a
(mocked) Plaid integration.

## Stack

- **FastAPI** + Pydantic
- **SQLAlchemy 2** over **SQLite** (`backend/database/cardoptimizer.db`, created on startup)
- **JWT** auth (PyJWT) with **bcrypt** password hashing
- **scikit-learn** KMeans for the spending-based recommender
- **BeautifulSoup4** for the card web scraper

## Setup

```bash
cd "Credit Card Analyzer"
python -m venv .venv
.venv\Scripts\activate           # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env   # then edit values
```

## Run

```bash
# from the repository root
python -m backend.api.main
# or:
uvicorn backend.api.main:app --reload
```

API docs: http://localhost:8000/docs

## Frontend demo

Open `frontend/plaid-demo.html` in a browser with the API running on port 8000.
Sign in (any email + 8+ char password creates an account), then "Connect Bank
Account" to walk the mocked Plaid flow.

## Tests

```bash
pytest backend/tests
```

## API overview

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` |
| Cards | `GET /cards/`, `GET /cards/{id}`, `POST /cards/recommend`, `POST /cards/{id}/annual-value`, `GET /cards/{id}/benefits` |
| Custom cards | `POST /cards/custom`, `POST /cards/custom/from-url`, `GET /cards/custom/user/{user_id}` |
| Transactions | `POST /transactions/`, `GET /transactions/{user_id}` |
| ML | `GET /ml/recommend/{user_id}` |
| Plaid (mock) | `POST /plaid/create-link-token`, `POST /plaid/exchange-token`, `GET /plaid/transactions`, `GET /plaid/spending` |
| Card ingest | `POST /ingest/candidates`, `GET /ingest/candidates`, `POST /ingest/candidates/{id}/approve`, `POST /ingest/candidates/{id}/reject` |

## Card ingestion agent

`backend/integrations/card_ingest/` automates adding cards to the catalog:

1. `POST /ingest/candidates {"url": ...}` fetches the card's page (robots.txt-aware,
   rate-limited) and extracts structured card data.
2. The extraction is validated and staged as a **pending candidate** — nothing
   is ever auto-published.
3. A reviewer inspects it (`GET /ingest/candidates?status_filter=pending`),
   then approves or rejects. Approved cards immediately join `/cards/` and the
   recommendation engine. Re-ingesting the same card produces a `diff` against
   the approved version (e.g. an annual-fee change) for review.

Extraction engines (pluggable, chosen automatically):

- **rule-based** (default) — BeautifulSoup + patterns. Free, no API, works offline.
- **claude** — LLM extraction via the Claude API; far more robust to page layout.
  Activates only when `ANTHROPIC_API_KEY` is set and `pip install anthropic` is
  done. With no key configured the pipeline runs at $0.

Note: issuer sites are often JS-rendered and prohibit scraping in their ToS —
the agent targets a curated URL list and keeps a human in the loop. A production
version would license card data or partner with issuers.

## Notes / known gaps

- **Plaid is mocked** — routes return canned data. To go live, set the `PLAID_*`
  env vars, add the `plaid` SDK, and replace the `_mock_*` helpers in
  `api/routes/plaid.py`.
- Spending categories are defined once in `core/categories.py`; transactions,
  the ML feature vector, and the card validator all import from there.
- Benefit *usage* tracking (`services/benefits_tracker.py`) is not yet persisted;
  only the parse/list view (`GET /cards/{id}/benefits`) is exposed.
