from django.db import models
from django.core.validators import FileExtensionValidator
from accounts.models import User
from opportunities.models import Opportunity
from opportunities.models import Application

class Resume(models.Model):
    """
    Volunteers upload resume.
    Stores file path for extraction of text to allow AI scoring
    """
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='resume',
                             help_text='Volunteer who uploaded the resume')

    # File storage
    file = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'docx', 'txt'])],
        help_text="Resume file (PDF, DOCX, or TXT)"
    )

    # Text extraction for AI scoring
    extracted_text = models.TextField(
        blank=True,
        help_text="Resume text extracted from file"
    )

    # General information extracted from resume
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(blank=True, null=True, max_length=20)

    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(
        default=False,
        help_text="Has text been extracted from file?")

    class Meta:
        db_table = 'resumes'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"

    def file_extension(self):
        return self.file.name.split('.')[-1].lower()

class ResumeScore(models.Model):
    """
    AI generated scoring for resumes to opportunities.
    Separate from MatchScore for maintenance flexibility
    """
    grade_choices = (
        ('A+', 'A+ (100-95)'),
        ('A', 'A (94-90)'),
        ('B+', 'B+ (89-85)'),
        ('B', 'B (84-80)'),
        ('C+', 'C+ (79-75)'),
        ('C', 'C (74-70)'),
        ('D', 'D (69-65)'),
        ('F', 'F (64-0)'),
    )

    recommendation_choices = (
        ('highly_recommended', 'Highly Recommended'),
        ('recommended', 'Recommended'),
        ('consider', 'Consider'),
        ('not_recommended', 'Not Recommended'),
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name='scores'
    )

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='resume_scores'
    )

    # Overall score (0-100)
    overall_score = models.IntegerField(
        help_text="Overall match score (0-100)"
    )

    # General Details
    skills_match = models.IntegerField(default=0, help_text="Skills alignment (0-100)")
    experience_match = models.IntegerField(default=0, help_text="Experience match (0-100)")
    education_match = models.IntegerField(default=0, help_text="Education match (0-100)")

    # Qualitative assessment with recommendation
    grade = models.CharField(max_length=3, choices=grade_choices)
    recommendation = models.CharField(max_length=20, choices=recommendation_choices)
    key_strength = models.TextField(help_text="Main Strength of Candidate")
    concerns = models.TextField(blank=True, help_text="Potential concerns or gaps")

    # Metadata
    scored_at = models.DateTimeField(auto_now_add=True)
    scored_by_model = models.CharField(
        max_length=50,
        default='gpt-4o-mini',
        help_text="AI Model used for Scoring"
    )

    class Meta:
        db_table = 'resume_scores'
        ordering = ['-overall_score']
        unique_together = ['resume', 'opportunity']
        indexes = [
            models.Index(fields=['opportunity', '-overall_score']),
            models.Index(fields=['-overall_score']),
        ]
    def __str__(self):
        return f"{self.resume.user.username} → {self.opportunity.title}: {self.overall_score}/100"

    def passes_threshold(self):
        return self.overall_score >= 65

    @classmethod
    def get_top_candidate(cls, opportunity, limit=10, min_score=65, applied_only=True):
        queryset = cls.objects.filter(opportunity=opportunity,
                                      overall_score__gte=min_score,
                                      ).select_related('resume__user', 'opportunity')
        if applied_only:
            applied_user_ids = Application.objects.filter(
                opportunity=opportunity,
            ).values_list('volunteer_id', flat=True)

            queryset = queryset.filter(resume__user__id__in=applied_user_ids)
        return queryset[:limit]

class ScoringJob(models.Model):
    """
    Track scoring jobs for monitoring and debugging.
    """
    status_choices = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='scoring_jobs')
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    opportunities_to_score = models.IntegerField(default=0)
    opportunities_scored = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'scoring_jobs'
        ordering = ['-started_at']

    def __str__(self):
        return f"Scoring Job {self.id} - {self.status}"




