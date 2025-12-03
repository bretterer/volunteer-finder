from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model

from opportunities.models import Opportunity, Application


def get_weekly_report_context():
    """
    Build a context dict for the weekly admin report email/template.
    """
    now = timezone.now()
    week_ago = now - timedelta(days=7)

    new_opps = Opportunity.objects.filter(created_at__gte=week_ago)
    new_apps = Application.objects.filter(applied_at__gte=week_ago)

    User = get_user_model()
    new_users = User.objects.filter(date_joined__gte=week_ago)

    context = {
        "week_start": week_ago,
        "week_end": now,
        "new_opps_count": new_opps.count(),
        "new_apps_count": new_apps.count(),
        "new_users_count": new_users.count(),

        "active_opps": Opportunity.objects.filter(status="active").count(),
        "filled_opps": Opportunity.objects.filter(status="filled").count(),
        "expired_opps": Opportunity.objects.filter(status="expired").count(),

        # limit to 5 to keep the email manageable
        "new_opps": new_opps.order_by("-created_at")[:5],
    }

    return context
