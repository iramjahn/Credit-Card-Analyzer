# app_state.py

from typing import List, Dict
from card_database import CreditCard
import re

class AppState:
    """Manages the application's state/data"""
    
    def __init__(self):
        """Initialize with default values"""
        self.user_cards: List[CreditCard] = []
        self.purchase_amount: float = 0.0
        self.selected_category: str = 'dining'
        self.monthly_spending: Dict[str, float] = {
            'dining': 500,
            'groceries': 600,
            'travel': 300,
            'gas': 150,
            'drugstores': 100,
            'entertainment': 200,
            'shopping': 400,
            'default': 300
        }
        self.active_tab: str = 'recommend'
    
    def add_card(self, card: CreditCard) -> None:
        """Add a card to user's wallet (prevents duplicates)"""
        if not any(c.id == card.id for c in self.user_cards):
            self.user_cards.append(card)
    
    def remove_card(self, card_id: str) -> None:
        """Remove a card from user's wallet by ID"""
        self.user_cards = [c for c in self.user_cards if c.id != card_id]
    
    def update_spending(self, category: str, amount: float) -> None:
        """Update monthly spending for a category"""
        self.monthly_spending[category] = amount
    
    def get_total_monthly_spending(self) -> float:
        """Calculate total monthly spending across all categories"""
        return sum(self.monthly_spending.values())
    
    def reset(self) -> None:
        """Reset state to defaults"""
        self.__init__()
    
    def add_custom_card(
        self,
        name: str,
        issuer: str,
        annual_fee: int,
        rewards: Dict[str, float],
        point_value: float,
        benefits: List[str]
    ) -> CreditCard:
        """Create and add a custom card from user input"""
        custom_id = f"custom-{name.lower().replace(' ', '-')}"
        
        new_card = CreditCard(
            id=custom_id,
            name=name,
            issuer=issuer,
            annual_fee=annual_fee,
            rewards=rewards,
            point_value=point_value,
            benefits=benefits,
            signup_bonus={}
        )
        
        self.add_card(new_card)
        return new_card
    
    def get_all_benefits(self) -> Dict[str, List[str]]:
        """Get all benefits from all user's cards"""
        all_benefits = {}
        for card in self.user_cards:
            all_benefits[card.name] = card.benefits
        return all_benefits
    
    def get_total_benefit_value(self) -> float:
        """Calculate estimated annual value of all card benefits"""
        total_value = 0.0
        
        for card in self.user_cards:
            for benefit in card.benefits:
                matches = re.findall(r'\$(\d+)', benefit)
                for match in matches:
                    total_value += float(match)
        
        return total_value
    
    def __repr__(self) -> str:
        return f"AppState(cards={len(self.user_cards)}, tab='{self.active_tab}', spending=${self.get_total_monthly_spending():.0f})"


# Test code
if __name__ == '__main__':
    from card_database import chase_sapphire_preferred, amex_gold
    
    print("=== Testing AppState ===\n")
    
    # Test 1: Initial state
    state = AppState()
    print(f"1. Initial state: {state}")
    print(f"   Total spending: ${state.get_total_monthly_spending()}")
    
    # Test 2: Add preset cards
    print("\n2. Adding preset cards...")
    state.add_card(chase_sapphire_preferred)
    state.add_card(amex_gold)
    print(f"   Cards: {len(state.user_cards)}")
    
    # Test 3: Add duplicate (should not add)
    print("\n3. Trying to add duplicate...")
    state.add_card(chase_sapphire_preferred)
    print(f"   Cards: {len(state.user_cards)} (should still be 2)")
    
    # Test 4: Add custom card
    print("\n4. Adding custom card...")
    custom = state.add_custom_card(
        name="My Custom Card",
        issuer="Local Bank",
        annual_fee=50,
        rewards={'dining': 2.5, 'groceries': 3, 'default': 1},
        point_value=0.01,
        benefits=["$100 annual bonus", "Free roadside assistance"]
    )
    print(f"   Custom card: {custom.name} (ID: {custom.id})")
    print(f"   Total cards: {len(state.user_cards)}")
    
    # Test 5: Get all benefits
    print("\n5. All benefits:")
    benefits = state.get_all_benefits()
    for card_name, card_benefits in benefits.items():
        print(f"   {card_name}:")
        for benefit in card_benefits[:2]:
            print(f"     - {benefit}")
    
    # Test 6: Calculate benefit value
    print("\n6. Total benefit value:")
    total_value = state.get_total_benefit_value()
    print(f"   ${total_value:.2f}")
    
    # Test 7: Update spending
    print("\n7. Update spending...")
    state.update_spending('dining', 800)
    print(f"   New total: ${state.get_total_monthly_spending()}")
    
    # Test 8: Remove card
    print("\n8. Remove card...")
    state.remove_card('csp')
    print(f"   Cards remaining: {len(state.user_cards)}")
    
    # Test 9: Reset
    print("\n9. Reset...")
    state.reset()
    print(f"   {state}")