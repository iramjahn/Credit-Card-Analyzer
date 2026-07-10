# backend/core/categories.py
#
# Single source of truth for spending categories across the whole app.
# Transactions, the ML feature vector, the recommendation endpoint, and the
# custom-card validator all import from here so the vocabulary can't drift.


class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Category({self.name})"


# Canonical spending categories — what a real purchase can be tagged as.
# The ML feature vector is built over this exact ordered list, so keep the
# order stable (append new categories at the end before "other").
CATEGORIES = [
    Category("dining", "Dining & Restaurants"),
    Category("groceries", "Groceries"),
    Category("travel", "Travel"),
    Category("flights", "Flights"),
    Category("hotels", "Hotels"),
    Category("streaming", "Streaming"),
    Category("transit", "Transit & Commuting"),
    Category("drugstores", "Drugstores"),
    Category("other", "Other/General"),
]

# Set of valid spending-category ids (used to validate transactions, etc.).
SPENDING_CATEGORIES = [c.id for c in CATEGORIES]
SPENDING_CATEGORY_SET = set(SPENDING_CATEGORIES)

# Catch-all used by the ML/feature layer when a transaction category is unknown.
DEFAULT_SPENDING_CATEGORY = "other"

# Special keys that may appear in a card's *reward structure* but are not
# user-selectable spending categories: a per-card fallback rate ("default")
# plus structural bonus keys some issuers use. The card validator allows these
# in a rewards dict in addition to the spending categories above.
REWARD_STRUCTURE_KEYS = {
    "default",        # fallback rate for any category not listed
    "online_grocery",
    "rotating",       # quarterly rotating 5% categories
    "top_category",   # auto-5%-in-your-top-category cards (Citi Custom Cash)
    "chase_travel",   # portal-only elevated rate
}

# Everything that is allowed as a key in a rewards dict.
VALID_REWARD_KEYS = SPENDING_CATEGORY_SET | REWARD_STRUCTURE_KEYS
