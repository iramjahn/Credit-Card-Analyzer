# annual_calculator.py
#
# Annualizes a monthly spending profile against a card's reward structure,
# honoring spend caps and top-category semantics, and nets out the annual fee.

from typing import Optional
from backend.core.card_database import CreditCard

_PERIODS_PER_YEAR = {"monthly": 12, "quarterly": 4, "annual": 1}


class AnnualValue():
    """Calculates reward value from card over the year."""
    def __init__(self, card: CreditCard, total_value: float, net_value: float, roi: Optional[float]):
        self.card = card
        self.total_value = total_value
        self.net_value = net_value
        self.roi = roi

    def __repr__(self) -> str:
        return f"AnnualValue({self.card.name}: total=${self.total_value:.2f}, net=${self.net_value:.2f})"


def _applied_reward_keys(card: CreditCard, annual_spending: dict) -> dict:
    """Map each spending category to the reward key that applies to it.

    - A direct category match wins.
    - "top_category" is assigned to the single highest-spend category if it
      beats that category's current rate (how these cards actually work).
    - "rotating" is never assigned (conservative: we can't know the active
      quarterly categories), so that spend earns the default rate.
    """
    applied = {
        cat: (cat if cat in card.rewards else "default")
        for cat in annual_spending
    }
    if "top_category" in card.rewards and annual_spending:
        top_cat = max(annual_spending, key=annual_spending.get)
        if card.rewards["top_category"] > card.rewards[applied[top_cat]]:
            applied[top_cat] = "top_category"
    return applied


def calculate_annual_value(card: CreditCard, monthly_spending: dict[str, float]) -> AnnualValue:
    annual_spending = {cat: amt * 12 for cat, amt in monthly_spending.items()}
    applied = _applied_reward_keys(card, annual_spending)

    total_value = 0.0
    for category, spend in annual_spending.items():
        key = applied[category]
        rate = card.rewards[key]
        cap_conf = card.reward_caps.get(key)
        if cap_conf:
            annual_cap = cap_conf["cap"] * _PERIODS_PER_YEAR[cap_conf["period"]]
            capped_spend = min(spend, annual_cap)
            post_rate = cap_conf.get("post_rate", card.rewards["default"])
            points = capped_spend * rate + (spend - capped_spend) * post_rate
        else:
            points = spend * rate
        total_value += points * card.point_value

    net_value = total_value - card.annual_fee

    if card.annual_fee > 0:
        roi = (net_value / card.annual_fee) * 100
    else:
        roi = None

    return AnnualValue(card, total_value, net_value, roi)
