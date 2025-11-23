"""
Check the structure of opportunities JSON file.
Usage: python manage.py check_json_structure
"""

from django.core.management.base import BaseCommand
import json
from pathlib import Path


class Command(BaseCommand):
    help = 'Check JSON structure'

    def handle(self, *args, **options):
        json_file = Path('results/opportunities_database.json')

        if not json_file.exists():
            self.stdout.write(self.style.ERROR(f"❌ File not found: {json_file}"))
            return

        # Load JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📊 JSON STRUCTURE'))
        self.stdout.write(self.style.SUCCESS('=' * 80 + '\n'))

        # Check top-level keys
        self.stdout.write("Top-level keys:")
        for key in data.keys():
            self.stdout.write(f"  • {key}: {type(data[key]).__name__}")

        # Check opportunities structure
        if 'opportunities' in data:
            opps = data['opportunities']
            self.stdout.write(f"\nOpportunities type: {type(opps).__name__}")

            if isinstance(opps, dict):
                # Dictionary structure
                self.stdout.write(f"Opportunities count: {len(opps)}")
                self.stdout.write("Opportunity IDs (first 10):")
                for i, key in enumerate(list(opps.keys())[:10]):
                    self.stdout.write(f"  • {key}")

                # Get first opportunity
                first_key = list(opps.keys())[0]
                first_opp = opps[first_key]

                self.stdout.write(f"\nFirst opportunity (ID: {first_key}):")
                self.stdout.write(f"Type: {type(first_opp).__name__}")

                if isinstance(first_opp, dict):
                    self.stdout.write("\nKeys in opportunity:")
                    for key in first_opp.keys():
                        value = first_opp[key]
                        if isinstance(value, str):
                            preview = value[:100]
                        else:
                            preview = str(value)
                        self.stdout.write(f"  • {key}: {preview}")

                elif isinstance(first_opp, str):
                    self.stdout.write(f"\nValue (first 300 chars):\n{first_opp[:300]}...")

            elif isinstance(opps, list):
                # List structure
                self.stdout.write(f"Opportunities count: {len(opps)}")
                first = opps[0]
                self.stdout.write(f"\nFirst opportunity type: {type(first).__name__}")
                if isinstance(first, dict):
                    self.stdout.write("Keys:")
                    for key in first.keys():
                        self.stdout.write(f"  • {key}")