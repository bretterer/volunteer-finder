"""
Recalculate grades based on actual scores.
Usage: python manage.py fix_grades
"""

from django.core.management.base import BaseCommand
from resumes.models import ResumeScore


class Command(BaseCommand):
    help = 'Recalculate grades for all resume scores based on actual score values'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            'updated': 0,
            'unchanged': 0,
            'errors': 0
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be saved\n'))

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🎓 RECALCULATING GRADES'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Get all scores
        scores = ResumeScore.objects.all()
        total = scores.count()

        self.stdout.write(f"Processing {total} scores...\n")

        for i, score in enumerate(scores, 1):
            if i % 500 == 0:
                self.stdout.write(f"Progress: {i}/{total}...")

            self.fix_single_grade(score, dry_run)

        self.print_summary()

    def calculate_grade(self, score):
        """
        Calculate letter grade based on score.

        Args:
            score: Numeric score (0-100)

        Returns:
            str: Letter grade
        """
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 65:
            return 'D'
        else:
            return 'F'

    def fix_single_grade(self, score_obj, dry_run):
        """
        Fix grade for a single score.

        Args:
            score_obj: ResumeScore instance
            dry_run: Whether to save changes
        """
        try:
            # Calculate correct grade
            correct_grade = self.calculate_grade(score_obj.overall_score)

            # Check if it needs updating
            if score_obj.grade == correct_grade:
                self.stats['unchanged'] += 1
                return

            # Show what will change
            if self.stats['updated'] < 10:  # Only show first 10
                self.stdout.write(
                    f"  ID {score_obj.id}: Score {score_obj.overall_score} "
                    f"→ Grade '{score_obj.grade}' → '{correct_grade}'"
                )

            if dry_run:
                self.stats['updated'] += 1
                return

            # Update the grade
            score_obj.grade = correct_grade
            score_obj.save(update_fields=['grade'])

            self.stats['updated'] += 1

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error for score ID {score_obj.id}: {e}"))
            self.stats['errors'] += 1

    def print_summary(self):
        """Print statistics."""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 GRADE FIX SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(
            f"\n✓ Updated: {self.stats['updated']}"
            f"\n⏭️  Unchanged: {self.stats['unchanged']}"
            f"\n✗ Errors: {self.stats['errors']}"
        )
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))