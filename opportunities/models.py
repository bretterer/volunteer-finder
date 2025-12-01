from django.db import models
from accounts.models import User

# Create your models here.

class Opportunity(models.Model):
    """
    Volunteer opportunity posted by organizations.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('filled', 'Filled'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )

    organization = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opportunities')
    title = models.CharField(max_length=255)
    description = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)  # List of required skills
    location = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    hours_required = models.IntegerField(help_text="Total hours needed")
    spots_available = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_filename = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'opportunities'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.organization.username}"

    @property
    def accepted_applications_count(self):
        """Count of accepted applications for this opportunity."""
        return self.applications.filter(status='accepted').count()

    @property
    def active_applications_count(self):
        """Count of active applications (pending or accepted, excluding withdrawn/rejected)."""
        return self.applications.filter(status__in=['pending', 'accepted']).count()

    @property
    def is_filled(self):
        """Check if all spots have been filled."""
        return self.accepted_applications_count >= self.spots_available

    def check_and_update_status(self):
        """
        Check if the opportunity should be automatically closed.
        Sets status to 'filled' if all positions are filled.
        Returns True if status was changed, False otherwise.
        """
        from django.utils import timezone

        if self.status != 'active':
            return False

        # Check if all spots are filled
        if self.is_filled:
            self.status = 'filled'
            self.save(update_fields=['status', 'updated_at'])
            return True

        # Check if end date has passed
        if self.end_date and self.end_date < timezone.now().date():
            self.status = 'expired'
            self.save(update_fields=['status', 'updated_at'])
            return True

        return False


class Application(models.Model):
    """
    Volunteer application for an opportunity.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='applications')
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    message = models.TextField(blank=True, null=True, help_text="Cover letter or message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'applications'
        ordering = ['-applied_at']
        unique_together = ['opportunity', 'volunteer']  # One application per volunteer per opportunity

    def __str__(self):
        return f"{self.volunteer.username} -> {self.opportunity.title}"
