# backend/services/custom_card_service.py
#
# Manages user-created custom cards. Backed by the `custom_cards` table so
# cards survive restarts and are isolated per user.

from typing import Dict, List, Tuple, Optional

from sqlalchemy.orm import Session

from backend.database.models import CustomCard
from backend.services.validators import CardValidator


class CustomCardService:
    """CRUD for custom user-created credit cards, persisted to the database."""

    def __init__(self):
        self.validator = CardValidator()

    # ── Create ────────────────────────────────────────────────────────────────

    def create_custom_card(
        self,
        db: Session,
        user_id: int,
        name: str,
        issuer: str,
        annual_fee: int,
        point_value: float,
        rewards: Dict[str, float],
        benefits: List[str],
    ) -> Tuple[bool, Optional[CustomCard], List[str]]:
        """Validate and persist a new custom card. Returns (success, card, errors)."""
        is_valid, errors = self.validator.validate_all(
            name, issuer, annual_fee, point_value, rewards, benefits
        )
        if not is_valid:
            return False, None, errors

        card_id = self._generate_card_id(user_id, name)
        if db.get(CustomCard, card_id) is not None:
            return False, None, [f"A card with this name already exists (ID: {card_id})"]

        card = CustomCard(
            id=card_id,
            user_id=str(user_id),
            name=name,
            issuer=issuer,
            annual_fee=annual_fee,
            point_value=point_value,
            rewards=rewards,
            benefits=benefits,
            signup_bonus={},  # custom cards don't carry a signup bonus
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        return True, card, []

    def create_card_from_url(
        self,
        db: Session,
        user_id: int,
        url: str,
    ) -> Tuple[bool, Optional[CustomCard], List[str]]:
        """Scrape a card from a URL, then persist it."""
        try:
            from backend.services.web_scraper import CreditCardWebScraper
        except ImportError:
            from services.web_scraper import CreditCardWebScraper

        scraper = CreditCardWebScraper()
        success, card_data, error = scraper.scrape_card_from_url(url)
        if not success:
            return False, None, [error]

        return self.create_custom_card(
            db,
            user_id=user_id,
            name=card_data["name"],
            issuer=card_data["issuer"],
            annual_fee=card_data["annual_fee"],
            point_value=card_data["point_value"],
            rewards=card_data["rewards"],
            benefits=card_data["benefits"],
        )

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_custom_card(self, db: Session, card_id: str) -> Optional[CustomCard]:
        return db.get(CustomCard, card_id)

    def get_all_custom_cards(self, db: Session, user_id: int) -> List[CustomCard]:
        return (
            db.query(CustomCard)
            .filter(CustomCard.user_id == str(user_id))
            .order_by(CustomCard.created_at)
            .all()
        )

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_custom_card(self, db: Session, card_id: str) -> bool:
        card = db.get(CustomCard, card_id)
        if card is None:
            return False
        db.delete(card)
        db.commit()
        return True

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _generate_card_id(self, user_id: int, name: str) -> str:
        """Build a unique, URL-friendly card id: custom-user-{user_id}-{name-slug}."""
        slug = name.lower().replace(" ", "-").replace("_", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        slug = "-".join(filter(None, slug.split("-")))
        slug = slug[:50]
        return f"custom-user-{user_id}-{slug}"
