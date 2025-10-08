from django.db import models
from accounts.models import User

# Create your models here.

class Notification(models.Model):
    """
    Notification model for alerts and emails to users.
    """
    NOTIFICATION_TYPES = (
        ('application_received', 'Application Received'),
        ('application_accepted', 'Application Accepted'),
        ('application_rejected', 'Application Rejected'),
        ('new_opportunity', 'New Opportunity Match'),
        ('reminder', 'Reminder'),
        ('system', 'System Notification'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username}"
