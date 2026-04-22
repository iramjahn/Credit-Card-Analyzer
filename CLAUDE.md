# Credit Card Analyzer

## Project Overview

CardOptimizer — a credit card rewards optimization platform that helps users find the best card for purchases and track annual rewards value.

## Stack

- **Backend**: FastAPI (Python), Pydantic, JWT auth, bcrypt, BeautifulSoup4
- **Frontend**: Single Plaid demo HTML file (no framework)
- **Storage**: In-memory dicts — no persistent DB yet

## Structure

- `backend/core/` — calculation engine, card database, comparator
- `backend/api/` — FastAPI routes and Pydantic models
- `backend/auth/` — JWT + bcrypt auth
- `backend/services/` — custom cards, validators, benefits tracker, web scraper
- `backend/database/`, `backend/ml/`, `backend/integrations/` — empty, not started
- Root-level `.py` files — legacy duplicates of `backend/core/`, do not edit

## Notes

- Plaid integration exists in HTML but has no backend routes yet
- DB persistence and Plaid backend are the main gaps
