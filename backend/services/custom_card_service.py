# backend/services/custom_card_service.py

import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

from typing import Dict, List, Tuple, Optional
try:
    from backend.core.card_database import CreditCard
    from backend.services.validators import CardValidator
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from core.card_database import CreditCard
    from services.validators import CardValidator

class CustomCardService:
    """Manages custom user-created credit cards"""
    
    def __init__(self):
        self.validator = CardValidator()
        # In-memory storage (will be replaced with database later)
        self.custom_cards = {}  # {card_id: CreditCard}
    
    # ============================================
    # CREATE METHODS
    # ============================================
    
    def create_custom_card(
        self,
        user_id: int,
        name: str,
        issuer: str,
        annual_fee: int,
        point_value: float,
        rewards: Dict[str, float],
        benefits: List[str]
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Create a new custom card manually
        
        Args:
            user_id: ID of user creating the card
            name: Card name
            issuer: Bank/issuer name
            annual_fee: Annual fee in dollars
            point_value: Value per point (e.g., 0.01 = 1 cent)
            rewards: Rewards structure dict
            benefits: List of benefits
            
        Returns:
            (success, card, errors)
        """
        # Validate all inputs
        is_valid, errors = self.validator.validate_all(
            name, issuer, annual_fee, point_value, rewards, benefits
        )
        
        if not is_valid:
            return False, None, errors
        
        # Generate unique card ID
        card_id = self._generate_card_id(user_id, name)
        
        # Check if card ID already exists
        if card_id in self.custom_cards:
            return False, None, [f"A card with this name already exists (ID: {card_id})"]
        
        # Create CreditCard object
        card = CreditCard(
            id=card_id,
            name=name,
            issuer=issuer,
            annual_fee=annual_fee,
            rewards=rewards,
            point_value=point_value,
            benefits=benefits,
            signup_bonus={}  # Custom cards don't have signup bonuses
        )
        
        # Save card
        self.custom_cards[card_id] = card
        
        return True, card, []
    
    def create_card_from_url(
        self,
        user_id: int,
        url: str
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Create a custom card by scraping a URL
        
        Args:
            user_id: ID of user creating the card
            url: URL to credit card page
            
        Returns:
            (success, card, errors)
        """
        try:
            from backend.services.web_scraper import CreditCardWebScraper
        except ImportError:
            from services.web_scraper import CreditCardWebScraper
        
        print(f"\n🌐 Creating card from URL: {url}\n")
        
        # Scrape the URL
        scraper = CreditCardWebScraper()
        success, card_data, error = scraper.scrape_card_from_url(url)
        
        if not success:
            return False, None, [error]
        
        print("\n✅ Scraped successfully! Creating card...\n")
        
        # Create card using scraped data
        return self.create_custom_card(
            user_id=user_id,
            name=card_data['name'],
            issuer=card_data['issuer'],
            annual_fee=card_data['annual_fee'],
            point_value=card_data['point_value'],
            rewards=card_data['rewards'],
            benefits=card_data['benefits']
        )
    
    # ============================================
    # READ METHODS
    # ============================================
    
    def get_custom_card(self, card_id: str) -> Optional[CreditCard]:
        """
        Get a custom card by ID
        
        Args:
            card_id: Card ID
            
        Returns:
            CreditCard if found, None otherwise
        """
        return self.custom_cards.get(card_id)
    
    def get_all_custom_cards(self, user_id: int) -> List[CreditCard]:
        """
        Get all custom cards for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            List of CreditCard objects
        """
        # Filter cards by user ID (card ID starts with custom-user-{user_id}-)
        prefix = f"custom-user-{user_id}-"
        return [
            card for card_id, card in self.custom_cards.items()
            if card_id.startswith(prefix)
        ]
    
    def get_all_cards(self) -> List[CreditCard]:
        """
        Get all custom cards (across all users)
        
        Returns:
            List of all CreditCard objects
        """
        return list(self.custom_cards.values())
    
    def card_exists(self, card_id: str) -> bool:
        """
        Check if a card exists
        
        Args:
            card_id: Card ID
            
        Returns:
            True if exists, False otherwise
        """
        return card_id in self.custom_cards
    
    def get_user_card_count(self, user_id: int) -> int:
        """
        Get count of custom cards for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of cards
        """
        return len(self.get_all_custom_cards(user_id))
    
    # ============================================
    # UPDATE METHODS
    # ============================================
    
    def edit_custom_card(
        self,
        card_id: str,
        name: Optional[str] = None,
        issuer: Optional[str] = None,
        annual_fee: Optional[int] = None,
        point_value: Optional[float] = None,
        rewards: Optional[Dict[str, float]] = None,
        benefits: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Edit an existing custom card
        
        Only provided fields will be updated
        
        Args:
            card_id: ID of card to edit
            name: New name (optional)
            issuer: New issuer (optional)
            annual_fee: New annual fee (optional)
            point_value: New point value (optional)
            rewards: New rewards structure (optional)
            benefits: New benefits list (optional)
            
        Returns:
            (success, updated_card, errors)
        """
        # Check if card exists
        if card_id not in self.custom_cards:
            return False, None, ["Card not found"]
        
        card = self.custom_cards[card_id]
        errors = []
        
        # Update fields if provided and valid
        if name is not None:
            valid, error = self.validator.validate_card_name(name)
            if not valid:
                errors.append(error)
            else:
                card.name = name
        
        if issuer is not None:
            valid, error = self.validator.validate_issuer(issuer)
            if not valid:
                errors.append(error)
            else:
                card.issuer = issuer
        
        if annual_fee is not None:
            valid, error = self.validator.validate_annual_fee(annual_fee)
            if not valid:
                errors.append(error)
            else:
                card.annual_fee = annual_fee
        
        if point_value is not None:
            valid, error = self.validator.validate_point_value(point_value)
            if not valid:
                errors.append(error)
            else:
                card.point_value = point_value
        
        if rewards is not None:
            valid, error = self.validator.validate_rewards(rewards)
            if not valid:
                errors.append(error)
            else:
                card.rewards = rewards
        
        if benefits is not None:
            valid, error = self.validator.validate_benefits(benefits)
            if not valid:
                errors.append(error)
            else:
                card.benefits = benefits
        
        if errors:
            return False, None, errors
        
        return True, card, []
    
    def update_card_rewards(
        self,
        card_id: str,
        category: str,
        rate: float
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Update a single reward category
        
        Args:
            card_id: Card ID
            category: Category to update
            rate: New reward rate
            
        Returns:
            (success, updated_card, errors)
        """
        if card_id not in self.custom_cards:
            return False, None, ["Card not found"]
        
        card = self.custom_cards[card_id]
        
        # Validate category
        if category not in self.validator.VALID_CATEGORIES:
            return False, None, [f"Invalid category: {category}"]
        
        # Validate rate
        if rate < 0 or rate > self.validator.MAX_REWARD_RATE:
            return False, None, [f"Invalid reward rate: {rate}"]
        
        # Update
        card.rewards[category] = rate
        
        return True, card, []
    
    def add_benefit(
        self,
        card_id: str,
        benefit: str
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Add a benefit to a card
        
        Args:
            card_id: Card ID
            benefit: Benefit description
            
        Returns:
            (success, updated_card, errors)
        """
        if card_id not in self.custom_cards:
            return False, None, ["Card not found"]
        
        card = self.custom_cards[card_id]
        
        # Validate benefit
        if not benefit or len(benefit) > 500:
            return False, None, ["Benefit must be 1-500 characters"]
        
        # Add if not already there
        if benefit not in card.benefits:
            card.benefits.append(benefit)
        
        return True, card, []
    
    def remove_benefit(
        self,
        card_id: str,
        benefit: str
    ) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Remove a benefit from a card
        
        Args:
            card_id: Card ID
            benefit: Benefit to remove
            
        Returns:
            (success, updated_card, errors)
        """
        if card_id not in self.custom_cards:
            return False, None, ["Card not found"]
        
        card = self.custom_cards[card_id]
        
        # Remove if exists
        if benefit in card.benefits:
            card.benefits.remove(benefit)
        
        return True, card, []
    
    # ============================================
    # DELETE METHODS
    # ============================================
    
    def delete_custom_card(self, card_id: str) -> bool:
        """
        Delete a custom card
        
        Args:
            card_id: Card ID
            
        Returns:
            True if deleted, False if not found
        """
        if card_id in self.custom_cards:
            del self.custom_cards[card_id]
            return True
        return False
    
    def delete_all_user_cards(self, user_id: int) -> int:
        """
        Delete all custom cards for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of cards deleted
        """
        prefix = f"custom-user-{user_id}-"
        to_delete = [
            card_id for card_id in self.custom_cards.keys()
            if card_id.startswith(prefix)
        ]
        
        for card_id in to_delete:
            del self.custom_cards[card_id]
        
        return len(to_delete)
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def _generate_card_id(self, user_id: int, name: str) -> str:
        """
        Generate unique card ID
        
        Format: custom-user-{user_id}-{name-slug}
        Example: custom-user-1-my-travel-card
        
        Args:
            user_id: User ID
            name: Card name
            
        Returns:
            Card ID string
        """
        # Convert name to URL-friendly slug
        slug = name.lower().replace(' ', '-').replace('_', '-')
        # Remove special characters
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        # Remove multiple consecutive dashes
        slug = '-'.join(filter(None, slug.split('-')))
        # Limit length
        slug = slug[:50]
        
        return f"custom-user-{user_id}-{slug}"
    
    def export_card_data(self, card_id: str) -> Optional[Dict]:
        """
        Export card as dictionary (for saving to database later)
        
        Args:
            card_id: Card ID
            
        Returns:
            Dictionary with card data, or None if not found
        """
        card = self.get_custom_card(card_id)
        if not card:
            return None
        
        return {
            'id': card.id,
            'name': card.name,
            'issuer': card.issuer,
            'annual_fee': card.annual_fee,
            'point_value': card.point_value,
            'rewards': card.rewards,
            'benefits': card.benefits,
            'signup_bonus': card.signup_bonus
        }
    
    def import_card_data(self, user_id: int, card_data: Dict) -> Tuple[bool, Optional[CreditCard], List[str]]:
        """
        Import card from dictionary (for loading from database later)
        
        Args:
            user_id: User ID
            card_data: Dictionary with card data
            
        Returns:
            (success, card, errors)
        """
        try:
            return self.create_custom_card(
                user_id=user_id,
                name=card_data['name'],
                issuer=card_data['issuer'],
                annual_fee=card_data['annual_fee'],
                point_value=card_data['point_value'],
                rewards=card_data['rewards'],
                benefits=card_data.get('benefits', [])
            )
        except KeyError as e:
            return False, None, [f"Missing required field: {e}"]
        except Exception as e:
            return False, None, [f"Import error: {str(e)}"]
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about custom cards
        
        Returns:
            Dictionary with stats
        """
        total_cards = len(self.custom_cards)
        
        # Count cards per user
        user_counts = {}
        for card_id in self.custom_cards.keys():
            # Extract user_id from card_id (format: custom-user-{id}-...)
            parts = card_id.split('-')
            if len(parts) >= 3:
                user_id = parts[2]
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        # Average annual fee
        if total_cards > 0:
            avg_fee = sum(c.annual_fee for c in self.custom_cards.values()) / total_cards
        else:
            avg_fee = 0
        
        return {
            'total_cards': total_cards,
            'unique_users': len(user_counts),
            'cards_per_user': user_counts,
            'average_annual_fee': avg_fee
        }
