from django.contrib import admin
from .models import Opportunity, Application

# Register your models here.

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    """Opportunity Admin"""
    list_display = ['title', 'organization', 'location', 'start_date', 'status', 'spots_available']
    list_filter = ['status', 'start_date']
    search_fields = ['title', 'description', 'organization__username']
    date_hierarchy = 'start_date'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Application Admin"""
    list_display = ['volunteer', 'opportunity', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['volunteer__username', 'opportunity__title']
