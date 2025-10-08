from django.contrib import admin
from .models import MatchScore

# Register your models here.

@admin.register(MatchScore)
class MatchScoreAdmin(admin.ModelAdmin):
    """Match Score Admin"""
    list_display = ['volunteer', 'opportunity', 'score', 'skill_match', 'availability_match', 'interest_match', 'calculated_at']
    list_filter = ['calculated_at']
    search_fields = ['volunteer__username', 'opportunity__title']
    ordering = ['-score']
