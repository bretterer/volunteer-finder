"""
Main execution script - Run this to process everything
"""

import logging
from pathlib import Path

from storage_manager import StorageManager
from file_readers import ResumeReader
from incremental_scorer import IncrementalScorer
from results_generator import ResultsGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    print("=" * 120)
    print("🚀 RESUME SCORING SYSTEM")
    print("=" * 120)

    # Initialize
    storage = StorageManager('.')
    scorer = IncrementalScorer(storage, threshold=70)
    results_gen = ResultsGenerator(storage)

    # Score everything
    print("\n⏳ Scoring all resumes against all opportunities...\n")
    scorer.score_all_resumes_all_opportunities(force=False)

    # Display results
    results_gen.display_all_opportunities_top_10()
    results_gen.export_all_opportunity_reports()
    results_gen.display_overlap_report()

    print("\n✓ COMPLETE! Check results/opportunity_reports/ for output\n")


if __name__ == "__main__":
    main()