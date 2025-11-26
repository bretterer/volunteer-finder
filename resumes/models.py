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

    def __str__(self):
        return f"{self.user.username} - {self.original_filename}"

    def save(self, *args, **kwargs):
        # Auto-calculate file_size from uploaded file
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except:
                self.file_size = 0

        # Auto-set original_filename from uploaded file
        if self.file and not self.original_filename:
            try:
                self.original_filename = self.file.name.split('/')[-1]
            except:
                self.original_filename = "unknown"

        # Check if this is a new resume (no id yet)
        is_new = self.pk is None

        # FIRST save to ensure file is written to disk
        super().save(*args, **kwargs)

        # THEN extract text if not already extracted
        if self.file and not self.extracted_text:
            extracted = self._extract_text_from_file()
            if extracted:
                self.extracted_text = extracted
                # Save again with extracted text (avoid triggering signals)
                Resume.objects.filter(pk=self.pk).update(extracted_text=extracted)

                # Trigger scoring for new resumes after text is extracted
                if is_new:
                    self._trigger_scoring()

    def _extract_text_from_file(self):
        """Extract text content from uploaded resume file"""
        try:
            import os
            file_path = self.file.path

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return ""

            file_ext = file_path.lower().split('.')[-1]

            if file_ext == 'txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            elif file_ext == 'docx':
                from docx import Document
                doc = Document(file_path)
                text = []
                for paragraph in doc.paragraphs:
                    text.append(paragraph.text)
                extracted = '\n'.join(text)
                print(f"✅ Extracted {len(extracted)} characters from DOCX")
                return extracted

            elif file_ext == 'pdf':
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                text = []
                for page in reader.pages:
                    text.append(page.extract_text() or '')
                extracted = '\n'.join(text)
                print(f"✅ Extracted {len(extracted)} characters from PDF")
                return extracted

            else:
                print(f"⚠️ Unsupported file type: {file_ext}")
                return ""

        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return ""

    def _trigger_scoring(self):
        """Trigger background scoring for this resume"""
        import threading

        def score_async(resume_id):
            import time
            time.sleep(1)

            try:
                from resumes.models import Resume, ResumeScore
                from opportunities.models import Opportunity
                from resumes.services import ResumeScoringService

                resume = Resume.objects.get(id=resume_id)

                if not resume.extracted_text:
                    print(f"⚠️ No text to score for resume {resume_id}")
                    return

                print(f"🤖 Scoring resume: {resume.original_filename}")

                service = ResumeScoringService()
                opportunities = Opportunity.objects.filter(status='active')

                count = 0
                for opp in opportunities:
                    if not ResumeScore.objects.filter(resume=resume, opportunity=opp).exists():
                        try:
                            service.score_resume_for_opportunity(resume, opp)
                            count += 1
                        except Exception as e:
                            print(f"  ❌ Error: {e}")

                print(f"✅ Scored resume against {count} opportunities")

            except Exception as e:
                print(f"❌ Scoring error: {e}")

        thread = threading.Thread(target=score_async, args=(self.pk,))
        thread.daemon = True
        thread.start()


class ResumeScore(models.Model):
    """
    AI-generated matching score between a resume and opportunity.
    """
    ACCEPTANCE_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('waitlist', 'Waitlisted'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='scores')
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='resume_scores')

    # Scores (0-100)
    overall_score = models.IntegerField(default=0)
    skills_score = models.IntegerField(default=0)
    experience_score = models.IntegerField(default=0)
    education_score = models.IntegerField(default=0)

    # Alternative field names used by scoring service
    skills_match = models.IntegerField(default=0)
    experience_match = models.IntegerField(default=0)
    education_match = models.IntegerField(default=0)

    # Letter grade
    grade = models.CharField(max_length=2, blank=True)

    # AI explanation
    recommendation = models.TextField(blank=True)
    key_strength = models.TextField(blank=True)
    concerns = models.TextField(blank=True)

    # Model tracking
    scored_by_model = models.CharField(max_length=100, blank=True)

    # Acceptance tracking
    acceptance_status = models.CharField(
        max_length=20,
        choices=ACCEPTANCE_STATUS_CHOICES,
        default='pending'
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_scores'
    )

    scored_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resume_scores'
        unique_together = ['resume', 'opportunity']
        ordering = ['-overall_score']

    def __str__(self):
        return f"{self.resume.user.username} → {self.opportunity.title}: {self.overall_score}/100"

    def save(self, *args, **kwargs):
        # Sync alternative field names
        if self.skills_match and not self.skills_score:
            self.skills_score = self.skills_match
        if self.experience_match and not self.experience_score:
            self.experience_score = self.experience_match
        if self.education_match and not self.education_score:
            self.education_score = self.education_match

        # Auto-calculate grade based on overall_score
        if self.overall_score >= 98:
            self.grade = 'A+'
        elif self.overall_score >= 94:
            self.grade = 'A'
        elif self.overall_score >= 90:
            self.grade = 'A-'
        elif self.overall_score >= 85:
            self.grade = 'B+'
        elif self.overall_score >= 80:
            self.grade = 'B'
        elif self.overall_score >= 74:
            self.grade = 'B-'
        elif self.overall_score >= 68:
            self.grade = 'C+'
        elif self.overall_score >= 62:
            self.grade = 'C'
        elif self.overall_score >= 56:
            self.grade = 'C-'
        elif self.overall_score >= 50:
            self.grade = 'D+'
        elif self.overall_score >= 44:
            self.grade = 'D'
        elif self.overall_score >= 40:
            self.grade = 'D-'
        else:
            self.grade = 'F'

        super().save(*args, **kwargs)


class ScoringJob(models.Model):
    """
    Track background scoring jobs.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, null=True, blank=True)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'scoring_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"ScoringJob {self.id}: {self.status}"