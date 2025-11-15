from django.contrib import admin
from .models import Check, Visit


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ['fiskal_id', 'user', 'amount', 'cashback_amount', 'datetime', 'created_at']
    list_filter = ['created_at', 'datetime']
    search_fields = ['fiskal_id', 'user__telegram_id', 'user__phone']
    readonly_fields = ['created_at', 'updated_at', 'raw_data']
    date_hierarchy = 'created_at'


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['user', 'check', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__telegram_id', 'user__phone']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

