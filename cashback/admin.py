from django.contrib import admin
from .models import CashbackRule, Settings


@admin.register(CashbackRule)
class CashbackRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'threshold', 'cash_amount', 'percentage', 'priority', 'is_active']
    list_filter = ['rule_type', 'is_active']
    search_fields = ['name']
    ordering = ['-priority', '-threshold']


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    search_fields = ['key']
    readonly_fields = ['created_at', 'updated_at']

