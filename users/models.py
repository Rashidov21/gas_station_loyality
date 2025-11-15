from django.db import models
from django.utils import timezone


class User(models.Model):
    """Customer model for loyalty system"""
    telegram_id = models.BigIntegerField(unique=True, db_index=True, help_text="Telegram user ID")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Customer phone number")
    car_name = models.CharField(max_length=100, blank=True, null=True, help_text="Car brand/model")
    car_number = models.CharField(max_length=20, blank=True, null=True, help_text="Car license plate number")
    registration_date = models.DateTimeField(default=timezone.now, help_text="When user registered in the system")
    is_active = models.BooleanField(default=True, help_text="Whether user is active")
    total_cashback = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total accumulated cashback")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"User {self.telegram_id} ({self.phone or 'No phone'})"

