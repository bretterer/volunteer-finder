"""
File monitor - detects new resumes and opportunities, registers them
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from storage_manager import StorageManager, StorageError
from file_readers import ResumeReader, FileReadError
from text_processor import TextProcessor, TextProcessingError

logger = logging.getLogger(__name__)


class FileMonitor:
    """Monitor folders for new resumes and opportunities"""

    def __init__(
            self,
            storage: StorageManager,
            resumes_folder: str | Path = 'resumes',
            opportunities_folder: str | Path = 'opportunities'
    ):
        """
        Initialize file monitor.

        Args:
            storage: StorageManager instance
            resumes_folder: Path to resumes folder
            opportunities_folder: Path to opportunities folder
        """
        self.storage = storage
        self.resumes_folder = Path(resumes_folder)
        self.opportunities_folder = Path(opportunities_folder)

        # Create folders if they don't exist
        self.resumes_folder.mkdir(exist_ok=True)
        self.opportunities_folder.mkdir(exist_ok=True)

    def scan_for_new_resumes(self) -> List[int]:
        """
        Scan resumes folder and register any new resumes.

        Returns:
            List of newly registered resume IDs
        """
        if not self.resumes_folder.exists():
            logger.warning(f"Resumes folder not found: {self.resumes_folder}")
            return []

        new_resume_ids = []
        existing_resumes = self.storage.get_all_resumes()
        existing_filenames = {r['filename'] for r in existing_resumes.values()}

        # Get all supported files
        resume_files = [
            f for f in self.resumes_folder.iterdir()
            if f.is_file() and ResumeReader.is_supported(f)
        ]

        logger.info(f"Scanning {len(resume_files)} files in resumes folder...")

        for resume_file in resume_files:
            # Skip if already registered
            if resume_file.name in existing_filenames:
                logger.debug(f"Already registered: {resume_file.name}")
                continue

            try:
                # Read the file
                text = ResumeReader.read_file(resume_file)

                # Extract contact info
                email = TextProcessor.find_email(text)
                phone = TextProcessor.find_phone(text)

                # Register in storage
                resume_id = self.storage.register_resume(
                    filename=resume_file.name,
                    file_path=str(resume_file),
                    text=text
                )

                # Update with contact info
                resume_data = self.storage.get_resume(resume_id)
                if resume_data:
                    resume_data['email'] = email
                    resume_data['phone'] = phone
                    # Save back (we need to add this method to StorageManager)

                new_resume_ids.append(resume_id)
                logger.info(f"✓ New resume registered: {resume_file.name} (ID: {resume_id})")

            except FileReadError as e:
                logger.error(f"Failed to read {resume_file.name}: {e}")
            except StorageError as e:
                logger.error(f"Failed to register {resume_file.name}: {e}")

        if new_resume_ids:
            logger.info(f"Registered {len(new_resume_ids)} new resumes")
        else:
            logger.info("No new resumes found")

        return new_resume_ids

    def scan_for_new_opportunities(self) -> List[int]:
        """
        Scan opportunities folder and register any new opportunities.

        Returns:
            List of newly registered opportunity IDs
        """
        if not self.opportunities_folder.exists():
            logger.warning(f"Opportunities folder not found: {self.opportunities_folder}")
            return []

        new_opp_ids = []
        existing_opps = self.storage.get_all_opportunities()
        existing_filenames = {o['filename'] for o in existing_opps.values()}

        # Get all supported files
        opp_files = [
            f for f in self.opportunities_folder.iterdir()
            if f.is_file() and ResumeReader.is_supported(f)
        ]

        logger.info(f"Scanning {len(opp_files)} files in opportunities folder...")

        for opp_file in opp_files:
            # Skip if already registered
            if opp_file.name in existing_filenames:
                logger.debug(f"Already registered: {opp_file.name}")
                continue

            try:
                # Read the file
                text = ResumeReader.read_file(opp_file)

                # Extract position (simple approach)
                position = self._extract_position_from_text(text, opp_file.name)

                # Register in storage
                opp_id = self.storage.register_opportunity(
                    filename=opp_file.name,
                    file_path=str(opp_file),
                    text=text,
                    position=position
                )

                new_opp_ids.append(opp_id)
                logger.info(f"✓ New opportunity registered: {opp_file.name} (ID: {opp_id})")
                logger.info(f"   Position: {position}")

            except FileReadError as e:
                logger.error(f"Failed to read {opp_file.name}: {e}")
            except StorageError as e:
                logger.error(f"Failed to register {opp_file.name}: {e}")

        if new_opp_ids:
            logger.info(f"Registered {len(new_opp_ids)} new opportunities")
        else:
            logger.info("No new opportunities found")

        return new_opp_ids

    def _extract_position_from_text(self, text: str, filename: str) -> str:
        """Extract position title from opportunity text"""
        lines = text.strip().split('\n')

        # Look for position indicators
        for line in lines[:10]:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['position:', 'role:', 'title:', 'job title:']):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()[:100]

        # Fallback: use first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()[:100]

        # Last resort: use filename
        return filename.replace('_', ' ').replace('.txt', '').replace('.pdf', '')[:100]

    def check_for_new_files(self) -> Tuple[List[int], List[int]]:
        """
        Check both folders for new files.

        Returns:
            Tuple of (new_resume_ids, new_opp_ids)
        """
        logger.info("=" * 80)
        logger.info("Checking for new files...")
        logger.info("=" * 80)

        new_resume_ids = self.scan_for_new_resumes()
        new_opp_ids = self.scan_for_new_opportunities()

        logger.info("=" * 80)
        logger.info(f"Summary: {len(new_resume_ids)} new resumes, {len(new_opp_ids)} new opportunities")
        logger.info("=" * 80)

        return new_resume_ids, new_opp_ids