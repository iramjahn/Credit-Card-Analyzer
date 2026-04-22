from backend.core.card_database import CreditCard
from backend.core.calculator import calculate_rewards, RewardCalculation

class CardComparison:
    """Stores a card and its reward calculation for comparison"""
    def __init__(self, card, calculation):
        self.card = card                    # CreditCard object
        self.calculation = calculation      # RewardCalculation object
    
    def __repr__(self):
        return f"CardComparison({self.card.name}: ${self.calculation.cash_value:.2f})"

def find_best_card(cards, amount, category) -> list:
    results = []
    for card in cards:
        calc = calculate_rewards(card, amount, category)
        comparison = CardComparison(card, calc)
        results.append(comparison)

    results.sort(key = lambda x: x.calculation.cash_value, reverse =True)
    return results

