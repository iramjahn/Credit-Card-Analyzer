# backend/services/validators.py

from typing import Dict, List, Tuple


class CardValidator:
    """Validates credit card data before creation or update"""

    VALID_CATEGORIES = {
        'dining', 'groceries', 'travel', 'gas', 'drugstores',
        'entertainment', 'shopping', 'streaming', 'transit',
        'flights', 'hotels', 'online_grocery', 'rotating',
        'top_category', 'chase_travel', 'default'
    }

    MAX_REWARD_RATE = 20.0

    def validate_card_name(self, name: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Card name cannot be empty"
        if len(name) > 100:
            return False, "Card name must be 100 characters or fewer"
        return True, ""

    def validate_issuer(self, issuer: str) -> Tuple[bool, str]:
        if not issuer or not issuer.strip():
            return False, "Issuer cannot be empty"
        if len(issuer) > 100:
            return False, "Issuer must be 100 characters or fewer"
        return True, ""

    def validate_annual_fee(self, annual_fee) -> Tuple[bool, str]:
        if not isinstance(annual_fee, (int, float)):
            return False, "Annual fee must be a number"
        if annual_fee < 0:
            return False, "Annual fee cannot be negative"
        return True, ""

    def validate_point_value(self, point_value) -> Tuple[bool, str]:
        if not isinstance(point_value, (int, float)):
            return False, "Point value must be a number"
        if point_value <= 0:
            return False, "Point value must be greater than 0"
        if point_value > 1:
            return False, "Point value cannot exceed 1 (100 cents)"
        return True, ""

    def validate_rewards(self, rewards: Dict) -> Tuple[bool, str]:
        if not isinstance(rewards, dict):
            return False, "Rewards must be a dictionary"
        if 'default' not in rewards:
            return False, "Rewards must include a 'default' category"
        for category, rate in rewards.items():
            if not isinstance(rate, (int, float)):
                return False, f"Reward rate for '{category}' must be a number"
            if rate < 0 or rate > self.MAX_REWARD_RATE:
                return False, f"Reward rate for '{category}' must be between 0 and {self.MAX_REWARD_RATE}"
        return True, ""

    def validate_benefits(self, benefits: List) -> Tuple[bool, str]:
        if not isinstance(benefits, list):
            return False, "Benefits must be a list"
        for benefit in benefits:
            if not isinstance(benefit, str) or len(benefit) > 500:
                return False, "Each benefit must be a string of 500 characters or fewer"
        return True, ""

    def validate_all(
        self,
        name: str,
        issuer: str,
        annual_fee,
        point_value,
        rewards: Dict,
        benefits: List
    ) -> Tuple[bool, List[str]]:
        errors = []

        valid, error = self.validate_card_name(name)
        if not valid:
            errors.append(error)

        valid, error = self.validate_issuer(issuer)
        if not valid:
            errors.append(error)

        valid, error = self.validate_annual_fee(annual_fee)
        if not valid:
            errors.append(error)

        valid, error = self.validate_point_value(point_value)
        if not valid:
            errors.append(error)

        valid, error = self.validate_rewards(rewards)
        if not valid:
            errors.append(error)

        valid, error = self.validate_benefits(benefits)
        if not valid:
            errors.append(error)

        return len(errors) == 0, errors
