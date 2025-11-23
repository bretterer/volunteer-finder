"""
Score all unscored resumes against all opportunities.
Usage: python manage.py score_new_resumes
"""

from django.core.management.base import BaseCommand
from resumes.services import ResumeScoringService
from resumes.models import Resume
from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Score all unscored resume-opportunity pairs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be scored without actually scoring'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE\n'))

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 SCORING NEW RESUMES'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Count what needs scoring
        resumes = Resume.objects.filter(processed=True)
        opportunities = Opportunity.objects.filter(status='active')

        self.stdout.write(f"📄 Total Resumes: {resumes.count()}")
        self.stdout.write(f"💼 Active Opportunities: {opportunities.count()}\n")

        if dry_run:
            # Count unscored pairs
            from resumes.models import ResumeScore
            total_possible = resumes.count() * opportunities.count()
            total_scored = ResumeScore.objects.count()
            unscored = total_possible - total_scored

            self.stdout.write(f"✅ Already Scored: {total_scored}")
            self.stdout.write(f"⏳ Need Scoring: {unscored}")
            self.stdout.write(f"📊 Total Possible: {total_possible}\n")

            self.stdout.write(self.style.SUCCESS('[DRY RUN] No scores created'))
            return

        # Actually score
        try:
            service = ResumeScoringService()
            stats = service.score_all_unscored_resumes()

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            self.stdout.write(self.style.SUCCESS('✅ SCORING COMPLETE'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(f"\n📄 Resumes Processed: {stats['resumes_processed']}")
            self.stdout.write(f"✅ Scores Created: {stats['scores_created']}")
            self.stdout.write(f"❌ Errors: {stats['errors']}\n")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
            raise