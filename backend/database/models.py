# backend/database/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    # Stored as a string so it works with both numeric user ids and the
    # synthetic ids ("user_1") used by the ML flow and tests.
    user_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    merchant = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CardCandidate(Base):
    """A card extracted by the ingest pipeline, awaiting human review.

    Approved candidates become part of the live card catalog
    (see backend/core/card_catalog.py). Re-scraping the same card creates a
    fresh pending candidate whose `diff` shows what changed.
    """

    __tablename__ = "card_candidates"

    id = Column(Integer, primary_key=True, index=True)
    # Stable slug derived from issuer+name (e.g. "ingest-chase-sapphire-preferred")
    card_id = Column(String, index=True, nullable=False)
    source_url = Column(String, nullable=False)
    extractor = Column(String, nullable=False)  # "rule-based" | "claude"
    # pending | approved | rejected | superseded
    status = Column(String, index=True, nullable=False, default="pending")
    payload = Column(JSON, nullable=False)  # full extracted card data
    diff = Column(JSON, nullable=True)      # changes vs the currently approved version
    review_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)


class CustomCard(Base):
    __tablename__ = "custom_cards"

    # Slug id (e.g. "custom-user-1-my-travel-card"); unique across users.
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    issuer = Column(String, nullable=False)
    annual_fee = Column(Integer, nullable=False, default=0)
    point_value = Column(Float, nullable=False, default=0.01)
    rewards = Column(JSON, nullable=False, default=dict)
    benefits = Column(JSON, nullable=False, default=list)
    signup_bonus = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
