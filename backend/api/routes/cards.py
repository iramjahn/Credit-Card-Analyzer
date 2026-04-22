# backend/api/routes/cards.py

import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.auth.dependencies import get_current_user
from backend.database.models import User
from backend.api.models import (
    CardRecommendationRequest,
    CardRecommendationResponse,
    CustomCardCreate,
    CustomCardFromURL,
    CardResponse
)
from backend.core.card_database import CARD_DATABASE
from backend.core.comparator import find_best_card
from backend.services.custom_card_service import CustomCardService

router = APIRouter(prefix="/cards", tags=["Cards"])

# Initialize services
custom_card_service = CustomCardService()

# ============================================
# Get All Cards
# ============================================

@router.get("/", response_model=List[CardResponse])
def get_all_cards():
    """Get all available credit cards"""
    cards = []
    for card in CARD_DATABASE:
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
def get_card(card_id: str):
    """Get a specific card by ID"""
    for card in CARD_DATABASE:
        if card.id == card_id:
            return CardResponse(
                id=card.id,
                name=card.name,
                issuer=card.issuer,
                annual_fee=card.annual_fee,
                point_value=card.point_value,
                rewards=card.rewards,
                benefits=card.benefits
            )
    
    raise HTTPException(status_code=404, detail="Card not found")

# ============================================
# Get Card Recommendation
# ============================================

@router.post("/recommend", response_model=List[CardRecommendationResponse])
def recommend_card(request: CardRecommendationRequest):
    """Get card recommendation for a purchase"""
    
    # Find best cards
    results = find_best_card(CARD_DATABASE, request.amount, request.category)
    
    # Convert to response format
    recommendations = []
    for result in results[:5]:  # Top 5 cards
        recommendations.append(CardRecommendationResponse(
            card_id=result.card.id,
            card_name=result.card.name,
            reward_rate=result.calculation.reward_rate,
            points_earned=result.calculation.points,
            cash_value=result.calculation.cash_value
        ))
    
    return recommendations

# ============================================
# Create Custom Card
# ============================================

@router.post("/custom", response_model=CardResponse)
def create_custom_card(request: CustomCardCreate, current_user: User = Depends(get_current_user)):
    """Create a custom credit card"""
    
    success, card, errors = custom_card_service.create_custom_card(
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
def create_card_from_url(request: CustomCardFromURL, current_user: User = Depends(get_current_user)):
    """Create a custom card by scraping a URL"""
    
    success, card, errors = custom_card_service.create_card_from_url(
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
def get_user_custom_cards(user_id: int):
    """Get all custom cards for a user"""
    
    cards = custom_card_service.get_all_custom_cards(user_id)
    
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