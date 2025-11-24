from django.contrib import admin
from .models import Opportunity, Application
from django.utils.html import format_html

# Register your models here.

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    """Opportunity Admin"""
    list_display = ['opportunity_info', 'status', 'start_date']
    list_filter = ['status', 'location', 'created_at']
    search_fields = ['title', 'description', 'organization__username', 'location']
    date_hierarchy = 'start_date'

    def opportunity_info(self, obj):
        """Display opportunity in formatted layout"""
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong>POSITION:</strong> {}<br>'
            '<strong>DEPARTMENT:</strong> {}<br>'
            '<strong>Volunteers Needed:</strong> {}'
            '</div>',
            obj.title,
            obj.location,
            obj.spots_available
        )

    opportunity_info.short_description = 'Opportunity Details'


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Application Admin"""
    list_display = ['volunteer', 'get_opportunity_title', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['volunteer__username', 'opportunity__title']

    def get_opportunity_title(self, obj):
        return obj.opportunity.title
    get_opportunity_title.short_description = 'Opportunity'
    get_opportunity_title.admin_order_field = 'opportunity__title'

