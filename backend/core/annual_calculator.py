# annual_calculator.py

from typing import Optional
from backend.core.card_database import CreditCard

class AnnualValue():
    """Calculates reward value from card over the year."""
    def __init__(self, card: CreditCard, total_value: float, net_value: float, roi: Optional[float]):
        self.card = card
        self.total_value = total_value
        self.net_value = net_value
        self.roi = roi

    def __repr__(self) -> str:
        return f"AnnualValue({self.card.name}: total=${self.total_value:.2f}, net=${self.net_value:.2f})"

def calculate_annual_value(card: CreditCard, monthly_spending: dict[str, float]) -> AnnualValue:
    total_value = 0.0
    for category, monthly_amount in monthly_spending.items():
        annual_spending = monthly_amount * 12
        reward_rate = card.rewards.get(category, card.rewards['default'])
        points = annual_spending * reward_rate
        cash_value = points * card.point_value
        total_value += cash_value
    
    net_value = total_value - card.annual_fee
    
    if card.annual_fee > 0:
        roi = (net_value / card.annual_fee) * 100
    else:
        roi = None
    
    return AnnualValue(card, total_value, net_value, roi)