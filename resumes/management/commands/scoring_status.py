"""
Display scoring system status and statistics.
Usage: python manage.py scoring_status
"""

from django.core.management.base import BaseCommand
from resumes.models import Resume, ResumeScore
from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Display scoring system status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 SCORING SYSTEM STATUS'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Counts
        total_resumes = Resume.objects.count()
        processed_resumes = Resume.objects.filter(processed=True).count()
        total_opportunities = Opportunity.objects.count()
        active_opportunities = Opportunity.objects.filter(status='active').count()
        total_scores = ResumeScore.objects.count()

        self.stdout.write(f"📄 Resumes:")
        self.stdout.write(f"   Total: {total_resumes}")
        self.stdout.write(f"   Processed: {processed_resumes}")
        self.stdout.write(f"   Unprocessed: {total_resumes - processed_resumes}\n")

        self.stdout.write(f"💼 Opportunities:")
        self.stdout.write(f"   Total: {total_opportunities}")
        self.stdout.write(f"   Active: {active_opportunities}")
        self.stdout.write(f"   Inactive: {total_opportunities - active_opportunities}\n")

        # Calculate coverage
        max_possible = processed_resumes * active_opportunities
        coverage = (total_scores / max_possible * 100) if max_possible > 0 else 0
        unscored = max_possible - total_scores

        self.stdout.write(f"📊 Scoring Coverage:")
        self.stdout.write(f"   Total Scores: {total_scores}")
        self.stdout.write(f"   Max Possible: {max_possible}")
        self.stdout.write(f"   Coverage: {coverage:.1f}%")
        self.stdout.write(f"   Unscored Pairs: {unscored}\n")

        # Grade distribution
        from django.db.models import Count
        grade_dist = ResumeScore.objects.values('grade').annotate(count=Count('grade')).order_by('-count')

        self.stdout.write(f"🎓 Grade Distribution:")
        for item in grade_dist:
            self.stdout.write(f"   {item['grade']}: {item['count']}")

        self.stdout.write('\n' + '=' * 80 + '\n')