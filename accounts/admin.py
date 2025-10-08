from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, VolunteerProfile, OrganizationProfile

# Register your models here.

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ['username', 'email', 'user_type', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone')}),
    )


@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    """Volunteer Profile Admin"""
    list_display = ['user', 'hours_completed']
    search_fields = ['user__username', 'user__email']


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    """Organization Profile Admin"""
    list_display = ['organization_name', 'contact_person', 'verified', 'user']
    list_filter = ['verified']
    search_fields = ['organization_name', 'contact_person', 'user__username']
