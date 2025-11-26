from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Resume, ResumeScore, ScoringJob


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['user', 'original_filename', 'file_size_display', 'uploaded_at', 'processed']
    list_filter = ['processed', 'uploaded_at']
    search_fields = ['user__username', 'original_filename', 'extracted_text']
    readonly_fields = ['uploaded_at', 'file_size', 'extracted_text_preview']

    fieldsets = (
        ('User Info', {
            'fields': ('user', 'file', 'original_filename')
        }),
        ('Extracted Data', {
            'fields': ('extracted_text_preview', 'email', 'phone'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('file_size', 'uploaded_at', 'processed')
        }),
    )

    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "-"

    file_size_display.short_description = "File Size"

    def extracted_text_preview(self, obj):
        if obj.extracted_text:
            return obj.extracted_text[:500] + "..." if len(obj.extracted_text) > 500 else obj.extracted_text
        return "No text extracted"

    extracted_text_preview.short_description = "Extracted Text Preview"


@admin.register(ResumeScore)
class ResumeScoreAdmin(admin.ModelAdmin):
    list_display = ['resume', 'opportunity', 'overall_score_display', 'grade', 'acceptance_status', 'scored_at']
    list_filter = ['grade', 'acceptance_status', 'scored_at']
    search_fields = ['resume__user__username', 'opportunity__title', 'recommendation']
    readonly_fields = ['scored_at']

    fieldsets = (
        ('Match Info', {
            'fields': ('resume', 'opportunity')
        }),
        ('Scores', {
            'fields': ('overall_score', 'skills_score', 'experience_score', 'education_score', 'grade')
        }),
        ('AI Analysis', {
            'fields': ('recommendation',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('acceptance_status', 'accepted_at', 'accepted_by', 'scored_at')
        }),
    )

    def overall_score_display(self, obj):
        score = obj.overall_score
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}/100</span>', color, score)

    overall_score_display.short_description = "Score"


@admin.register(ScoringJob)
class ScoringJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'resume', 'opportunity', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['resume__user__username', 'opportunity__title']
    readonly_fields = ['created_at', 'completed_at']

    fieldsets = (
        ('Job Info', {
            'fields': ('resume', 'opportunity', 'status')
        }),
        ('Results', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )