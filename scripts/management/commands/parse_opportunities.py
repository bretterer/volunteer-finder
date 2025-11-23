"""
Parse opportunity descriptions and extract structured data.
Usage: python manage.py parse_opportunities
"""

from django.core.management.base import BaseCommand
import re
from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Parse opportunity descriptions and extract POSITION, DEPARTMENT, and Volunteers Needed'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if fields seem correct'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be saved\n'))

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📋 PARSING OPPORTUNITY DESCRIPTIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Get all opportunities
        opportunities = Opportunity.objects.all()

        for opp in opportunities:
            self.parse_and_update_opportunity(opp, dry_run, force)

        # Print summary
        self.print_summary()

    def parse_and_update_opportunity(self, opp, dry_run, force):
        full_text = opp.title

        try:
            # Check if title needs parsing (contains "POSITION:")
            needs_parsing = "POSITION:" in full_text or len(full_text) > 150

            if not needs_parsing and not force:
                self.stdout.write(f"⏭️  Skipped ID {opp.id}: Already clean")
                self.stats['skipped'] += 1
                return

            # IMPROVED: Extract POSITION - text immediately after "POSITION:" up to "DEPARTMENT:"
            # Using non-greedy match and stripping whitespace
            position_match = re.search(r'POSITION:\s*(.+?)\s+DEPARTMENT:', full_text)
            if position_match:
                position = position_match.group(1).strip()
            else:
                # Fallback: try to get first 100 chars
                position = re.sub(r'POSITION:\s*', '', full_text.split('DEPARTMENT:')[0]).strip()[:100]

            # IMPROVED: Extract DEPARTMENT - text after "DEPARTMENT:" up to "Volunteers Needed:"
            dept_match = re.search(r'DEPARTMENT:\s*(.+?)\s+Volunteers\s+Needed:', full_text)
            if dept_match:
                department = dept_match.group(1).strip()
            else:
                department = opp.location

            # Extract Volunteers Needed
            volunteers_match = re.search(r'Volunteers\s+Needed:\s*(\d+)', full_text)
            if volunteers_match:
                volunteers_needed = int(volunteers_match.group(1))
            else:
                volunteers_needed = opp.spots_available

            # IMPROVED: Extract clean description - from "ORGANIZATIONAL" onwards
            # Remove everything before it
            desc_match = re.search(
                r'(ORGANIZATIONAL\s+LEADERS:.*)',
                full_text,
                re.DOTALL
            )
            if desc_match:
                clean_description = desc_match.group(1).strip()
            else:
                # Fallback - try ABOUT THE ROLE
                desc_match2 = re.search(r'(ABOUT\s+THE\s+ROLE:.*)', full_text, re.DOTALL)
                if desc_match2:
                    clean_description = desc_match2.group(1).strip()
                else:
                    clean_description = opp.description

            # Show what will change
            self.stdout.write(f"\n📝 Opportunity ID {opp.id}:")
            self.stdout.write(f"   OLD Title ({len(opp.title)} chars): '{opp.title[:80]}...'")
            self.stdout.write(f"   NEW Title ({len(position)} chars): '{position}'")
            self.stdout.write(f"   Department: '{opp.location}' → '{department}'")
            self.stdout.write(f"   Volunteers: {opp.spots_available} → {volunteers_needed}")
            self.stdout.write(f"   Description: {len(opp.description)} → {len(clean_description)} chars")

            if dry_run:
                self.stdout.write(self.style.WARNING("   [DRY RUN - Not saved]"))
                self.stats['updated'] += 1
                return

            # Update the opportunity
            opp.title = position
            opp.location = department
            opp.spots_available = volunteers_needed
            opp.description = clean_description
            opp.save()

            self.stdout.write(self.style.SUCCESS(f"   ✓ Saved"))
            self.stats['updated'] += 1

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ✗ Error: {e}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            self.stats['errors'] += 1

    def print_summary(self):
        """Print parsing statistics."""
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 PARSING SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(
            f"\n✓ Updated: {self.stats['updated']}"
            f"\n⏭️  Skipped: {self.stats['skipped']}"
            f"\n✗ Errors:  {self.stats['errors']}"
        )
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80 + '\n'))