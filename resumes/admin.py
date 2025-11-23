from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from .models import Resume, ResumeScore, ScoringJob
from .admin_views import OpportunityMatchingView


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'original_filename', 'file_type', 'processed', 'uploaded_at']
    list_filter = ['processed', 'uploaded_at']
    search_fields = ['user__name', 'user__email', 'original_filename']
    readonly_fields = ['uploaded_at', 'file_size', 'extracted_text']

    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('File Info', {
            'fields': ('file', 'original_filename', 'file_size', 'uploaded_at')
        }),
        ('Extracted Data', {
            'fields': ('extracted_text', 'email', 'phone', 'processed')
        }),
    )

    def file_type(self, obj):
        ext = obj.file.name.split('.')[-1].upper()
        return ext

    file_type.short_description = 'Type'


@admin.register(ResumeScore)
class ResumeScoreAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'volunteer_name',
        'opportunity_title',
        'colored_score',
        'grade',
        'recommendation',
        'acceptance_status',
        'scored_at'
    ]
    list_filter = ['grade', 'recommendation', 'acceptance_status', 'scored_at', 'scored_by_model']
    search_fields = [
        'resume__user__username',
        'resume__user__email',
        'opportunity__title'
    ]
    readonly_fields = ['scored_at', 'scored_by_model']

    fieldsets = (
        ('Match Info', {
            'fields': ('resume', 'opportunity')
        }),
        ('Scores', {
            'fields': (
                'overall_score',
                'skills_match',
                'experience_match',
                'education_match'
            )
        }),
        ('Assessment', {
            'fields': ('grade', 'recommendation', 'key_strength', 'concerns')
        }),
        ('Metadata', {
            'fields': ('scored_at', 'scored_by_model')
        }),
    )

    def volunteer_name(self, obj):
        return obj.resume.user.username

    volunteer_name.short_description = 'Volunteer'
    volunteer_name.admin_order_field = 'resume__user__username'

    def opportunity_title(self, obj):
        return obj.opportunity.title[:50]

    opportunity_title.short_description = 'Opportunity'
    opportunity_title.admin_order_field = 'opportunity__title'

    def colored_score(self, obj):
        """Display score with color coding"""
        if obj.overall_score >= 85:
            color = 'green'
        elif obj.overall_score >= 70:
            color = 'orange'
        elif obj.overall_score >= 65:
            color = 'blue'
        else:
            color = 'red'

        return format_html(
            '<strong style="color: {};">{}/100</strong>',
            color,
            obj.overall_score
        )

    colored_score.short_description = 'Score'
    colored_score.admin_order_field = 'overall_score'


@admin.register(ScoringJob)
class ScoringJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'resume', 'status', 'progress', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at']

    def progress(self, obj):
        if obj.opportunities_to_score > 0:
            percent = (obj.opportunities_scored / obj.opportunities_to_score) * 100
            return f"{obj.opportunities_scored}/{obj.opportunities_to_score} ({percent:.0f}%)"
        return "0/0"

    progress.short_description = 'Progress'


# ✅ ADD THIS: Proxy model for Matching Dashboard link
class MatchingDashboard(ResumeScore):
    """Proxy model to add Matching Dashboard link to admin."""

    class Meta:
        proxy = True
        verbose_name = "Matching Dashboard"
        verbose_name_plural = "🎯 Matching Dashboard"


@admin.register(MatchingDashboard)
class MatchingDashboardAdmin(admin.ModelAdmin):
    """Fake admin to show dashboard link in sidebar."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """Redirect to matching dashboard."""
        return redirect('/admin/matching/')


# Register custom matching dashboard URL
_original_get_urls = admin.site.__class__.get_urls


def custom_get_urls(self):
    """Add custom matching dashboard URLs to admin."""
    urls = _original_get_urls(self)
    custom_urls = [
        path('matching/', OpportunityMatchingView.as_view(), name='opportunity-matching'),
        path('matching/<int:opportunity_id>/', OpportunityMatchingView.as_view(), name='opportunity-matching'),
    ]
    return custom_urls + urls


# Replace the get_urls method at the class level
admin.site.__class__.get_urls = custom_get_urls