"""
Monitor a folder for new resume files and add them to Django.
Usage: python manage.py watch_for_resumes
"""

from django.core.management.base import BaseCommand
from django.core.files import File
from pathlib import Path
import time
from datetime import datetime

from accounts.models import User, VolunteerProfile
from resumes.models import Resume
from resumes.services import ResumeScoringService


class Command(BaseCommand):
    help = 'Monitor folder for new resumes and automatically score them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            default='resume_uploads',
            help='Folder to monitor for new resumes'
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
        parser.add_argument(
            '--auto-score',
            action='store_true',
            help='Automatically score new resumes after adding'
        )

    def handle(self, *args, **options):
        folder = Path(options['folder'])
        interval = options['interval']
        once = options['once']
        auto_score = options['auto_score']

        if not folder.exists():
            self.stdout.write(self.style.ERROR(f"❌ Folder not found: {folder}"))
            return

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('👀 RESUME FILE MONITOR'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"\n📁 Watching: {folder.absolute()}")
        self.stdout.write(f"⏱️  Interval: {interval} seconds ({interval / 60:.1f} minutes)")
        self.stdout.write(f"🤖 Auto-score: {'Yes' if auto_score else 'No'}")
        self.stdout.write(f"🔄 Mode: {'Single check' if once else 'Continuous'}\n")

        if not once:
            self.stdout.write(self.style.WARNING("Press Ctrl+C to stop\n"))

        # Main loop
        try:
            while True:
                self.check_for_new_files(folder, auto_score)

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

    def check_for_new_files(self, folder: Path, auto_score: bool):
        """Check folder for new resume files."""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(f'🔄 FILE CHECK - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('=' * 80)

        # Supported extensions
        extensions = ['.pdf', '.docx', '.txt']

        # Find all resume files
        resume_files = []
        for ext in extensions:
            resume_files.extend(folder.glob(f'*{ext}'))

        self.stdout.write(f"\n📂 Found {len(resume_files)} files in {folder}")

        # Check which are new
        new_files = []
        for file_path in resume_files:
            filename = file_path.name

            # Check if already in database
            exists = Resume.objects.filter(original_filename=filename).exists()
            if not exists:
                new_files.append(file_path)

        if not new_files:
            self.stdout.write("✅ No new files to process")
            return

        self.stdout.write(f"\n🆕 Found {len(new_files)} new files:")
        for file_path in new_files:
            self.stdout.write(f"   • {file_path.name}")

        # Process new files
        added_resumes = []
        for file_path in new_files:
            resume = self.add_resume_to_database(file_path)
            if resume:
                added_resumes.append(resume)

        self.stdout.write(f"\n✅ Added {len(added_resumes)} resumes to database")

        # Auto-score if requested
        if auto_score and added_resumes:
            self.stdout.write("\n🤖 AUTO-SCORING NEW RESUMES...")
            service = ResumeScoringService()

            for resume in added_resumes:
                self.stdout.write(f"\n   Scoring: {resume.original_filename}")
                try:
                    scores = service.score_resume_for_all_opportunities(resume)
                    self.stdout.write(f"   ✅ Created {len(scores)} scores")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Error: {e}"))

    def add_resume_to_database(self, file_path: Path) -> Resume:
        """
        Add a resume file to the database.

        Args:
            file_path: Path to resume file

        Returns:
            Resume instance or None if failed
        """
        try:
            filename = file_path.name

            # Get or create user
            user = self.get_or_create_volunteer(filename)

            # Extract text based on file type
            extracted_text = self.extract_text(file_path)

            # Create resume record
            with open(file_path, 'rb') as f:
                resume = Resume(
                    user=user,
                    original_filename=filename,
                    file_size=file_path.stat().st_size,
                    extracted_text=extracted_text,
                    processed=True
                )
                resume.file.save(filename, File(f), save=False)
                resume.save()

            self.stdout.write(f"   ✅ Added: {filename}")
            return resume

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Error adding {file_path.name}: {e}"))
            return None

    def extract_text(self, file_path: Path) -> str:
        """
        Extract text from resume file.

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

            elif ext == '.docx':
                import docx
                doc = docx.Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs])
                return text

            else:
                return ''

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Text extraction failed: {e}"))
            return ''

    def get_or_create_volunteer(self, filename: str) -> User:
        """
        Get or create volunteer user from filename.

        Args:
            filename: Resume filename

        Returns:
            User instance
        """
        # Extract name from filename
        base_name = Path(filename).stem.replace('_Resume', '').replace('_resume', '').replace('_', ' ')
        username = base_name.lower().replace(' ', '_')[:30]

        # Check if user exists
        user = User.objects.filter(username=username).first()
        if user:
            return user

        # Create new volunteer
        user = User.objects.create_user(
            username=username,
            email=f'{username}@volunteer.com',
            user_type='volunteer'
        )

        # Create volunteer profile
        VolunteerProfile.objects.create(user=user)

        return user