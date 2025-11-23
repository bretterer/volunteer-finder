"""
Restore full opportunity descriptions from JSON data.
Usage: python manage.py fix_descriptions
"""

from django.core.management.base import BaseCommand
import json
from pathlib import Path
from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Restore full opportunity descriptions from JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default='results/opportunities_database.json',
            help='Path to opportunities JSON file'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without saving'
        )

    def handle(self, *args, **options):
        json_file = Path(options['json_file'])
        dry_run = options['dry_run']

        if not json_file.exists():
            self.stdout.write(self.style.ERROR(f"❌ File not found: {json_file}"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE\n'))

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📝 RESTORING OPPORTUNITY DESCRIPTIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Load JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        opportunities_data = data.get('opportunities', {})

        if not isinstance(opportunities_data, dict):
            self.stdout.write(self.style.ERROR("❌ Expected dict structure"))
            return

        self.stdout.write(f"Found {len(opportunities_data)} opportunities in JSON\n")

        updated = 0
        skipped = 0
        errors = 0

        # Iterate through dictionary
        for opp_id_str, opp_data in opportunities_data.items():
            try:
                # Convert string ID to int
                opp_id = int(opp_id_str)

                # Find matching opportunity in database
                try:
                    opp = Opportunity.objects.get(id=opp_id)
                except Opportunity.DoesNotExist:
                    skipped += 1
                    continue

                # Get full text from JSON (this is the key change!)
                full_text = opp_data.get('text', '')

                if not full_text:
                    self.stdout.write(f"⚠️  No text for ID {opp_id}")
                    skipped += 1
                    continue

                # Skip if description is already good
                if len(opp.description) >= len(full_text) * 0.9:
                    skipped += 1
                    continue

                # Show what will change (first 5 only)
                if updated < 5:
                    self.stdout.write(f"\n📝 Opportunity #{opp_id}: {opp.title[:50]}")
                    self.stdout.write(f"   Current: {len(opp.description)} chars")
                    self.stdout.write(f"   New: {len(full_text)} chars")
                    self.stdout.write(f"   Preview: {full_text[:100]}...")

                if dry_run:
                    updated += 1
                    continue

                # Update description with full text
                opp.description = full_text
                opp.save(update_fields=['description'])

                if updated < 5:
                    self.stdout.write(self.style.SUCCESS("   ✅ Updated"))

                updated += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error for ID {opp_id_str}: {e}"))
                errors += 1

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"\n✅ Updated: {updated}")
        self.stdout.write(f"⏭️  Skipped: {skipped}")
        self.stdout.write(f"❌ Errors: {errors}\n")