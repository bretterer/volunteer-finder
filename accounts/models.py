import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

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
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def name(self):
        """Return full name or username as fallback"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

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


class PasswordResetToken(models.Model):
    """
    Stores password reset tokens for secure password recovery.
    Tokens expire after 1 hour.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'password_reset_tokens'

    def __str__(self):
        return f"Password Reset Token for {self.user.username}"

    @classmethod
    def create_for_user(cls, user):
        """Create a new password reset token for a user."""
        # Invalidate any existing unused tokens for this user
        cls.objects.filter(user=user, used=False).update(used=True)
        # Generate a secure random token
        token = secrets.token_urlsafe(48)
        return cls.objects.create(user=user, token=token)

    def is_valid(self):
        """Check if the token is still valid (not used and not expired)."""
        if self.used:
            return False
        # Token expires after 1 hour
        expiry_time = self.created_at + timedelta(hours=1)
        return timezone.now() < expiry_time


class EmailVerificationToken(models.Model):
    """
    Stores email verification tokens for new account verification.
    Tokens expire after 24 hours.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_verification_tokens'

    def __str__(self):
        return f"Email Verification Token for {self.user.username}"

    @classmethod
    def create_for_user(cls, user):
        """Create a new email verification token for a user."""
        # Invalidate any existing unused tokens for this user
        cls.objects.filter(user=user, used=False).update(used=True)
        # Generate a secure random token
        token = secrets.token_urlsafe(48)
        return cls.objects.create(user=user, token=token)

    def is_valid(self):
        """Check if the token is still valid (not used and not expired)."""
        if self.used:
            return False
        # Token expires after 24 hours
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() < expiry_time
