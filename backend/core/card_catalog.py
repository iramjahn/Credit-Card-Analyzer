# backend/core/card_catalog.py
#
# The live card catalog = the 10 built-in cards + every approved ingest
# candidate. All read paths (listing, recommendations, annual value) should
# go through here so approved cards join the product immediately.

from typing import List, Optional

from sqlalchemy.orm import Session

from backend.core.card_database import CARD_DATABASE, CreditCard
from backend.database.models import CardCandidate


def _candidate_to_card(candidate: CardCandidate) -> CreditCard:
    payload = candidate.payload
    return CreditCard(
        id=candidate.card_id,
        name=payload["name"],
        issuer=payload["issuer"],
        annual_fee=payload["annual_fee"],
        rewards=payload["rewards"],
        point_value=payload["point_value"],
        benefits=payload.get("benefits", []),
        signup_bonus=payload.get("signup_bonus", {}),
    )


def get_active_cards(db: Optional[Session] = None) -> List[CreditCard]:
    """All cards eligible for recommendations: built-ins + approved candidates."""
    cards = list(CARD_DATABASE)
    if db is not None:
        approved = (
            db.query(CardCandidate)
            .filter(CardCandidate.status == "approved")
            .order_by(CardCandidate.id)
            .all()
        )
        # One card per card_id — the latest approval wins.
        latest = {c.card_id: c for c in approved}
        cards.extend(_candidate_to_card(c) for c in latest.values())
    return cards


def find_card(card_id: str, db: Optional[Session] = None) -> Optional[CreditCard]:
    return next((c for c in get_active_cards(db) if c.id == card_id), None)
