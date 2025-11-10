from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from opportunities.models import Opportunity, Application
from accounts.models import User

def home(request):
    """Home page view."""
    return render(request, 'home.html')

@login_required
def volunteer_dashboard(request):
    """Dashboard for volunteer users."""
    # Get volunteer's applications
    applications = Application.objects.filter(volunteer=request.user).select_related('opportunity', 'opportunity__organization')

    # Get recommended opportunities (active opportunities the volunteer hasn't applied to)
    applied_opportunity_ids = applications.values_list('opportunity_id', flat=True)
    recommended_opportunities = Opportunity.objects.filter(
        status='active'
    ).exclude(id__in=applied_opportunity_ids)[:6]

    # Calculate stats
    pending_applications = applications.filter(status='pending').count()

    context = {
        'applications': applications,
        'recommended_opportunities': recommended_opportunities,
        'volunteer_profile': getattr(request.user, 'volunteer_profile', None),
        'pending_applications': pending_applications,
    }
    return render(request, 'dashboards/volunteer_dashboard.html', context)

@login_required
def organization_dashboard(request):
    """Dashboard for organization users."""
    # Get organization's opportunities
    opportunities = Opportunity.objects.filter(organization=request.user).prefetch_related('applications')

    # Get recent applications to organization's opportunities
    recent_applications = Application.objects.filter(
        opportunity__organization=request.user
    ).select_related('volunteer', 'opportunity').order_by('-applied_at')[:10]

    # Calculate stats
    total_opportunities = opportunities.count()
    active_opportunities = opportunities.filter(status='active').count()
    pending_applications = Application.objects.filter(
        opportunity__organization=request.user,
        status='pending'
    ).count()

    context = {
        'opportunities': opportunities,
        'recent_applications': recent_applications,
        'total_opportunities': total_opportunities,
        'active_opportunities': active_opportunities,
        'pending_applications': pending_applications,
        'organization_profile': getattr(request.user, 'organization_profile', None),
    }
    return render(request, 'dashboards/organization_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Dashboard for admin users."""
    # Get overall stats
    total_volunteers = User.objects.filter(user_type='volunteer').count()
    total_organizations = User.objects.filter(user_type='organization').count()
    total_opportunities = Opportunity.objects.count()
    total_applications = Application.objects.count()

    # Get recent opportunities
    recent_opportunities = Opportunity.objects.all().select_related('organization')[:10]

    # Get recent applications
    recent_applications = Application.objects.all().select_related('volunteer', 'opportunity')[:10]

    context = {
        'total_volunteers': total_volunteers,
        'total_organizations': total_organizations,
        'total_opportunities': total_opportunities,
        'total_applications': total_applications,
        'recent_opportunities': recent_opportunities,
        'recent_applications': recent_applications,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)
