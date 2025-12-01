from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
import csv
import json

from opportunities.models import Opportunity, Application
from accounts.models import User, VolunteerProfile, OrganizationProfile


def is_admin(user):
    """Check if user is an admin."""
    return user.is_authenticated and user.user_type == 'admin'

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

    # Get recent applications to organization's opportunities (excluding withdrawn/rejected)
    recent_applications = Application.objects.filter(
        opportunity__organization=request.user,
        status__in=['pending', 'accepted']
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


@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    """Main reports page for admins."""
    return render(request, 'reports/index.html')


@login_required
@user_passes_test(is_admin)
def volunteer_activity_report(request):
    """Report on volunteer activity and engagement."""
    # Date range filtering
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Total volunteers
    total_volunteers = User.objects.filter(user_type='volunteer').count()
    new_volunteers = User.objects.filter(
        user_type='volunteer',
        date_joined__gte=start_date
    ).count()

    # Application statistics
    total_applications = Application.objects.filter(applied_at__gte=start_date).count()
    applications_by_status = Application.objects.filter(
        applied_at__gte=start_date
    ).values('status').annotate(count=Count('id'))

    # Most active volunteers (by application count)
    active_volunteers = User.objects.filter(
        user_type='volunteer',
        applications__applied_at__gte=start_date
    ).annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:10]

    # Volunteers by registration date (trend)
    volunteer_trend = User.objects.filter(
        user_type='volunteer',
        date_joined__gte=start_date
    ).annotate(
        week=TruncWeek('date_joined')
    ).values('week').annotate(count=Count('id')).order_by('week')

    # Application trend over time
    application_trend = Application.objects.filter(
        applied_at__gte=start_date
    ).annotate(
        week=TruncWeek('applied_at')
    ).values('week').annotate(count=Count('id')).order_by('week')

    # Acceptance rate
    accepted_count = Application.objects.filter(
        applied_at__gte=start_date,
        status='accepted'
    ).count()
    acceptance_rate = (accepted_count / total_applications * 100) if total_applications > 0 else 0

    context = {
        'days': days,
        'total_volunteers': total_volunteers,
        'new_volunteers': new_volunteers,
        'total_applications': total_applications,
        'applications_by_status': list(applications_by_status),
        'active_volunteers': active_volunteers,
        'volunteer_trend': list(volunteer_trend),
        'application_trend': list(application_trend),
        'acceptance_rate': round(acceptance_rate, 1),
        'accepted_count': accepted_count,
    }
    return render(request, 'reports/volunteer_activity.html', context)


@login_required
@user_passes_test(is_admin)
def opportunity_report(request):
    """Report on opportunity activity and status."""
    # Date range filtering
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Total opportunities
    total_opportunities = Opportunity.objects.count()
    new_opportunities = Opportunity.objects.filter(created_at__gte=start_date).count()

    # Opportunities by status
    opportunities_by_status = Opportunity.objects.values('status').annotate(
        count=Count('id')
    )

    # Most popular opportunities (by application count)
    popular_opportunities = Opportunity.objects.annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:10]

    # Opportunities by location
    opportunities_by_location = Opportunity.objects.values('location').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Opportunity creation trend
    opportunity_trend = Opportunity.objects.filter(
        created_at__gte=start_date
    ).annotate(
        week=TruncWeek('created_at')
    ).values('week').annotate(count=Count('id')).order_by('week')

    # Average applications per opportunity
    avg_applications = Opportunity.objects.annotate(
        app_count=Count('applications')
    ).aggregate(avg=Avg('app_count'))['avg'] or 0

    # Fill rate (filled opportunities / total)
    filled_count = Opportunity.objects.filter(status='filled').count()
    fill_rate = (filled_count / total_opportunities * 100) if total_opportunities > 0 else 0

    # Hours statistics
    total_hours = sum(opp.hours_required for opp in Opportunity.objects.filter(status__in=['active', 'filled']))

    context = {
        'days': days,
        'total_opportunities': total_opportunities,
        'new_opportunities': new_opportunities,
        'opportunities_by_status': list(opportunities_by_status),
        'popular_opportunities': popular_opportunities,
        'opportunities_by_location': list(opportunities_by_location),
        'opportunity_trend': list(opportunity_trend),
        'avg_applications': round(avg_applications, 1),
        'fill_rate': round(fill_rate, 1),
        'filled_count': filled_count,
        'total_hours': total_hours,
    }
    return render(request, 'reports/opportunity_report.html', context)


@login_required
@user_passes_test(is_admin)
def organization_report(request):
    """Report on organization activity."""
    # Date range filtering
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Total organizations
    total_organizations = User.objects.filter(user_type='organization').count()
    new_organizations = User.objects.filter(
        user_type='organization',
        date_joined__gte=start_date
    ).count()

    # Verified vs unverified
    verified_count = OrganizationProfile.objects.filter(verified=True).count()

    # Most active organizations (by opportunities posted)
    active_organizations = User.objects.filter(
        user_type='organization'
    ).annotate(
        opportunity_count=Count('opportunities'),
        application_count=Count('opportunities__applications')
    ).order_by('-opportunity_count')[:10]

    # Organizations by opportunity count distribution
    org_with_opportunities = User.objects.filter(
        user_type='organization',
        opportunities__isnull=False
    ).distinct().count()

    context = {
        'days': days,
        'total_organizations': total_organizations,
        'new_organizations': new_organizations,
        'verified_count': verified_count,
        'active_organizations': active_organizations,
        'org_with_opportunities': org_with_opportunities,
    }
    return render(request, 'reports/organization_report.html', context)


@login_required
@user_passes_test(is_admin)
def export_volunteer_report_csv(request):
    """Export volunteer activity report as CSV."""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="volunteer_report_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Volunteer Activity Report', f'Last {days} days'])
    writer.writerow([])

    # Summary stats
    writer.writerow(['Summary Statistics'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Volunteers', User.objects.filter(user_type='volunteer').count()])
    writer.writerow(['New Volunteers', User.objects.filter(user_type='volunteer', date_joined__gte=start_date).count()])
    writer.writerow(['Total Applications', Application.objects.filter(applied_at__gte=start_date).count()])
    writer.writerow([])

    # Active volunteers
    writer.writerow(['Most Active Volunteers'])
    writer.writerow(['Username', 'Email', 'Applications', 'Joined Date'])

    active_volunteers = User.objects.filter(
        user_type='volunteer',
        applications__applied_at__gte=start_date
    ).annotate(
        application_count=Count('applications')
    ).order_by('-application_count')[:20]

    for volunteer in active_volunteers:
        writer.writerow([
            volunteer.username,
            volunteer.email,
            volunteer.application_count,
            volunteer.date_joined.strftime('%Y-%m-%d')
        ])

    return response


@login_required
@user_passes_test(is_admin)
def export_opportunity_report_csv(request):
    """Export opportunity report as CSV."""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="opportunity_report_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Opportunity Report', f'Last {days} days'])
    writer.writerow([])

    # Summary stats
    writer.writerow(['Summary Statistics'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Opportunities', Opportunity.objects.count()])
    writer.writerow(['New Opportunities', Opportunity.objects.filter(created_at__gte=start_date).count()])
    writer.writerow(['Active Opportunities', Opportunity.objects.filter(status='active').count()])
    writer.writerow(['Filled Opportunities', Opportunity.objects.filter(status='filled').count()])
    writer.writerow([])

    # All opportunities
    writer.writerow(['Opportunities Detail'])
    writer.writerow(['Title', 'Organization', 'Location', 'Status', 'Applications', 'Spots', 'Created Date'])

    opportunities = Opportunity.objects.annotate(
        application_count=Count('applications')
    ).select_related('organization').order_by('-created_at')

    for opp in opportunities:
        writer.writerow([
            opp.title,
            opp.organization.username,
            opp.location,
            opp.status,
            opp.application_count,
            opp.spots_available,
            opp.created_at.strftime('%Y-%m-%d')
        ])

    return response


@login_required
@user_passes_test(is_admin)
def export_organization_report_csv(request):
    """Export organization report as CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="organization_report_{timezone.now().date()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Organization Report'])
    writer.writerow([])

    # Summary stats
    writer.writerow(['Summary Statistics'])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Organizations', User.objects.filter(user_type='organization').count()])
    writer.writerow(['Verified Organizations', OrganizationProfile.objects.filter(verified=True).count()])
    writer.writerow([])

    # Organization details
    writer.writerow(['Organizations Detail'])
    writer.writerow(['Username', 'Organization Name', 'Verified', 'Opportunities Posted', 'Total Applications', 'Joined Date'])

    organizations = User.objects.filter(
        user_type='organization'
    ).annotate(
        opportunity_count=Count('opportunities'),
        application_count=Count('opportunities__applications')
    ).select_related('organization_profile').order_by('-opportunity_count')

    for org in organizations:
        profile = getattr(org, 'organization_profile', None)
        writer.writerow([
            org.username,
            profile.organization_name if profile else 'N/A',
            'Yes' if profile and profile.verified else 'No',
            org.opportunity_count,
            org.application_count,
            org.date_joined.strftime('%Y-%m-%d')
        ])

    return response
