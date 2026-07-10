# backend/integrations/card_ingest/pipeline.py
#
# Orchestrates one ingest run:
#   fetch page -> extract card data -> validate -> diff vs live version
#   -> stage as a pending CardCandidate for human review.
#
# Nothing is ever auto-published: a human approves candidates via the
# /ingest API before they join the recommendation catalog.

import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from backend.database.models import CardCandidate
from backend.integrations.card_ingest.fetcher import fetch_page
from backend.integrations.card_ingest.extractors import get_extractor
from backend.services.validators import CardValidator

logger = logging.getLogger(__name__)

_validator = CardValidator()


def _slugify(issuer: str, name: str) -> str:
    base = f"{issuer}-{name}".lower()
    slug = "".join(c if c.isalnum() or c in " -" else "" for c in base)
    slug = "-".join(filter(None, slug.replace(" ", "-").split("-")))
    return f"ingest-{slug[:60]}"


def _diff_payloads(old: dict, new: dict) -> dict:
    """Field-level diff between the currently approved payload and a new one."""
    changes: dict = {}
    for field in ("name", "issuer", "annual_fee", "point_value", "rewards", "benefits", "signup_bonus"):
        if old.get(field) != new.get(field):
            changes[field] = {"from": old.get(field), "to": new.get(field)}
    return changes


def ingest_card_from_url(
    db: Session,
    url: str,
    html_override: Optional[str] = None,
) -> Tuple[bool, Optional[CardCandidate], str]:
    """
    Run the ingest pipeline for one URL and stage the result.

    `html_override` lets tests (and cached pages) bypass the network.
    Returns (success, candidate, error_message).
    """
    # 1. Fetch
    if html_override is not None:
        html = html_override
    else:
        ok, html, error = fetch_page(url)
        if not ok:
            return False, None, error

    # 2. Extract
    extractor = get_extractor()
    ok, payload, error = extractor.extract(html, url)
    if not ok:
        return False, None, f"Extraction failed: {error}"

    # 3. Validate (same rules as user-created custom cards)
    is_valid, errors = _validator.validate_all(
        payload["name"],
        payload["issuer"],
        payload["annual_fee"],
        payload["point_value"],
        payload["rewards"],
        payload["benefits"],
    )
    if not is_valid:
        return False, None, f"Extracted data failed validation: {'; '.join(errors)}"

    card_id = _slugify(payload["issuer"], payload["name"])

    # 4. Diff vs the currently approved version of this card (if any)
    current = (
        db.query(CardCandidate)
        .filter(CardCandidate.card_id == card_id, CardCandidate.status == "approved")
        .order_by(CardCandidate.id.desc())
        .first()
    )
    diff = _diff_payloads(current.payload, payload) if current else None
    if current and not diff:
        return False, None, "No changes vs the currently approved version of this card"

    # 5. Stage for review
    candidate = CardCandidate(
        card_id=card_id,
        source_url=url,
        extractor=extractor.name,
        status="pending",
        payload=payload,
        diff=diff,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    logger.info("Staged candidate %s (%s) from %s", candidate.id, card_id, url)
    return True, candidate, ""
