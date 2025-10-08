from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    """
    Extended user model to support multiple user types.
    Types: Volunteer (Student), Organization, Admin
    """
    USER_TYPE_CHOICES = (
        ('volunteer', 'Volunteer'),
        ('organization', 'Organization'),
        ('admin', 'Admin'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class VolunteerProfile(models.Model):
    """
    Profile for volunteer users (students).
    Stores skills, availability, and preferences.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='volunteer_profile')
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True)  # List of skills
    availability = models.JSONField(default=dict, blank=True)  # Availability schedule
    interests = models.JSONField(default=list, blank=True)  # Areas of interest
    hours_completed = models.IntegerField(default=0)

    class Meta:
        db_table = 'volunteer_profiles'

    def __str__(self):
        return f"Volunteer Profile: {self.user.username}"


class OrganizationProfile(models.Model):
    """
    Profile for organization users.
    Stores organization details and contact information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organization_profile')
    organization_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact_person = models.CharField(max_length=255)
    verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'organization_profiles'

    def __str__(self):
        return f"Organization: {self.organization_name}"
