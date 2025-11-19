from decimal import Decimal
from .models import CashbackRule


def calculate_cashback(check_amount):
    """
    Calculate cashback based on active rules.
    Returns the cashback amount.
    """
    if check_amount <= 0:
        return Decimal('0.00')
    
    # Get active rules ordered by priority (highest first)
    active_rules = CashbackRule.objects.filter(is_active=True).order_by('-priority', '-threshold')
    
    cashback_amount = Decimal('0.00')
    
    for rule in active_rules:
        # Skip if check amount is below threshold
        if check_amount < rule.threshold:
            continue
        
        if rule.rule_type == 'fixed':
            cashback_amount += rule.cash_amount
            break  # Fixed amount is usually applied once
        
        elif rule.rule_type == 'percentage':
            percentage_cashback = (check_amount * rule.percentage) / Decimal('100.00')
            cashback_amount += percentage_cashback
            break  # Usually one percentage rule applies
        
        elif rule.rule_type == 'tiered':
            # For tiered, you might want to calculate based on the amount above threshold
            amount_above_threshold = check_amount - rule.threshold
            if rule.cash_amount > 0:
                cashback_amount += rule.cash_amount
            elif rule.percentage > 0:
                tiered_cashback = (amount_above_threshold * rule.percentage) / Decimal('100.00')
                cashback_amount += tiered_cashback
    
    return cashback_amount.quantize(Decimal('0.01'))


