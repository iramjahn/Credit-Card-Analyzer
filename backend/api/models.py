# backend/api/models.py

from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional

# ============================================
# User Models
# ============================================

class UserSignup(BaseModel):
    """Request model for user signup"""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Response model for user data"""
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]

class TokenResponse(BaseModel):
    """Response model for authentication token"""
    token: str
    user: UserResponse

# ============================================
# Card Models
# ============================================

class CardRecommendationRequest(BaseModel):
    """Request for card recommendation"""
    amount: float
    category: str

class CardRecommendationResponse(BaseModel):
    """Response with card recommendation"""
    card_id: str
    card_name: str
    reward_rate: float
    points_earned: int
    cash_value: float
    note: Optional[str] = None  # caveat, e.g. top-category cards

class CustomCardCreate(BaseModel):
    """Request to create custom card"""
    name: str
    issuer: str
    annual_fee: int
    point_value: float
    rewards: Dict[str, float]
    benefits: List[str]

class CustomCardFromURL(BaseModel):
    """Request to create card from URL"""
    url: str

class CardResponse(BaseModel):
    """Response with card data"""
    id: str
    name: str
    issuer: str
    annual_fee: int
    point_value: float
    rewards: Dict[str, float]
    benefits: List[str]

# ============================================
# Annual Value Models
# ============================================

class AnnualValueRequest(BaseModel):
    """Monthly spend per category, e.g. {"dining": 400, "travel": 200}."""
    monthly_spending: Dict[str, float]

class AnnualValueResponse(BaseModel):
    """Annualized rewards value for a card given a spending profile."""
    card_id: str
    card_name: str
    total_value: float          # gross rewards value over a year
    annual_fee: int
    net_value: float            # total_value minus the annual fee
    roi: Optional[float]        # net value as a % of the fee (None if no fee)

# ============================================
# Benefit Models
# ============================================

class CardBenefitInfo(BaseModel):
    """A single card benefit with its parsed monetary value and reset cadence."""
    card_id: str
    card_name: str
    benefit_name: str
    estimated_value: float
    reset_period: str           # 'annual' | 'monthly' | 'one-time' | 'none'
    days_until_reset: Optional[int]