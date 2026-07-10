# backend/api/routes/cards.py

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.auth.dependencies import get_current_user
from backend.database.connection import get_db
from backend.database.models import User
from backend.api.models import (
    CardRecommendationRequest,
    CardRecommendationResponse,
    CustomCardCreate,
    CustomCardFromURL,
    CardResponse,
    AnnualValueRequest,
    AnnualValueResponse,
    CardBenefitInfo,
)
from backend.core.card_catalog import get_active_cards, find_card
from backend.core.comparator import find_best_card
from backend.core.annual_calculator import calculate_annual_value
from backend.services.custom_card_service import CustomCardService
from backend.services.benefits_tracker import BenefitsTracker

router = APIRouter(prefix="/cards", tags=["Cards"])

# Initialize services
custom_card_service = CustomCardService()

# ============================================
# Get All Cards
# ============================================

@router.get("/", response_model=List[CardResponse])
def get_all_cards(db: Session = Depends(get_db)):
    """Get all available credit cards (built-in + approved ingested cards)"""
    cards = []
    for card in get_active_cards(db):
        cards.append(CardResponse(
            id=card.id,
            name=card.name,
            issuer=card.issuer,
            annual_fee=card.annual_fee,
            point_value=card.point_value,
            rewards=card.rewards,
            benefits=card.benefits
        ))
    return cards

# ============================================
# Get Card by ID
# ============================================

@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: str, db: Session = Depends(get_db)):
    """Get a specific card by ID"""
    card = find_card(card_id, db)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    return CardResponse(
        id=card.id,
        name=card.name,
        issuer=card.issuer,
        annual_fee=card.annual_fee,
        point_value=card.point_value,
        rewards=card.rewards,
        benefits=card.benefits
    )

# ============================================
# Get Card Recommendation
# ============================================

@router.post("/recommend", response_model=List[CardRecommendationResponse])
def recommend_card(request: CardRecommendationRequest, db: Session = Depends(get_db)):
    """Get card recommendation for a purchase"""

    # Find best cards across the whole active catalog
    results = find_best_card(get_active_cards(db), request.amount, request.category)
    
    # Convert to response format
    recommendations = []
    for result in results[:5]:  # Top 5 cards
        recommendations.append(CardRecommendationResponse(
            card_id=result.card.id,
            card_name=result.card.name,
            reward_rate=result.calculation.reward_rate,
            points_earned=result.calculation.points,
            cash_value=result.calculation.cash_value,
            note=result.calculation.note
        ))
    
    return recommendations

# ============================================
# Create Custom Card
# ============================================

@router.post("/custom", response_model=CardResponse)
def create_custom_card(
    request: CustomCardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom credit card"""

    success, card, errors = custom_card_service.create_custom_card(
        db,
        user_id=current_user.id,
        name=request.name,
        issuer=request.issuer,
        annual_fee=request.annual_fee,
        point_value=request.point_value,
        rewards=request.rewards,
        benefits=request.benefits
    )

    if not success:
        raise HTTPException(status_code=400, detail=errors)
    
    return CardResponse(
        id=card.id,
        name=card.name,
        issuer=card.issuer,
        annual_fee=card.annual_fee,
        point_value=card.point_value,
        rewards=card.rewards,
        benefits=card.benefits
    )

# ============================================
# Create Custom Card from URL
# ============================================

@router.post("/custom/from-url", response_model=CardResponse)
def create_card_from_url(
    request: CustomCardFromURL,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a custom card by scraping a URL"""

    success, card, errors = custom_card_service.create_card_from_url(
        db,
        user_id=current_user.id,
        url=request.url
    )

    if not success:
        raise HTTPException(status_code=400, detail=errors)
    
    return CardResponse(
        id=card.id,
        name=card.name,
        issuer=card.issuer,
        annual_fee=card.annual_fee,
        point_value=card.point_value,
        rewards=card.rewards,
        benefits=card.benefits
    )

# ============================================
# Get Custom Cards
# ============================================

@router.get("/custom/user/{user_id}", response_model=List[CardResponse])
def get_user_custom_cards(user_id: int, db: Session = Depends(get_db)):
    """Get all custom cards for a user"""

    cards = custom_card_service.get_all_custom_cards(db, user_id)

    return [
        CardResponse(
            id=card.id,
            name=card.name,
            issuer=card.issuer,
            annual_fee=card.annual_fee,
            point_value=card.point_value,
            rewards=card.rewards,
            benefits=card.benefits
        )
        for card in cards
    ]

# ============================================
# Annual Value
# ============================================

@router.post("/{card_id}/annual-value", response_model=AnnualValueResponse)
def get_annual_value(card_id: str, request: AnnualValueRequest, db: Session = Depends(get_db)):
    """Estimate a card's net annual rewards value for a monthly spending profile."""
    card = find_card(card_id, db)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    result = calculate_annual_value(card, request.monthly_spending)
    return AnnualValueResponse(
        card_id=card.id,
        card_name=card.name,
        total_value=round(result.total_value, 2),
        annual_fee=card.annual_fee,
        net_value=round(result.net_value, 2),
        roi=round(result.roi, 2) if result.roi is not None else None,
    )

# ============================================
# Card Benefits (parsed value + reset cadence)
# ============================================

@router.get("/{card_id}/benefits", response_model=List[CardBenefitInfo])
def get_card_benefits(card_id: str, db: Session = Depends(get_db)):
    """List a card's benefits with parsed dollar values and reset periods."""
    card = find_card(card_id, db)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    tracker = BenefitsTracker()
    tracker.add_card_benefits(card)
    return [
        CardBenefitInfo(
            card_id=b.card_id,
            card_name=b.card_name,
            benefit_name=b.benefit_name,
            estimated_value=b.total_value,
            reset_period=b.reset_period,
            days_until_reset=b.days_until_reset,
        )
        for b in tracker.get_benefits_by_card(card.id)
    ]