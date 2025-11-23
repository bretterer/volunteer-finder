"""
Monitor a folder for new opportunity files and add them to Django.
Usage: python manage.py watch_for_opportunities
"""

from django.core.management.base import BaseCommand
from pathlib import Path
import time
from datetime import datetime
import re

from accounts.models import User
from opportunities.models import Opportunity


class Command(BaseCommand):
    help = 'Monitor folder for new opportunities and automatically add them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default='opportunity_uploads',
            help='Folder to monitor for new opportunities'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=300,
            help='Check interval in seconds (default: 300 = 5 minutes)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Check once and exit (don\'t loop)'
        )

    def handle(self, *args, **options):
        folder = Path(options['folder'])
        interval = options['interval']
        once = options['once']

        if not folder.exists():
            self.stdout.write(self.style.ERROR(f"❌ Folder not found: {folder}"))
            return

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('👀 OPPORTUNITY FILE MONITOR'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"\n📁 Watching: {folder.absolute()}")
        self.stdout.write(f"⏱️  Interval: {interval} seconds ({interval / 60:.1f} minutes)")
        self.stdout.write(f"🔄 Mode: {'Single check' if once else 'Continuous'}\n")

        if not once:
            self.stdout.write(self.style.WARNING("Press Ctrl+C to stop\n"))

        # Main loop
        try:
            while True:
                self.check_for_new_files(folder)

                if once:
                    break

                # Wait for next check
                next_check = datetime.now().timestamp() + interval
                self.stdout.write(f"\n⏳ Waiting {interval} seconds until next check...")
                self.stdout.write(
                    f"   Next check at: {datetime.fromtimestamp(next_check).strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('\n\n🛑 MONITOR STOPPED'))

    def check_for_new_files(self, folder: Path):
        """Check folder for new opportunity files."""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(f'🔄 FILE CHECK - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        # Supported extensions
        extensions = ['.pdf', '.txt']

        # Find all opportunity files
        opportunity_files = []
        for ext in extensions:
            opportunity_files.extend(folder.glob(f'*{ext}'))

        self.stdout.write(f"\n📂 Found {len(opportunity_files)} files in {folder}")

        # Check which are new (by checking if filename already exists in DB)
        new_files = []
        for file_path in opportunity_files:
            # Create a unique identifier from filename
            file_identifier = file_path.stem  # filename without extension

            # Check if already in database (by checking if similar title exists)
            exists = Opportunity.objects.filter(
                title__icontains=file_identifier.replace('_', ' ')[:50]
            ).exists()

            if not exists:
                new_files.append(file_path)

        if not new_files:
            self.stdout.write("✅ No new files to process")
            return

        self.stdout.write(f"\n🆕 Found {len(new_files)} new files:")
        for file_path in new_files:
            self.stdout.write(f"   • {file_path.name}")

        # Process new files
        added_count = 0
        for file_path in new_files:
            if self.add_opportunity_to_database(file_path):
                added_count += 1

        self.stdout.write(f"\n✅ Added {added_count} opportunities to database")

    def add_opportunity_to_database(self, file_path: Path) -> bool:
        """
        Add an opportunity file to the database.

        Args:
            file_path: Path to opportunity file

        Returns:
            True if successful, False otherwise
        """
        try:
            filename = file_path.name

            # Extract text based on file type
            extracted_text = self.extract_text(file_path)

            if not extracted_text:
                self.stdout.write(self.style.WARNING(f"   ⚠️  No text extracted from {filename}"))
                return False

            # Parse opportunity details from text
            opp_data = self.parse_opportunity_text(extracted_text, filename)

            # Get or create organization user
            org_user = self.get_or_create_organization(opp_data['organization_name'])

            # Create opportunity record
            opportunity = Opportunity.objects.create(
                organization=org_user,
                title=opp_data['title'],
                description=opp_data['description'],
                location=opp_data['location'],
                required_skills=opp_data['required_skills'],
                hours_required=opp_data['hours_required'],
                spots_available=opp_data['spots_available'],
                start_date=opp_data['start_date'],
                end_date=opp_data['end_date'],
                status='active'
            )

            self.stdout.write(f"   ✅ Added: {opp_data['title'][:50]}")
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error adding {file_path.name}: {e}"))
            return False

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from opportunity file.

        Args:
            file_path: Path to file

        Returns:
            Extracted text
        """
        ext = file_path.suffix.lower()

        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()

            elif ext == '.pdf':
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text() + '\n'
                    return text

            else:
                return ''

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Text extraction failed: {e}"))
            return ''

    def parse_opportunity_text(self, text: str, filename: str) -> dict:
        """
        Parse opportunity details from extracted text.

        Args:
            text: Extracted text from file
            filename: Original filename

        Returns:
            Dictionary of opportunity data
        """
        # Initialize with defaults
        data = {
            'title': filename.replace('.pdf', '').replace('.txt', '').replace('_', ' '),
            'description': text,
            'location': 'Not specified',
            'organization_name': 'System Admin',
            'required_skills': [],
            'hours_required': 5,
            'spots_available': 1,
            'start_date': None,
            'end_date': None
        }

        # Try to extract POSITION
        position_match = re.search(r'POSITION:\s*(.+?)(?:\n|DEPARTMENT:)', text, re.IGNORECASE)
        if position_match:
            data['title'] = position_match.group(1).strip()

        # Try to extract DEPARTMENT/Location
        dept_match = re.search(r'DEPARTMENT:\s*(.+?)(?:\n|Volunteers)', text, re.IGNORECASE)
        if dept_match:
            data['location'] = dept_match.group(1).strip()

        # Try to extract Volunteers Needed
        spots_match = re.search(r'Volunteers Needed:\s*(\d+)', text, re.IGNORECASE)
        if spots_match:
            data['spots_available'] = int(spots_match.group(1))

        # Try to extract organization leaders
        org_match = re.search(r'ORGANIZATIONAL LEADERS?:\s*(.+?)(?:\n\n|REQUIREMENTS|$)', text,
                              re.IGNORECASE | re.DOTALL)
        if org_match:
            leaders = org_match.group(1).strip()
            # Extract first leader name
            first_leader = re.search(r'[-•]\s*(?:Prof\.|Dr\.)?\s*(.+?)(?:\n|$)', leaders)
            if first_leader:
                data['organization_name'] = first_leader.group(1).strip()

        # Try to extract hours required
        hours_match = re.search(r'(\d+)\s*hours?\s*(?:per week|weekly)', text, re.IGNORECASE)
        if hours_match:
            data['hours_required'] = int(hours_match.group(1))

        return data

    def get_or_create_organization(self, org_name: str) -> User:
        """
        Get or create organization user.

        Args:
            org_name: Organization name

        Returns:
            User instance
        """
        # Create username from organization name
        username = org_name.lower().replace(' ', '_').replace('.', '')[:30]

        # Check if user exists
        user = User.objects.filter(username=username).first()
        if user:
            return user

        # Create new organization
        user = User.objects.create_user(
            username=username,
            email=f'{username}@university.edu',
            user_type='organization'
        )

        return user