from backend.core.card_database import CreditCard

class RewardCalculation:
    """Stores the results of a reward calculation"""
    def __init__(self, reward_rate, points, cash_value, note=None):
        self.reward_rate = reward_rate
        self.points = points
        self.cash_value = cash_value
        self.note = note  # caveat surfaced to the user, if any

    def __repr__(self):
        return f"RewardCalculation(rate = {self.reward_rate}x, points = {self.points}, value = ${self.cash_value:.2f})"


def resolve_purchase_rate(card, category):
    """
    Resolve the reward rate a single purchase in `category` earns on `card`.

    Special reward keys:
    - "top_category": the rate applies only to the cardholder's highest-spend
      category each cycle. For a single-purchase comparison we apply it
      optimistically (the user can dedicate the card to this category) and
      attach a caveat note.
    - "rotating": quarterly rotating categories we can't know at purchase
      time — resolved conservatively to the default rate.

    Returns (rate, note).
    """
    if category in card.rewards:
        return card.rewards[category], None
    if 'top_category' in card.rewards:
        note = (
            f"{card.rewards['top_category']}x applies only if this is your "
            "highest-spend category this cycle"
        )
        cap = card.reward_caps.get('top_category')
        if cap:
            note += f" (up to ${cap['cap']}/{cap['period'].rstrip('ly')})"
        return card.rewards['top_category'], note
    return card.rewards['default'], None


def calculate_rewards(card, amount, category) -> RewardCalculation:
    reward_rate, note = resolve_purchase_rate(card, category)
    points = round(amount * reward_rate)
    cash_value = points * card.point_value
    return RewardCalculation(reward_rate, points, cash_value, note)
