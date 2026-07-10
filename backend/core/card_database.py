# card_database.py
from typing import Dict, List

class CreditCard:
    def __init__(self, id, name, issuer, annual_fee, rewards, point_value, benefits, signup_bonus, reward_caps=None):
        self.id = id
        self.name = name
        self.issuer = issuer
        self.annual_fee = annual_fee
        self.rewards = rewards
        self.point_value = point_value
        self.benefits = benefits
        self.signup_bonus = signup_bonus
        # Spend caps on bonus categories: {reward_key: {"cap": dollars,
        # "period": "monthly"|"quarterly"|"annual", "post_rate": rate after cap}}
        self.reward_caps = reward_caps or {}

    def __repr__(self):
        return f"CreditCard({self.name})"


# Card 1: Chase Sapphire Preferred
chase_sapphire_preferred = CreditCard(
    id='csp',
    name='Chase Sapphire Preferred',
    issuer='Chase',
    annual_fee=95,
    rewards={
        'chase_travel': 5,   # 5x only via the Chase Travel portal
        'travel': 2,         # 2x on general travel booked directly
        'dining': 3,
        'online_grocery': 3,
        'streaming': 3,
        'default': 1
    },
    point_value=0.0125,
    benefits=[
        '$50 annual hotel credit via Chase Travel',
        'No foreign transaction fees',
        '10% anniversary bonus on purchases',
        'DashPass membership ($120 value)',
        'Primary rental car insurance'
    ],
    signup_bonus={
        'amount': 75000,
        'spend_requirement': 5000,
        'months': 3
    }
)

# Card 2: American Express Gold
amex_gold = CreditCard(
    id='amex-gold',
    name='American Express Gold',
    issuer='American Express',
    annual_fee=250,
    rewards={
        'dining': 4,
        'groceries': 4,
        'flights': 3,
        'default': 1
    },
    reward_caps={
        'groceries': {'cap': 25000, 'period': 'annual', 'post_rate': 1},
    },
    point_value=0.01,
    benefits=[
        '$120 Uber Cash annually',
        '$120 dining credits annually ($10/month)',
        'No foreign transaction fees',
        '4x points at restaurants'
    ],
    signup_bonus={
        'amount': 60000,
        'spend_requirement': 6000,
        'months': 6
    }
)

# Card 3: Chase Freedom Unlimited
chase_freedom_unlimited = CreditCard(
    id='chase-freedom-unlimited',
    name='Chase Freedom Unlimited',
    issuer='Chase',
    annual_fee=0,
    rewards={
        'chase_travel': 5,   # 5x only via the Chase Travel portal
        'dining': 3,
        'drugstores': 3,
        'default': 1.5
    },
    point_value=0.01,
    benefits=[
        'No annual fee',
        '0% intro APR for 15 months',
        'Cell phone protection',
        'No foreign transaction fees'
    ],
    signup_bonus={
        'amount': 20000,
        'spend_requirement': 500,
        'months': 3
    }
)

# Card 4: Capital One Venture
capital_one_venture = CreditCard(
    id='cap1-venture',
    name='Capital One Venture',
    issuer='Capital One',
    annual_fee=95,
    rewards={
        'hotels': 5,
        'default': 2
    },
    point_value=0.01,
    benefits=[
        '$250 Capital One Travel credit (first year)',
        'TSA PreCheck/Global Entry credit ($120)',
        'No foreign transaction fees',
        'Transfer to airline partners at 1:1'
    ],
    signup_bonus={
        'amount': 75000,
        'spend_requirement': 4000,
        'months': 3
    }
)

# Card 5: American Express Platinum
amex_platinum = CreditCard(
    id='amex-platinum',
    name='American Express Platinum',
    issuer='American Express',
    annual_fee=695,
    rewards={
        'flights': 5,
        'hotels': 5,
        'default': 1
    },
    point_value=0.015,
    benefits=[
        '$200 airline fee credit',
        '$200 hotel credit',
        '$200 Uber Cash ($15/month + $20 Dec)',
        '$155 Walmart+ credit',
        'Airport lounge access (1,550+ lounges)',
        'TSA PreCheck/Global Entry credit'
    ],
    signup_bonus={
        'amount': 125000,
        'spend_requirement': 8000,
        'months': 6
    }
)

# Card 6: Citi Custom Cash
citi_custom_cash = CreditCard(
    id='citi-custom',
    name='Citi Custom Cash',
    issuer='Citi',
    annual_fee=0,
    rewards={
        'top_category': 5,   # applies to the highest-spend eligible category
        'default': 1
    },
    reward_caps={
        'top_category': {'cap': 500, 'period': 'monthly', 'post_rate': 1},
    },
    point_value=0.01,
    benefits=[
        'No annual fee',
        'Automatic 5% in top category (up to $500/month)',
        '0% intro APR for 15 months'
    ],
    signup_bonus={
        'amount': 20000,
        'spend_requirement': 1500,
        'months': 3
    }
)

# Card 7: American Express Blue Cash Preferred
amex_blue_cash_preferred = CreditCard(
    id='amex-bcp',
    name='American Express Blue Cash Preferred',
    issuer='American Express',
    annual_fee=95,
    rewards={
        'groceries': 6,
        'streaming': 6,
        'transit': 3,
        'default': 1
    },
    reward_caps={
        'groceries': {'cap': 6000, 'period': 'annual', 'post_rate': 1},
    },
    point_value=0.01,
    benefits=[
        '$84 Disney+ credit annually',
        'No foreign transaction fees',
        'High grocery cash back rate'
    ],
    signup_bonus={
        'amount': 25000,
        'spend_requirement': 3000,
        'months': 6
    }
)

# Card 8: Chase Freedom Flex
chase_freedom_flex = CreditCard(
    id='chase-freedom-flex',
    name='Chase Freedom Flex',
    issuer='Chase',
    annual_fee=0,
    rewards={
        'rotating': 5,       # quarterly categories, resolved conservatively
        'chase_travel': 5,   # 5x only via the Chase Travel portal
        'dining': 3,
        'drugstores': 3,
        'default': 1
    },
    point_value=0.01,
    benefits=[
        'No annual fee',
        '5% rotating quarterly categories',
        'Cell phone protection',
        '0% intro APR for 15 months'
    ],
    signup_bonus={
        'amount': 20000,
        'spend_requirement': 500,
        'months': 3
    }
)

# Card 9: Chase Sapphire Reserve
chase_sapphire_reserve = CreditCard(
    id='csr',
    name='Chase Sapphire Reserve',
    issuer='Chase',
    annual_fee=795,
    rewards={
        'chase_travel': 8,
        'flights': 4,
        'hotels': 4,
        'dining': 3,
        'default': 1
    },
    point_value=0.02,
    benefits=[
        '$300 annual travel credit',
        '$500 The Edit hotel credit',
        '$250 The Shops at Chase credit',
        'Airport lounge access (Chase Sapphire Lounges)',
        'Priority Pass lounge access',
        'No foreign transaction fees',
        'TSA PreCheck/Global Entry credit'
    ],
    signup_bonus={
        'amount': 125000,
        'spend_requirement': 6000,
        'months': 3
    }
)

# Card 10: Discover it Cash Back
discover_it = CreditCard(
    id='discover-it',
    name='Discover it Cash Back',
    issuer='Discover',
    annual_fee=0,
    rewards={
        'rotating': 5,
        'default': 1
    },
    point_value=0.01,
    benefits=[
        'No annual fee',
        'Cashback Match (doubles all cash back first year)',
        '5% rotating quarterly categories',
        'No foreign transaction fees',
        'Free FICO credit score'
    ],
    signup_bonus={
        'amount': 0,
        'spend_requirement': 0,
        'months': 12
    }
)

# Store all cards in a list
CARD_DATABASE = [
    chase_sapphire_preferred,
    amex_gold,
    chase_freedom_unlimited,
    capital_one_venture,
    amex_platinum,
    citi_custom_cash,
    amex_blue_cash_preferred,
    chase_freedom_flex,
    chase_sapphire_reserve,
    discover_it
]

# Test the database
if __name__ == '__main__':
    print(f"Loaded {len(CARD_DATABASE)} credit cards")
    print("\nCards in database:")
    for card in CARD_DATABASE:
        print(f"  - {card.name} (Annual Fee: ${card.annual_fee})")