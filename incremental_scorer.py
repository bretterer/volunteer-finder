import json
from typing import Dict, List, Optional
import logging
from openai import OpenAI

from config import Config, ConfigurationError
from storage_manager import StorageManager, StorageError

logger = logging.getLogger(__name__)


class ScoringError(Exception):
    """Custom exception for scoring errors"""
    pass


class IncrementalScorer:
    """Scores resumes against opportunities using OpenAI, with smart caching"""

    def __init__(self, storage: StorageManager, threshold: int = 70):
        """
        Initialize scorer.

        Args:
            storage: StorageManager instance
            threshold: Score threshold for filtering (default: 70)
        """
        self.storage = storage
        self.threshold = threshold

        # Initialize OpenAI client
        try:
            self.client = Config.get_openai_client()
        except ConfigurationError as e:
            raise ScoringError(f"Failed to initialize OpenAI client: {e}") from e

    def score_resume_for_opportunity(
            self,
            resume_id: int,
            opp_id: int,
            force: bool = False
    ) -> Optional[Dict]:
        """
        Score a single resume against an opportunity.

        Args:
            resume_id: Resume sequence ID
            opp_id: Opportunity sequence ID
            force: If True, rescore even if already scored

        Returns:
            Dict with score data, or None if skipped
        """
        # Check if already scored (unless force=True)
        if not force and not self.storage.resume_needs_scoring(resume_id, opp_id):
            logger.info(f"Resume {resume_id} already scored for Opportunity {opp_id}, skipping")
            return self.storage.get_score(resume_id, opp_id)

        # Get resume and opportunity data
        resume = self.storage.get_resume(resume_id)
        opportunity = self.storage.get_opportunity(opp_id)

        if not resume or not opportunity:
            raise ScoringError(f"Resume {resume_id} or Opportunity {opp_id} not found")

        # Call OpenAI to score
        try:
            score_data = self._call_openai_scoring(resume['text'], opportunity['text'])

            # Add metadata
            score_data['resume_id'] = resume_id
            score_data['opp_id'] = opp_id
            score_data['filename'] = resume['filename']

            # Save to storage
            self.storage.save_score(resume_id, opp_id, score_data)

            logger.info(
                f"Scored Resume {resume_id} x Opportunity {opp_id} = {score_data['overall']}/100"
            )

            return score_data

        except Exception as e:
            raise ScoringError(
                f"Failed to score Resume {resume_id} x Opportunity {opp_id}: {str(e)}"
            ) from e

    def _call_openai_scoring(self, resume_text: str, job_description: str) -> Dict:
        """
        Call OpenAI API to score resume against job description.

        Args:
            resume_text: Resume text
            job_description: Job description text

        Returns:
            Dict with scoring results
        """
        prompt = f"""You are an expert recruiter. Score this resume against the job description.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Provide a score from 0-100 (integers only, no decimals) and analysis in this EXACT JSON format:
{{
    "overall": <integer 0-100>,
    "skills_match": <integer 0-100>,
    "experience_match": <integer 0-100>,
    "education_match": <integer 0-100>,
    "grade": "<A+, A, B+, B, C+, C, D, or F>",
    "recommendation": "<Highly Recommended, Recommended, Consider, or Not Recommended>",
    "key_strength": "<one sentence describing main strength>",
    "concerns": "<one sentence describing main concern or 'None'>"
}}

IMPORTANT: 
- Respond ONLY with valid JSON
- Use integer scores only (no floats like 85.5)
- Do not include any text outside the JSON
- Do not use markdown code blocks"""

        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=Config.MAX_COMPLETION_TOKENS,
                temperature=Config.TEMPERATURE
            )

            response_text = response.choices[0].message.content.strip()

            # Remove markdown if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            # Parse JSON
            score_data = json.loads(response_text.strip())

            # Validate required fields
            required_fields = ['overall', 'skills_match', 'experience_match',
                               'grade', 'recommendation', 'key_strength']
            for field in required_fields:
                if field not in score_data:
                    raise ValueError(f"Missing required field: {field}")

            # Ensure integers
            score_data['overall'] = int(score_data['overall'])
            score_data['skills_match'] = int(score_data['skills_match'])
            score_data['experience_match'] = int(score_data['experience_match'])
            score_data['education_match'] = int(score_data.get('education_match', 50))

            return score_data

        except json.JSONDecodeError as e:
            raise ScoringError(f"Failed to parse OpenAI response as JSON: {e}") from e
        except Exception as e:
            raise ScoringError(f"OpenAI API call failed: {e}") from e

    def score_all_for_opportunity(self, opp_id: int, force: bool = False) -> List[Dict]:
        """
        Score ALL resumes for a specific opportunity.

        Args:
            opp_id: Opportunity sequence ID
            force: If True, rescore everything

        Returns:
            List of score data dicts
        """
        all_resumes = self.storage.get_all_resumes()
        scores = []

        logger.info(f"Scoring {len(all_resumes)} resumes for Opportunity {opp_id}")

        for idx, resume_id in enumerate(all_resumes.keys(), 1):
            try:
                # Check threshold rule: if already scored below threshold, skip
                if not force:
                    existing_score = self.storage.get_score(resume_id, opp_id)
                    if existing_score and existing_score.get('overall', 0) < self.threshold:
                        logger.info(
                            f"Resume {resume_id} previously scored {existing_score['overall']} "
                            f"(below threshold {self.threshold}), skipping"
                        )
                        scores.append(existing_score)
                        continue

                score_data = self.score_resume_for_opportunity(resume_id, opp_id, force)
                if score_data:
                    scores.append(score_data)

                # Progress update
                if idx % 5 == 0:
                    logger.info(f"Progress: {idx}/{len(all_resumes)} resumes scored")

            except ScoringError as e:
                logger.error(f"Failed to score resume {resume_id}: {e}")
                continue

        logger.info(f"Completed scoring: {len(scores)} resumes scored")
        return scores

    def score_resume_for_all_opportunities(self, resume_id: int, force: bool = False) -> List[Dict]:
        """
        Score a single resume against ALL opportunities.

        Args:
            resume_id: Resume sequence ID
            force: If True, rescore everything

        Returns:
            List of score data dicts
        """
        all_opps = self.storage.get_all_opportunities()
        scores = []

        logger.info(f"Scoring Resume {resume_id} against {len(all_opps)} opportunities")

        for opp_id in all_opps.keys():
            try:
                score_data = self.score_resume_for_opportunity(resume_id, opp_id, force)
                if score_data:
                    scores.append(score_data)

            except ScoringError as e:
                logger.error(f"Failed to score for opportunity {opp_id}: {e}")
                continue

        logger.info(f"Completed scoring: {len(scores)} opportunities scored")
        return scores

    def get_top_n_for_opportunity(self, opp_id: int, n: int = 10) -> List[Dict]:
        """
        Get top N candidates for an opportunity.

        Args:
            opp_id: Opportunity sequence ID
            n: Number of top candidates (default: 10)

        Returns:
            List of top N score dicts, sorted by overall score
        """
        scores = self.storage.get_opportunity_scores(opp_id)

        if not scores:
            logger.warning(f"No scores found for Opportunity {opp_id}")
            return []

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

        # Sort by overall score (descending)
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get('overall', 0),
            reverse=True
        )

        return sorted_candidates[:n]

    def score_all_resumes_all_opportunities(self, force: bool = False) -> Dict[int, List[Dict]]:
        """
        Score ALL resumes against ALL opportunities.
        This is the main function to run for complete scoring.

        Args:
            force: If True, rescore everything even if already scored

        Returns:
            Dict mapping opportunity IDs to lists of all scores
        """
        all_resumes = self.storage.get_all_resumes()
        all_opps = self.storage.get_all_opportunities()

        total_pairs = len(all_resumes) * len(all_opps)
        completed = 0
        skipped = 0

        logger.info("=" * 80)
        logger.info(f"Starting complete scoring: {len(all_resumes)} resumes x {len(all_opps)} opportunities")
        logger.info(f"Total scoring pairs: {total_pairs}")
        logger.info("=" * 80)

        results_by_opp = {opp_id: [] for opp_id in all_opps.keys()}

        for opp_id, opp_data in all_opps.items():
            logger.info(f"\n📋 Scoring for: {opp_data['position']} (ID: {opp_id})")
            logger.info(f"   Processing {len(all_resumes)} resumes...")

            for idx, resume_id in enumerate(all_resumes.keys(), 1):
                try:
                    # Check if needs scoring
                    if not force:
                        existing_score = self.storage.get_score(resume_id, opp_id)

                        # Skip if already scored and below threshold
                        if existing_score:
                            if existing_score.get('overall', 0) < self.threshold:
                                logger.debug(
                                    f"   Resume {resume_id}: Already scored {existing_score['overall']} "
                                    f"(below threshold), skipping"
                                )
                                results_by_opp[opp_id].append(existing_score)
                                skipped += 1
                                completed += 1
                                continue
                            else:
                                # Already scored above threshold, use existing
                                logger.debug(f"   Resume {resume_id}: Using existing score {existing_score['overall']}")
                                results_by_opp[opp_id].append(existing_score)
                                skipped += 1
                                completed += 1
                                continue

                    # Score the resume
                    score_data = self.score_resume_for_opportunity(resume_id, opp_id, force)
                    if score_data:
                        results_by_opp[opp_id].append(score_data)

                    completed += 1

                    # Progress update every 5 resumes
                    if idx % 5 == 0:
                        progress = (completed / total_pairs) * 100
                        logger.info(
                            f"   Progress: {idx}/{len(all_resumes)} resumes | Overall: {completed}/{total_pairs} ({progress:.1f}%)")

                except ScoringError as e:
                    logger.error(f"   ✗ Failed to score Resume {resume_id}: {e}")
                    completed += 1
                    continue

        logger.info("\n" + "=" * 80)
        logger.info("✓ COMPLETE SCORING FINISHED")
        logger.info("=" * 80)
        logger.info(f"Total pairs processed: {completed}/{total_pairs}")
        logger.info(f"New scores generated: {completed - skipped}")
        logger.info(f"Existing scores used: {skipped}")
        logger.info("=" * 80)

        return results_by_opp