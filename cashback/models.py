from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User


class CashbackRule(models.Model):
    """Rules for calculating cashback"""
    
    RULE_TYPES = [
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ('tiered', 'Tiered (Amount-based)'),
    ]
    
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, help_text="Type of cashback rule")
    name = models.CharField(max_length=100, help_text="Rule name/description")
    
    # For tiered rules: minimum threshold amount
    threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Minimum check amount to apply this rule"
    )
    
    # For fixed amount
    cash_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Fixed cashback amount (if rule_type is 'fixed')"
    )
    
    # For percentage
    percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Cashback percentage (if rule_type is 'percentage')"
    )
    
    is_active = models.BooleanField(default=True, help_text="Whether this rule is active")
    priority = models.IntegerField(default=0, help_text="Higher priority rules are checked first")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cashback_rules'
        ordering = ['-priority', '-threshold']
        verbose_name = 'Cashback Rule'
        verbose_name_plural = 'Cashback Rules'

    def __str__(self):
        if self.rule_type == 'fixed':
            return f"{self.name}: {self.cash_amount} fixed"
        elif self.rule_type == 'percentage':
            return f"{self.name}: {self.percentage}%"
        else:
            return f"{self.name}: {self.threshold}+ = {self.cash_amount or self.percentage}%"


class Settings(models.Model):
    """System-wide settings"""
    key = models.CharField(max_length=100, unique=True, help_text="Setting key")
    value = models.TextField(help_text="Setting value")
    description = models.TextField(blank=True, help_text="Description of this setting")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'settings'
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

    def __str__(self):
        return f"{self.key}: {self.value}"

