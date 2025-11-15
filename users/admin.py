from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'phone', 'car_number', 'total_cashback', 'registration_date', 'is_active']
    list_filter = ['is_active', 'registration_date']
    search_fields = ['telegram_id', 'phone', 'car_number']
    readonly_fields = ['created_at', 'updated_at']

