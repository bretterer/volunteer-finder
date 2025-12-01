"""
URL configuration for volunteer_finder project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    home, volunteer_dashboard, organization_dashboard, admin_dashboard,
    admin_reports, volunteer_activity_report, opportunity_report, organization_report,
    export_volunteer_report_csv, export_opportunity_report_csv, export_organization_report_csv,
    send_test_email
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('opportunities/', include('opportunities.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/volunteer/', volunteer_dashboard, name='volunteer_dashboard'),
    path('dashboard/organization/', organization_dashboard, name='organization_dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/test-email/', send_test_email, name='send_test_email'),
    # Admin Reports
    path('dashboard/admin/reports/', admin_reports, name='admin_reports'),
    path('dashboard/admin/reports/volunteers/', volunteer_activity_report, name='volunteer_activity_report'),
    path('dashboard/admin/reports/opportunities/', opportunity_report, name='opportunity_report'),
    path('dashboard/admin/reports/organizations/', organization_report, name='organization_report'),
    # Report Exports
    path('dashboard/admin/reports/volunteers/export/', export_volunteer_report_csv, name='export_volunteer_report_csv'),
    path('dashboard/admin/reports/opportunities/export/', export_opportunity_report_csv, name='export_opportunity_report_csv'),
    path('dashboard/admin/reports/organizations/export/', export_organization_report_csv, name='export_organization_report_csv'),
    path('', home, name='home'),
    path('resumes/', include('resumes.urls'))
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
