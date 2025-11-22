import logging
from pathlib import Path

from storage_manager import StorageManager
from incremental_scorer import IncrementalScorer, ScoringError
from results_generator import ResultsGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_complete_scoring():
    """Test complete scoring: ALL resumes against ALL opportunities"""

    print("\n" + "=" * 120)
    print("🤖 COMPLETE SCORING SYSTEM TEST")
    print("=" * 120)

    # Initialize components
    try:
        storage = StorageManager('.')
        scorer = IncrementalScorer(storage, threshold=70)
        results_gen = ResultsGenerator(storage)

        print("✓ All components initialized\n")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return

    # Check what we have
    all_resumes = storage.get_all_resumes()
    all_opps = storage.get_all_opportunities()

    if not all_resumes:
        print("⚠️  No resumes found. Run test_storage_manager.py first!")
        return

    if not all_opps:
        print("⚠️  No opportunities found. Run test_storage_manager.py first!")
        return

    print(f"📊 Current Database:")
    print(f"   Resumes: {len(all_resumes)}")
    print(f"   Opportunities: {len(all_opps)}")
    print(f"   Total pairs to score: {len(all_resumes) * len(all_opps)}\n")

    # Step 1: Score everything
    print("=" * 120)
    print("STEP 1: Score All Resumes Against All Opportunities")
    print("=" * 120)

    try:
        print("⏳ Starting complete scoring... (this will take several minutes)\n")

        results = scorer.score_all_resumes_all_opportunities(force=False)

        print("\n✓ Complete scoring finished!")

    except ScoringError as e:
        print(f"✗ Scoring failed: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return

    # Step 2: Display top 10 for each opportunity
    print("\n" + "=" * 120)
    print("STEP 2: Display Top 10 Candidates for Each Opportunity")
    print("=" * 120 + "\n")

    results_gen.display_all_opportunities_top_10()

    # Step 3: Check for overlap
    print("\n" + "=" * 120)
    print("STEP 3: Analyze Candidate Overlap")
    print("=" * 120 + "\n")

    results_gen.display_overlap_report()

    # Step 4: Export reports for opportunity managers
    print("\n" + "=" * 120)
    print("STEP 4: Export Individual Opportunity Reports")
    print("=" * 120 + "\n")

    try:
        results_gen.export_all_opportunity_reports('results/opportunity_reports')
    except Exception as e:
        print(f"✗ Export failed: {e}")

    # Step 5: Check for low-scoring resumes
    print("\n" + "=" * 120)
    print("STEP 5: Identify Low-Scoring Resumes (below 70 on ALL opportunities)")
    print("=" * 120 + "\n")

    low_scorers = storage.get_low_scoring_resumes(threshold=70)

    if low_scorers:
        print(f"Found {len(low_scorers)} resumes scoring below 70 on ALL opportunities:\n")
        for resume in low_scorers:
            print(f"  📄 {resume['filename']} (ID: {resume['resume_id']})")
            if resume['email']:
                print(f"     Email: {resume['email']}")
            if resume['phone']:
                print(f"     Phone: {resume['phone']}")
            print(f"     Max Score: {max(s['overall'] for s in resume['scores'].values())}/100\n")
    else:
        print("✓ No resumes scored below 70 on all opportunities")

    # Final statistics
    print("\n" + "=" * 120)
    print("📊 FINAL STATISTICS")
    print("=" * 120)

    storage.update_metadata()
    metadata = storage.get_metadata()

    print(f"\nSystem Status:")
    print(f"  📄 Total Resumes: {metadata['total_resumes']}")
    print(f"  💼 Total Opportunities: {metadata['total_opportunities']}")
    print(f"  📊 Total Scores: {metadata['total_scores']}")

    if metadata['total_resumes'] > 0 and metadata['total_opportunities'] > 0:
        max_possible = metadata['total_resumes'] * metadata['total_opportunities']
        coverage = (metadata['total_scores'] / max_possible) * 100
        print(f"  📈 Coverage: {coverage:.1f}% ({metadata['total_scores']}/{max_possible})")

    print("\n" + "=" * 120)
    print("✓ TEST COMPLETED SUCCESSFULLY!")
    print("=" * 120)
    print("\n📁 Output Files:")
    print("   • results/opportunity_reports/ - Individual JSON reports for each opportunity")
    print("   • results/*.json - Database files\n")


if __name__ == "__main__":
    test_complete_scoring()