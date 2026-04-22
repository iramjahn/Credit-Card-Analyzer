# backend/services/benefits_tracker.py

import sys
import os

# Setup imports
if __name__ == '__main__':
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from backend.core.card_database import CreditCard


@dataclass
class Benefit:
    """Represents a single credit card benefit"""
    
    card_id: str
    card_name: str
    benefit_name: str
    total_value: float  # Total benefit value in dollars
    used_value: float  # How much has been used
    reset_period: str  # 'annual', 'monthly', 'one-time', 'none'
    reset_date: Optional[datetime]  # When benefit resets
    
    @property
    def remaining_value(self) -> float:
        """Calculate remaining benefit value"""
        return max(0, self.total_value - self.used_value)
    
    @property
    def usage_percentage(self) -> float:
        """Calculate what percentage has been used"""
        if self.total_value == 0:
            return 0
        return (self.used_value / self.total_value) * 100
    
    @property
    def is_fully_used(self) -> bool:
        """Check if benefit is fully used"""
        return self.used_value >= self.total_value
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if benefit expires within 30 days"""
        if not self.reset_date:
            return False
        days_until_reset = (self.reset_date - datetime.now()).days
        return 0 < days_until_reset <= 30
    
    @property
    def days_until_reset(self) -> Optional[int]:
        """Days until benefit resets"""
        if not self.reset_date:
            return None
        days = (self.reset_date - datetime.now()).days
        return max(0, days)
    
    def __repr__(self) -> str:
        return f"Benefit({self.benefit_name}: ${self.remaining_value:.2f} remaining)"


class BenefitsTracker:
    """Manages and tracks credit card benefits"""
    
    def __init__(self):
        # In-memory storage (will be replaced with database later)
        self.benefits: List[Benefit] = []
    
    # ============================================
    # EXTRACT BENEFITS FROM CARDS
    # ============================================
    
    def extract_benefit_value(self, benefit_text: str) -> float:
        """
        Extract dollar value from benefit text
        
        Args:
            benefit_text: Benefit description like "$300 annual travel credit"
            
        Returns:
            Dollar value (e.g., 300.0) or 0 if no value found
        """
        import re
        
        # Look for $XXX pattern
        match = re.search(r'\$(\d+)', benefit_text)
        if match:
            return float(match.group(1))
        
        return 0.0
    
    def determine_reset_period(self, benefit_text: str) -> str:
        """
        Determine reset period from benefit text
        
        Args:
            benefit_text: Benefit description
            
        Returns:
            'annual', 'monthly', 'one-time', or 'none'
        """
        text_lower = benefit_text.lower()
        
        if 'annual' in text_lower or 'yearly' in text_lower or 'per year' in text_lower:
            return 'annual'
        elif 'monthly' in text_lower or 'per month' in text_lower:
            return 'monthly'
        elif 'one-time' in text_lower or 'one time' in text_lower:
            return 'one-time'
        else:
            return 'none'
    
    def calculate_reset_date(self, reset_period: str) -> Optional[datetime]:
        """
        Calculate next reset date based on period
        
        Args:
            reset_period: 'annual', 'monthly', 'one-time', or 'none'
            
        Returns:
            Next reset date or None
        """
        now = datetime.now()
        
        if reset_period == 'annual':
            # Reset on January 1st next year
            next_year = now.year + 1
            return datetime(next_year, 1, 1)
        
        elif reset_period == 'monthly':
            # Reset on 1st of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        
        elif reset_period == 'one-time':
            # No reset
            return None
        
        else:  # 'none'
            return None
    
    def add_card_benefits(self, card: CreditCard) -> int:
        """
        Extract and add all benefits from a card
        
        Args:
            card: CreditCard object
            
        Returns:
            Number of trackable benefits added
        """
        added_count = 0
        
        for benefit_text in card.benefits:
            # Extract value
            value = self.extract_benefit_value(benefit_text)
            
            # Only track benefits with monetary value
            if value > 0:
                reset_period = self.determine_reset_period(benefit_text)
                reset_date = self.calculate_reset_date(reset_period)
                
                benefit = Benefit(
                    card_id=card.id,
                    card_name=card.name,
                    benefit_name=benefit_text,
                    total_value=value,
                    used_value=0.0,
                    reset_period=reset_period,
                    reset_date=reset_date
                )
                
                self.benefits.append(benefit)
                added_count += 1
        
        return added_count
    
    # ============================================
    # TRACK USAGE
    # ============================================
    
    def mark_benefit_used(
        self, 
        card_id: str, 
        benefit_name: str, 
        amount: float
    ) -> bool:
        """
        Mark a benefit as partially or fully used
        
        Args:
            card_id: Card ID
            benefit_name: Benefit name
            amount: Amount used
            
        Returns:
            True if successful, False if benefit not found
        """
        for benefit in self.benefits:
            if benefit.card_id == card_id and benefit.benefit_name == benefit_name:
                benefit.used_value = min(benefit.used_value + amount, benefit.total_value)
                return True
        
        return False
    
    def reset_benefit(self, card_id: str, benefit_name: str) -> bool:
        """
        Reset a benefit's usage to 0
        
        Args:
            card_id: Card ID
            benefit_name: Benefit name
            
        Returns:
            True if successful, False if benefit not found
        """
        for benefit in self.benefits:
            if benefit.card_id == card_id and benefit.benefit_name == benefit_name:
                benefit.used_value = 0.0
                # Update reset date
                benefit.reset_date = self.calculate_reset_date(benefit.reset_period)
                return True
        
        return False
    
    def auto_reset_expired_benefits(self) -> int:
        """
        Automatically reset benefits that have passed their reset date
        
        Returns:
            Number of benefits reset
        """
        now = datetime.now()
        reset_count = 0
        
        for benefit in self.benefits:
            if benefit.reset_date and benefit.reset_date <= now:
                benefit.used_value = 0.0
                benefit.reset_date = self.calculate_reset_date(benefit.reset_period)
                reset_count += 1
        
        return reset_count
    
    # ============================================
    # QUERY BENEFITS
    # ============================================
    
    def get_all_benefits(self) -> List[Benefit]:
        """Get all benefits"""
        return self.benefits
    
    def get_benefits_by_card(self, card_id: str) -> List[Benefit]:
        """Get all benefits for a specific card"""
        return [b for b in self.benefits if b.card_id == card_id]
    
    def get_unused_benefits(self) -> List[Benefit]:
        """Get benefits that haven't been used at all"""
        return [b for b in self.benefits if b.used_value == 0]
    
    def get_partially_used_benefits(self) -> List[Benefit]:
        """Get benefits that are partially used"""
        return [
            b for b in self.benefits 
            if 0 < b.used_value < b.total_value
        ]
    
    def get_fully_used_benefits(self) -> List[Benefit]:
        """Get benefits that are fully used"""
        return [b for b in self.benefits if b.is_fully_used]
    
    def get_expiring_benefits(self, days: int = 30) -> List[Benefit]:
        """
        Get benefits expiring within specified days
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of benefits expiring soon
        """
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        return [
            b for b in self.benefits 
            if b.reset_date and now < b.reset_date <= cutoff
        ]
    
    # ============================================
    # CALCULATE VALUES
    # ============================================
    
    def get_total_benefit_value(self) -> float:
        """Calculate total value of all benefits"""
        return sum(b.total_value for b in self.benefits)
    
    def get_total_used_value(self) -> float:
        """Calculate total value already used"""
        return sum(b.used_value for b in self.benefits)
    
    def get_total_remaining_value(self) -> float:
        """Calculate total remaining value across all benefits"""
        return sum(b.remaining_value for b in self.benefits)
    
    def get_card_benefit_value(self, card_id: str) -> Dict[str, float]:
        """
        Get benefit value breakdown for a specific card
        
        Returns:
            Dictionary with total, used, and remaining values
        """
        card_benefits = self.get_benefits_by_card(card_id)
        
        return {
            'total': sum(b.total_value for b in card_benefits),
            'used': sum(b.used_value for b in card_benefits),
            'remaining': sum(b.remaining_value for b in card_benefits)
        }
    
    # ============================================
    # STATISTICS & REPORTING
    # ============================================
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about benefits"""
        return {
            'total_benefits': len(self.benefits),
            'total_value': self.get_total_benefit_value(),
            'total_used': self.get_total_used_value(),
            'total_remaining': self.get_total_remaining_value(),
            'unused_count': len(self.get_unused_benefits()),
            'partially_used_count': len(self.get_partially_used_benefits()),
            'fully_used_count': len(self.get_fully_used_benefits()),
            'expiring_soon_count': len(self.get_expiring_benefits(30))
        }
    
    def generate_usage_report(self) -> str:
        """Generate a text report of benefit usage"""
        stats = self.get_statistics()
        
        report = "="*60 + "\n"
        report += "CREDIT CARD BENEFITS REPORT\n"
        report += "="*60 + "\n\n"
        
        report += f"Total Benefits: {stats['total_benefits']}\n"
        report += f"Total Value: ${stats['total_value']:.2f}\n"
        report += f"Used Value: ${stats['total_used']:.2f}\n"
        report += f"Remaining Value: ${stats['total_remaining']:.2f}\n\n"
        
        report += f"Status Breakdown:\n"
        report += f"  - Unused: {stats['unused_count']}\n"
        report += f"  - Partially Used: {stats['partially_used_count']}\n"
        report += f"  - Fully Used: {stats['fully_used_count']}\n"
        report += f"  - Expiring Soon (30 days): {stats['expiring_soon_count']}\n\n"
        
        # Show expiring benefits
        expiring = self.get_expiring_benefits(30)
        if expiring:
            report += "⚠️  BENEFITS EXPIRING SOON:\n"
            for benefit in expiring:
                report += f"  - {benefit.benefit_name} ({benefit.card_name})\n"
                report += f"    ${benefit.remaining_value:.2f} remaining, expires in {benefit.days_until_reset} days\n"
        
        report += "="*60
        return report
