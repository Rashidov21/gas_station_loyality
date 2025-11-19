from django.db import models
from django.utils import timezone
from users.models import User


class Check(models.Model):
    """Fiscal check model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='checks', help_text="User who submitted this check")
    fiskal_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="Unique fiscal check ID (RRN/FISKAL_NO)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Check amount")
    datetime = models.DateTimeField(help_text="Date and time of the check")
    source_url = models.URLField(max_length=500, help_text="URL extracted from QR code")
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Cashback earned for this check")
    
    # Raw data from API (optional, for debugging/audit)
    raw_data = models.JSONField(default=dict, blank=True, help_text="Raw data fetched from fiscal check API")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'checks'
        ordering = ['-created_at']
        verbose_name = 'Check'
        verbose_name_plural = 'Checks'
        indexes = [
            models.Index(fields=['fiskal_id']),
            models.Index(fields=['user', 'datetime']),
        ]

    def __str__(self):
        return f"Check {self.fiskal_id} - {self.amount} - User {self.user.telegram_id}"


class Visit(models.Model):
    """Visit model linking user and check"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits', help_text="User who made this visit")
    check = models.OneToOneField(Check, on_delete=models.CASCADE, related_name='visit', help_text="Associated fiscal check")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visits'
        ordering = ['-created_at']
        verbose_name = 'Visit'
        verbose_name_plural = 'Visits'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Visit by User {self.user.telegram_id} - {self.check.amount}"



