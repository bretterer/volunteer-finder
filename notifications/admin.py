from django.contrib import admin
from .models import Notification

# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification Admin"""
    list_display = ['user', 'notification_type', 'title', 'is_read', 'email_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'email_sent', 'created_at']
    search_fields = ['user__username', 'title', 'message']
