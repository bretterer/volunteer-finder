"""
Automatic scorer - monitors folders and scores new files
"""

import logging
import time
from pathlib import Path
from datetime import datetime

from storage_manager import StorageManager
from file_monitor import FileMonitor
from incremental_scorer import IncrementalScorer
from results_generator import ResultsGenerator

logger = logging.getLogger(__name__)


class AutoScorer:
    """Automatic scoring system with file monitoring"""

    def __init__(
            self,
            project_path: str | Path = '.',
            threshold: int = 70,
            check_interval: int = 300  # 5 minutes in seconds
    ):
        """
        Initialize auto scorer.

        Args:
            project_path: Project root directory
            threshold: Score threshold for filtering
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        self.project_path = Path(project_path)
        self.check_interval = check_interval

        # Initialize components
        self.storage = StorageManager(project_path)
        self.monitor = FileMonitor(self.storage)
        self.scorer = IncrementalScorer(self.storage, threshold=threshold)
        self.results_gen = ResultsGenerator(self.storage)

    def process_new_files(self) -> bool:
        """
        Check for new files and score them.

        Returns:
            bool: True if new files were processed
        """
        # Check for new files
        new_resume_ids, new_opp_ids = self.monitor.check_for_new_files()

        if not new_resume_ids and not new_opp_ids:
            logger.info("No new files to process")
            return False

        # Process new resumes
        if new_resume_ids:
            logger.info(f"\n📄 Processing {len(new_resume_ids)} new resumes...")
            for resume_id in new_resume_ids:
                try:
                    logger.info(f"   Scoring Resume {resume_id} against all opportunities...")
                    scores = self.scorer.score_resume_for_all_opportunities(resume_id)
                    logger.info(f"   ✓ Resume {resume_id}: Scored against {len(scores)} opportunities")
                except Exception as e:
                    logger.error(f"   ✗ Failed to score Resume {resume_id}: {e}")

        # Process new opportunities
        if new_opp_ids:
            logger.info(f"\n💼 Processing {len(new_opp_ids)} new opportunities...")
            for opp_id in new_opp_ids:
                try:
                    logger.info(f"   Scoring all resumes against Opportunity {opp_id}...")
                    scores = self.scorer.score_all_for_opportunity(opp_id)
                    logger.info(f"   ✓ Opportunity {opp_id}: Scored {len(scores)} resumes")
                except Exception as e:
                    logger.error(f"   ✗ Failed to score Opportunity {opp_id}: {e}")

        # Update metadata
        self.storage.update_metadata()

        # FIXED: Generate reports if ANY new files were added (resumes OR opportunities)
        if new_resume_ids or new_opp_ids:
            logger.info("\n📊 Regenerating all opportunity reports with updated rankings...")
            try:
                self.results_gen.export_all_opportunity_reports()
                logger.info("✓ All reports regenerated successfully")
            except Exception as e:
                logger.error(f"✗ Failed to generate reports: {e}")

        return True

    def run_once(self):
        """Run one check and processing cycle"""
        logger.info("\n" + "=" * 120)
        logger.info(f"🔄 AUTO SCORER - CHECK CYCLE")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 120)

        processed = self.process_new_files()

        if processed:
            # Display updated results
            self.results_gen.display_all_opportunities_summary()

        logger.info("=" * 120)
        logger.info("✓ Check cycle complete")
        logger.info("=" * 120 + "\n")

    def run_continuous(self):
        """Run continuously, checking every check_interval seconds"""
        logger.info("=" * 120)
        logger.info("🤖 AUTO SCORER - CONTINUOUS MODE")
        logger.info("=" * 120)
        logger.info(f"Check interval: {self.check_interval} seconds ({self.check_interval / 60:.1f} minutes)")
        logger.info(f"Resumes folder: {self.monitor.resumes_folder}")
        logger.info(f"Opportunities folder: {self.monitor.opportunities_folder}")
        logger.info("=" * 120)
        logger.info("\nPress Ctrl+C to stop\n")

        try:
            while True:
                self.run_once()

                logger.info(f"⏳ Waiting {self.check_interval} seconds until next check...")
                logger.info(
                    f"   Next check at: {datetime.now().replace(microsecond=0) + __import__('datetime').timedelta(seconds=self.check_interval)}\n")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\n\n" + "=" * 120)
            logger.info("🛑 AUTO SCORER STOPPED")
            logger.info("=" * 120 + "\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Automatic Resume Scorer')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=300, help='Check interval in seconds (default: 300)')
    parser.add_argument('--threshold', type=int, default=70, help='Score threshold (default: 70)')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Initialize auto scorer
    auto_scorer = AutoScorer(
        project_path='.',
        threshold=args.threshold,
        check_interval=args.interval
    )

    if args.once:
        # Run once and exit
        auto_scorer.run_once()
    else:
        # Run continuously
        auto_scorer.run_continuous()


if __name__ == "__main__":
    main()