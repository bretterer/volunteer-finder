from typing import List, Dict, Optional
import logging
from pathlib import Path
import json
from datetime import datetime

from storage_manager import StorageManager

logger = logging.getLogger(__name__)


class ResultsGenerator:
    """Generate formatted results tables for opportunity managers"""

    def __init__(self, storage: StorageManager):
        """Initialize results generator"""
        self.storage = storage

    def display_top_candidates(self, opp_id: int, candidates: List[Dict], n: int = 10) -> None:
        """
        Display top N candidates table for a specific opportunity.

        Args:
            opp_id: Opportunity sequence ID
            candidates: List of candidate score dicts
            n: Number to display (default: 10)
        """
        # Get opportunity info
        opportunity = self.storage.get_opportunity(opp_id)
        if not opportunity:
            print(f"Opportunity {opp_id} not found")
            return

        # Header
        print("=" * 120)
        print("📋 TOP 10 CANDIDATES - COMPARISON TABLE")
        print("=" * 120)
        print(f"Position: {opportunity['position']}")
        print(f"Opportunity ID: {opp_id} | File: {opportunity['filename']}\n")

        # Table header
        print(f"{'Rank':<6}{'Candidate':<30}{'Score':<10}{'Grade':<8}{'Recommendation':<18}{'Key Strength':<50}")
        print("─" * 120)

        # Show top N candidates
        display_count = min(len(candidates), n)
        for i, candidate in enumerate(candidates[:display_count], 1):
            name = candidate['filename'][:28]
            score = f"{candidate['overall']}/100"
            grade = candidate['grade'].split()[0]  # Remove any extra text
            rec = candidate['recommendation'][:15]
            strength = candidate.get('key_strength', 'N/A')[:47]
            if len(strength) > 47:
                strength += "..."

            print(f"{i:<6}{name:<30}{score:<10}{grade:<8}{rec:<18}{strength:<50}")

        print("=" * 120)

        # Summary stats
        if candidates:
            avg_score = sum(c['overall'] for c in candidates[:display_count]) / display_count
            print(f"\n📊 Statistics:")
            print(f"   Total Candidates Scored: {len(candidates)}")
            print(f"   Average Score (Top {display_count}): {avg_score:.1f}/100")
            print(f"   Highest Score: {candidates[0]['overall']}/100")
            if display_count == n and len(candidates) >= n:
                print(f"   {n}th Place Score: {candidates[n - 1]['overall']}/100")

        print("=" * 120 + "\n")

    def display_all_opportunities_top_10(self) -> None:
        """
        Display top 10 candidates for EACH opportunity.
        This is what opportunity managers will see.
        """
        all_opps = self.storage.get_all_opportunities()

        if not all_opps:
            print("No opportunities found in database")
            return

        print("\n" + "=" * 120)
        print("🎯 ALL OPPORTUNITIES - TOP 10 CANDIDATES PER OPPORTUNITY")
        print("=" * 120)
        print(f"Total Opportunities: {len(all_opps)}\n")

        for opp_id in sorted(all_opps.keys()):
            # Get top 10 for this opportunity
            scores = self.storage.get_opportunity_scores(opp_id)

            if not scores:
                print(f"\n⚠️  Opportunity {opp_id}: No scores yet")
                continue

            # Convert to list with resume data
            candidates = []
            for resume_id, score_data in scores.items():
                resume = self.storage.get_resume(resume_id)
                if resume:
                    candidates.append({
                        **score_data,
                        'resume_id': resume_id,
                        'filename': resume['filename']
                    })

            # Sort by overall score
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x.get('overall', 0),
                reverse=True
            )

            # Display top 10
            self.display_top_candidates(opp_id, sorted_candidates, n=10)

    def generate_opportunity_report(self, opp_id: int) -> Dict:
        """
        Generate complete report for a single opportunity.

        Args:
            opp_id: Opportunity sequence ID

        Returns:
            Dict containing full report data
        """
        opportunity = self.storage.get_opportunity(opp_id)
        if not opportunity:
            return {'error': f'Opportunity {opp_id} not found'}

        scores = self.storage.get_opportunity_scores(opp_id)

        # Build candidate list
        candidates = []
        for resume_id, score_data in scores.items():
            resume = self.storage.get_resume(resume_id)
            if resume:
                candidates.append({
                    'resume_id': resume_id,
                    'filename': resume['filename'],
                    'email': resume.get('email'),
                    'phone': resume.get('phone'),
                    'overall_score': score_data.get('overall'),
                    'skills_match': score_data.get('skills_match'),
                    'experience_match': score_data.get('experience_match'),
                    'education_match': score_data.get('education_match'),
                    'grade': score_data.get('grade'),
                    'recommendation': score_data.get('recommendation'),
                    'key_strength': score_data.get('key_strength'),
                    'concerns': score_data.get('concerns', 'None')
                })

        # Sort by score
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get('overall_score', 0),
            reverse=True
        )

        # Generate report
        report = {
            'opportunity': {
                'id': opp_id,
                'position': opportunity['position'],
                'filename': opportunity['filename'],
                'registered_at': opportunity.get('registered_at')
            },
            'statistics': {
                'total_candidates': len(candidates),
                'average_score': sum(c['overall_score'] for c in candidates) / len(candidates) if candidates else 0,
                'highest_score': sorted_candidates[0]['overall_score'] if sorted_candidates else 0,
                'lowest_score': sorted_candidates[-1]['overall_score'] if sorted_candidates else 0
            },
            'top_10_candidates': sorted_candidates[:10],
            'all_candidates': sorted_candidates,
            'generated_at': datetime.now().isoformat()
        }

        return report

    def export_all_opportunity_reports(self, output_dir: str = 'results/opportunity_reports') -> None:
        """
        Export separate report for each opportunity manager.

        Args:
            output_dir: Directory to save reports
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_opps = self.storage.get_all_opportunities()

        print("=" * 120)
        print("📄 EXPORTING OPPORTUNITY REPORTS")
        print("=" * 120)

        for opp_id, opp_data in all_opps.items():
            # Generate report
            report = self.generate_opportunity_report(opp_id)

            if 'error' in report:
                print(f"✗ {report['error']}")
                continue

            # Clean position name for filename (remove invalid characters)
            position_clean = self._sanitize_filename(opp_data['position'])

            # Create filename
            filename = f"opportunity_{opp_id}_{position_clean}.json"
            filepath = output_path / filename

            # Save report
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print(f"✓ Exported: {filepath}")
            print(f"   Position: {opp_data['position']}")
            print(f"   Total Candidates: {report['statistics']['total_candidates']}")
            print(f"   Avg Score: {report['statistics']['average_score']:.1f}/100\n")

        print("=" * 120)
        print(f"✓ All reports exported to: {output_path}")
        print("=" * 120 + "\n")

    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Clean text to make it safe for filenames.

        Args:
            text: Text to sanitize
            max_length: Maximum length of output (default: 50)

        Returns:
            Sanitized filename-safe string
        """
        import re

        # Remove or replace invalid filename characters
        # Windows invalid chars: < > : " / \ | ? * and control chars
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')

        # Replace invalid characters with underscore
        text = re.sub(r'[<>:"/\\|?*]', '_', text)

        # Replace multiple spaces/underscores with single underscore
        text = re.sub(r'[\s_]+', '_', text)

        # Remove leading/trailing underscores
        text = text.strip('_')

        # Limit length
        if len(text) > max_length:
            text = text[:max_length]

        # Ensure it's not empty
        if not text:
            text = "unnamed"

        return text

    def check_candidate_overlap(self) -> Dict:
        """
        Check which candidates appear in top 10 for multiple opportunities.

        Returns:
            Dict with overlap statistics
        """
        all_opps = self.storage.get_all_opportunities()

        # Track which candidates are in which top 10 lists
        candidate_appearances = {}  # resume_id -> list of opp_ids

        for opp_id in all_opps.keys():
            scores = self.storage.get_opportunity_scores(opp_id)

            # Get top 10
            candidates = []
            for resume_id, score_data in scores.items():
                candidates.append({
                    'resume_id': resume_id,
                    'overall': score_data.get('overall', 0)
                })

            sorted_candidates = sorted(
                candidates,
                key=lambda x: x['overall'],
                reverse=True
            )[:10]

            # Track appearances
            for candidate in sorted_candidates:
                resume_id = candidate['resume_id']
                if resume_id not in candidate_appearances:
                    candidate_appearances[resume_id] = []
                candidate_appearances[resume_id].append(opp_id)

        # Find overlaps
        overlapping = {
            resume_id: opps
            for resume_id, opps in candidate_appearances.items()
            if len(opps) > 1
        }

        return {
            'total_unique_in_top_10': len(candidate_appearances),
            'candidates_in_multiple_top_10': len(overlapping),
            'overlap_details': overlapping
        }

    def display_overlap_report(self) -> None:
        """Display report of candidates appearing in multiple top 10 lists"""
        overlap_data = self.check_candidate_overlap()

        print("=" * 120)
        print("🔄 CANDIDATE OVERLAP ANALYSIS")
        print("=" * 120)
        print(f"Total unique candidates in any top 10: {overlap_data['total_unique_in_top_10']}")
        print(f"Candidates in multiple top 10 lists: {overlap_data['candidates_in_multiple_top_10']}\n")

        if overlap_data['overlap_details']:
            print("Candidates appearing in multiple opportunities:\n")

            for resume_id, opp_ids in overlap_data['overlap_details'].items():
                resume = self.storage.get_resume(resume_id)
                if resume:
                    print(f"📄 {resume['filename']} (Resume ID: {resume_id})")
                    print(f"   Appears in {len(opp_ids)} opportunity top 10 lists:")

                    for opp_id in opp_ids:
                        opp = self.storage.get_opportunity(opp_id)
                        score = self.storage.get_score(resume_id, opp_id)
                        if opp and score:
                            print(f"      • {opp['position'][:50]} - Score: {score['overall']}/100")
                    print()
        else:
            print("✓ No overlap - all candidates are unique to their top 10 list")

        print("=" * 120 + "\n")

    def display_all_opportunities_summary(self) -> None:
        """Display summary of all opportunities and their scoring status"""
        all_opps = self.storage.get_all_opportunities()

        if not all_opps:
            print("No opportunities found in database")
            return

        print("=" * 120)
        print("📊 ALL OPPORTUNITIES SUMMARY")
        print("=" * 120)

        for opp_id, opp_data in all_opps.items():
            scores = self.storage.get_opportunity_scores(opp_id)

            print(f"\n💼 {opp_data['position']}")
            print(f"   ID: {opp_id} | File: {opp_data['filename']}")
            print(f"   Total Candidates Scored: {len(scores)}")

            if scores:
                all_scores = [score_data['overall'] for score_data in scores.values()]
                top_score = max(all_scores)
                avg_score = sum(all_scores) / len(all_scores)

                print(f"   Top Score: {top_score}/100 | Average: {avg_score:.1f}/100")
            else:
                print("   ⚠️  No scores yet")

        print("=" * 120 + "\n")