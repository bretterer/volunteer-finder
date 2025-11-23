"""
Script to migrate all .json data files to Django model.
Main call: python manage.py migrate_data_to_django
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils import timezone
from pathlib import Path
import json

from accounts.models import User, VolunteerProfile
from opportunities.models import Opportunity
from resumes.models import Resume, ResumeScore

class Command(BaseCommand):
    help = 'Migrate all .json data files to Django model.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.json_dir = None
        self.resumes_dir = None
        self.opportunities_dir = None
        self.dry_run = False
        self.resume_map = {}
        self.opportunity_map = {}
        self.stats = {
            'opportunities': {'created': 0, 'skipped': 0, 'errors': 0},
            'resumes': {'created': 0, 'skipped': 0, 'errors': 0},
            'scores': {'created': 0, 'skipped': 0, 'errors': 0},
        }
        self.admin_user = None


    def add_arguments(self, parser):
        parser.add_argument(
            '--json-dir',
            type=str,
            default='results',
            help='Directory containing JSON database files'
        )
        parser.add_argument(
            '--resumes-dir',
            type=str,
            default='resumes',
            help='Directory containing resume files'
        )
        parser.add_argument(
            '--opportunities-dir',
            type=str,
            default='opportunities',
            help='Directory containing opportunity files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate migration without saving to database'
        )

    def handle(self, *args, **options):
        self.json_dir = Path(options['json_dir'])
        self.resumes_dir = Path(options['resumes_dir'])
        self.opportunities_dir = Path(options['opportunities_dir'])
        self.dry_run = options['dry_run']

        if self.dry_run:
            self.stdout.write(self.style.WARNING('Dry Run Mode: NO Data Will Be Saved'))

        self.print_header()

        self.stdout.write(self.style.SUCCESS('JSON -> Django in progress'))
        self.migrate_opportunities()
        self.migrate_resumes()
        self.migrate_scores()

        self.print_summary()

    def print_header(self):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('Migration: JSON to Django Database in Progress'))
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))

    def print_summary(self):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        for resource, counts in self.stats.items():
            self.stdout.write(
                f"\n{resource.upper()}:"
                f"\n  ✓ Created: {counts['created']}"
                f"\n  ⏭ Skipped: {counts['skipped']}"
                f"\n  ✗ Errors:  {counts['errors']}"
            )

        total_created = sum(s['created'] for s in self.stats.values())
        total_skipped = sum(s['skipped'] for s in self.stats.values())
        total_errors = sum(s['errors'] for s in self.stats.values())

        self.stdout.write(self.style.SUCCESS(
            f"\n\nTOTAL: {total_created} created, {total_skipped} skipped, {total_errors} errors"
        ))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

    def load_json(self, filename):
        file_path = self.json_dir / filename
        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {file_path}: {e}'))
            return None

    def migrate_opportunities(self):
        self.stdout.write('Migrating Opportunities....')

        data = self.load_json('opportunities_database.json')
        if not data:
            return

        opportunities = data.get('opportunities', {})
        self.admin_user = self.get_or_create_admin()

        for opp_id, opp_data in opportunities.items():
            self.migrate_single_opportunity(int(opp_id), opp_data)

        self.stdout.write(self.style.SUCCESS(
            f"✓ Opportunities: {self.stats['opportunities']['created']} created, "
            f"{self.stats['opportunities']['skipped']} skipped"
        ))

    def migrate_single_opportunity(self, opp_id, opp_data):
        existing = Opportunity.objects.filter(title=opp_data['position']).first()

        if existing:
            self.opportunity_map[opp_id] = existing
            self.stats['opportunities']['skipped'] += 1
            return

        if self.dry_run:
            self.stdout.write(f"[DRY RUN] Would create: {opp_data['position'][:50]}")
            self.stats['opportunities']['created'] += 1
            return
        try:
            # Create opportunity
            opportunity = Opportunity.objects.create(
                organization=self.admin_user,
                title=opp_data['position'],
                description=opp_data.get('description', ''),
                required_skills=opp_data.get('required_skills', []),
                location=opp_data.get('department', 'Campus'),
                start_date=timezone.now().date(),
                hours_required=opp_data.get('hours_per_week', 10),
                spots_available=1,
                status='active'
            )

            # Store mapping
            self.opportunity_map[opp_id] = opportunity

            self.stdout.write(f'   ✓ Created: {opportunity.title[:50]}')
            self.stats['opportunities']['created'] += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            self.stats['opportunities']['errors'] += 1

    def migrate_resumes(self):
        """Migrate resumes from JSON to Django."""
        self.stdout.write('\n📄 MIGRATING RESUMES...')

        data = self.load_json('resumes_database.json')
        if not data:
            return

        resumes_data = data.get('resumes', {})

        for resume_id, resume_data in resumes_data.items():
            self.migrate_single_resume(int(resume_id), resume_data)

        self.stdout.write(self.style.SUCCESS(
            f"✓ Resumes: {self.stats['resumes']['created']} created, "
            f"{self.stats['resumes']['skipped']} skipped, "
            f"{self.stats['resumes']['errors']} errors"))

    def migrate_single_resume(self, resume_id, resume_data):
        filename = resume_data['filename']
        filepath = self.resumes_dir / filename

        # Check if file exists
        if not filepath.exists():
            self.stdout.write(self.style.WARNING(f'   ⚠️  File not found: {filename}'))
            self.stats['resumes']['errors'] += 1
            return

        # Check if already migrated
        existing = Resume.objects.filter(original_filename=filename).first()
        if existing:
            self.resume_map[resume_id] = existing
            self.stats['resumes']['skipped'] += 1
            return

        if self.dry_run:
            self.stdout.write(f'   [DRY RUN] Would create: {filename}')
            self.stats['resumes']['created'] += 1
            return

        try:
            # Get or create user
            user = self.get_or_create_volunteer(filename)

            # Create resume
            with open(filepath, 'rb') as f:
                resume = Resume(
                    user=user,
                    original_filename=filename,
                    file_size=filepath.stat().st_size,
                    extracted_text=resume_data.get('text', ''),
                    processed=True
                )
                resume.file.save(filename, File(f), save=False)
                resume.save()

            # Store mapping
            self.resume_map[resume_id] = resume

            self.stdout.write(f'   ✓ Created: {filename[:50]}')
            self.stats['resumes']['created'] += 1

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error: {e}'))
            self.stats['resumes']['errors'] += 1

    def migrate_scores(self):
        """Migrate scores from JSON to Django."""
        self.stdout.write('\n📊 MIGRATING SCORES...')

        if not self.resume_map or not self.opportunity_map:
            self.stdout.write(self.style.ERROR(
                '   ✗ Cannot migrate scores - no resumes or opportunities migrated'
            ))
            return

        data = self.load_json('scores_database.json')
        if not data:
            return

        scores_data = data.get('scores', {})

        for resume_id, resume_scores in scores_data.items():
            self.migrate_resume_scores(int(resume_id), resume_scores)

        self.stdout.write(self.style.SUCCESS(
            f"✓ Scores: {self.stats['scores']['created']} created, "
            f"{self.stats['scores']['skipped']} skipped, "
            f"{self.stats['scores']['errors']} errors"
        ))

    def migrate_resume_scores(self, resume_id, resume_scores):
        if resume_id not in self.resume_map:
            return

        resume = self.resume_map[resume_id]

        for opp_id, score_data in resume_scores.items():
            self.migrate_single_score(resume, int(opp_id), score_data)

    def migrate_single_score(self, resume, opp_id, score_data):
        if opp_id not in self.opportunity_map:
            return

        opportunity = self.opportunity_map[opp_id]

        existing = ResumeScore.objects.filter(
            resume=resume,
            opportunity=opportunity
        ).first()

        if existing:
            self.stats['scores']['skipped'] += 1
            return

        if self.dry_run:
            self.stats['scores']['created'] += 1
            return

        try:
            # Map recommendation
            recommendation = self.map_recommendation(score_data.get('recommendation', 'Consider'))

            # Create score
            ResumeScore.objects.create(
                resume=resume,
                opportunity=opportunity,
                overall_score=score_data.get('overall', 0),
                skills_match=score_data.get('skills_match', 0),
                experience_match=score_data.get('experience_match', 0),
                education_match=score_data.get('education_match', 0),
                grade=score_data.get('grade', 'F'),
                recommendation=recommendation,
                key_strength=score_data.get('key_strength', ''),
                concerns=score_data.get('concerns', ''),
                scored_by_model='gpt-4o-mini'
            )

            self.stats['scores']['created'] += 1

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Error creating score: {e}'))
            self.stats['scores']['errors'] += 1

    def map_recommendation(self, recommendation_str):

        recommendation_map = {
            'Highly Recommended': 'highly_recommended',
            'Recommended': 'recommended',
            'Consider': 'consider',
            'Not Recommended': 'not_recommended'
        }
        return recommendation_map.get(recommendation_str, 'consider')

    def get_or_create_admin(self):
        """
        Get or create admin user for opportunities.

        Returns:
            User: Admin user instance
        """
        admin = User.objects.filter(user_type='admin', username='system_admin').first()

        if not admin:
            admin = User.objects.create_user(
                username='system_admin',
                email='admin@volunteer-finder.com',
                user_type='admin',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('   ✓ Created system admin user')

        return admin

    def get_or_create_volunteer(self, filename):
        """
        Get or create volunteer user for resume.

        Args:
            filename: Resume filename to extract name from

        Returns:
            User: Volunteer user instance
        """
        # Extract name from filename
        base_name = Path(filename).stem.replace('_Resume', '').replace('_', ' ')
        username = base_name.lower().replace(' ', '_')[:30]

        # Check if user exists
        user = User.objects.filter(username=username).first()
        if user:
            return user

        # Create new volunteer user
        user = User.objects.create_user(
            username=username,
            email=f'{username}@volunteer.com',
            user_type='volunteer'
        )

        # Create volunteer profile
        VolunteerProfile.objects.create(user=user)

        return user




