"""
Score a specific resume against all opportunities.
Usage: python manage.py score_resume <resume_id>
"""

from django.core.management.base import BaseCommand, CommandError
from resumes.services import ResumeScoringService
from resumes.models import Resume


class Command(BaseCommand):
    help = 'Score a specific resume against all opportunities'

    def add_arguments(self, parser):
        parser.add_argument('resume_id', type=int, help='Resume ID to score')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rescore even if already scored'
        )

    def handle(self, *args, **options):
        resume_id = options['resume_id']
        force = options['force']

        # Get resume
        try:
            resume = Resume.objects.get(id=resume_id)
        except Resume.DoesNotExist:
            raise CommandError(f'Resume with ID {resume_id} does not exist')

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS(f'📊 SCORING RESUME #{resume_id}'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        self.stdout.write(f"Volunteer: {resume.user.username}")
        self.stdout.write(f"Filename: {resume.original_filename}")
        self.stdout.write(f"Force Rescore: {force}\n")

        # Score
        try:
            service = ResumeScoringService()
            scores = service.score_resume_for_all_opportunities(resume, force=force)

            self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
            self.stdout.write(self.style.SUCCESS('✅ SCORING COMPLETE'))
            self.stdout.write(self.style.SUCCESS('=' * 80))
            self.stdout.write(f"\n✅ Created/Updated {len(scores)} scores\n")

            # Show top 5 matches
            top_scores = sorted(scores, key=lambda s: s.overall_score, reverse=True)[:5]
            self.stdout.write("\n🏆 TOP 5 MATCHES:")
            for i, score in enumerate(top_scores, 1):
                self.stdout.write(
                    f"  {i}. {score.opportunity.title[:50]}: "
                    f"{score.overall_score}/100 ({score.grade}) - {score.recommendation}"
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error: {e}'))
            raise