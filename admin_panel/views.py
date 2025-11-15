from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from users.models import User
from bot.models import Check, Visit
from cashback.models import CashbackRule


@staff_member_required
def dashboard(request):
    """Admin dashboard with statistics"""
    
    # Today's stats
    today = timezone.now().date()
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_checks = Check.objects.filter(created_at__gte=today_start)
    today_visits = Visit.objects.filter(created_at__gte=today_start)
    today_revenue = today_checks.aggregate(total=Sum('amount'))['total'] or 0
    today_cashback = today_checks.aggregate(total=Sum('cashback_amount'))['total'] or 0
    
    # Total stats
    total_users = User.objects.count()
    total_checks = Check.objects.count()
    total_cashback = Check.objects.aggregate(total=Sum('cashback_amount'))['total'] or 0
    total_revenue = Check.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent checks
    recent_checks = Check.objects.select_related('user').order_by('-created_at')[:10]
    
    # Active rules
    active_rules = CashbackRule.objects.filter(is_active=True).order_by('-priority')
    
    context = {
        'today_checks_count': today_checks.count(),
        'today_visits_count': today_visits.count(),
        'today_revenue': today_revenue,
        'today_cashback': today_cashback,
        'total_users': total_users,
        'total_checks': total_checks,
        'total_cashback': total_cashback,
        'total_revenue': total_revenue,
        'recent_checks': recent_checks,
        'active_rules': active_rules,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

