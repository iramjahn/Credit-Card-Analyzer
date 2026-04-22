from backend.core.card_database import CreditCard

class RewardCalculation:
    """Stores the results of a reward calculation"""
    def __init__(self, reward_rate, points, cash_value):
        self.reward_rate = reward_rate
        self.points = points
        self.cash_value = cash_value
    
    def __repr__(self):
        return f"RewardCalculation(rate = {self.reward_rate}x, points = {self.points}, value = ${self.cash_value:.2f})"


def calculate_rewards(card, amount, category) -> RewardCalculation:
    reward_rate = card.rewards.get(category, card.rewards['default'])
    points = amount * reward_rate
    points = round(points)
    cash_value = points * card.point_value
    return RewardCalculation(reward_rate, points, cash_value)

