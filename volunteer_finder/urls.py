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
from core.views import home, volunteer_dashboard, organization_dashboard, admin_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('opportunities/', include('opportunities.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/volunteer/', volunteer_dashboard, name='volunteer_dashboard'),
    path('dashboard/organization/', organization_dashboard, name='organization_dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('', home, name='home'),
]
