"""
Scoring service for resume-opportunity matching using OpenAI.
"""

import os
import json
import logging
from typing import Dict, List, Optional

import openai
from django.conf import settings

from .models import Resume, ResumeScore
from opportunities.models import Opportunity

logger = logging.getLogger(__name__)


class ResumeScoringService:
    """Service to score resumes against opportunities using OpenAI."""

    def __init__(self, model_name: str = None, max_tokens: int = None):
        """
        Initialize scoring service.

        Args:
            model_name: OpenAI model to use (default from settings)
            max_tokens: Max completion tokens (default from settings)
        """
        # Get API key from settings or environment
        self.api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in settings or environment")

        openai.api_key = self.api_key

        self.model_name = model_name or getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = max_tokens or getattr(settings, 'OPENAI_MAX_TOKENS', 2100)

    def score_resume_for_opportunity(
            self,
            resume: Resume,
            opportunity: Opportunity,
            force: bool = False
    ) -> Optional[ResumeScore]:
        """
        Score a single resume against a single opportunity.

        Args:
            resume: Resume instance
            opportunity: Opportunity instance
            force: Force rescore even if already scored

        Returns:
            ResumeScore instance or None if failed
        """
        # Check if already scored
        if not force:
            existing = ResumeScore.objects.filter(
                resume=resume,
                opportunity=opportunity
            ).first()
            if existing:
                logger.info(f"Resume {resume.id} already scored for opportunity {opportunity.id}")
                return existing

        try:
            # Build the prompt
            prompt = self._build_scoring_prompt(resume, opportunity)

            # Call OpenAI
            logger.info(f"Scoring resume {resume.id} for opportunity {opportunity.id}")
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR recruiter analyzing candidate resumes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=0.7
            )

            # Parse response
            result_text = response.choices[0].message.content.strip()
            score_data = self._parse_scoring_response(result_text)

            # Map recommendation
            recommendation_map = {
                'Highly Recommended': 'highly_recommended',
                'Recommended': 'recommended',
                'Consider': 'consider',
                'Not Recommended': 'not_recommended'
            }
            recommendation = recommendation_map.get(
                score_data.get('recommendation', 'Consider'),
                'consider'
            )

            # Create or update score
            score, created = ResumeScore.objects.update_or_create(
                resume=resume,
                opportunity=opportunity,
                defaults={
                    'overall_score': score_data.get('overall', 0),
                    'skills_match': score_data.get('skills_match', 0),
                    'experience_match': score_data.get('experience_match', 0),
                    'education_match': score_data.get('education_match', 0),
                    'grade': score_data.get('grade', 'F'),
                    'recommendation': recommendation,
                    'key_strength': score_data.get('key_strength', ''),
                    'concerns': score_data.get('concerns', ''),
                    'scored_by_model': self.model_name
                }
            )

            action = "Created" if created else "Updated"
            logger.info(
                f"{action} score for resume {resume.id} x opportunity {opportunity.id}: {score.overall_score}/100")

            return score

        except Exception as e:
            logger.error(f"Error scoring resume {resume.id} for opportunity {opportunity.id}: {e}")
            return None

    def score_resume_for_all_opportunities(
            self,
            resume: Resume,
            force: bool = False,
            min_score: int = 65
    ) -> List[ResumeScore]:
        """
        Score a resume against all active opportunities.

        Args:
            resume: Resume instance
            force: Force rescore even if already scored
            min_score: Minimum score threshold

        Returns:
            List of ResumeScore instances
        """
        opportunities = Opportunity.objects.filter(status='active')
        scores = []

        logger.info(f"Scoring resume {resume.id} against {opportunities.count()} opportunities")

        for opportunity in opportunities:
            score = self.score_resume_for_opportunity(resume, opportunity, force=force)
            if score:
                scores.append(score)

        logger.info(f"Completed scoring resume {resume.id}: {len(scores)} scores created")
        return scores

    def score_all_unscored_resumes(self, min_score: int = 65) -> Dict[str, int]:
        """
        Score all resumes that haven't been scored yet.

        Args:
            min_score: Minimum score threshold

        Returns:
            Dictionary with statistics
        """
        stats = {
            'resumes_processed': 0,
            'scores_created': 0,
            'errors': 0
        }

        # Get all resumes
        resumes = Resume.objects.filter(processed=True)
        opportunities = Opportunity.objects.filter(status='active')

        logger.info(f"Checking {resumes.count()} resumes against {opportunities.count()} opportunities")

        for resume in resumes:
            # Check which opportunities need scoring
            existing_scores = ResumeScore.objects.filter(resume=resume).values_list('opportunity_id', flat=True)
            opportunities_to_score = opportunities.exclude(id__in=existing_scores)

            if not opportunities_to_score.exists():
                continue

            logger.info(f"Resume {resume.id}: Scoring against {opportunities_to_score.count()} new opportunities")
            stats['resumes_processed'] += 1

            for opportunity in opportunities_to_score:
                score = self.score_resume_for_opportunity(resume, opportunity)
                if score:
                    stats['scores_created'] += 1
                else:
                    stats['errors'] += 1

        return stats

    def _build_scoring_prompt(self, resume: Resume, opportunity: Opportunity) -> str:
        """
        Build the scoring prompt for OpenAI.

        Args:
            resume: Resume instance
            opportunity: Opportunity instance

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are evaluating a candidate's resume for a volunteer opportunity.

OPPORTUNITY:
Position: {opportunity.title}
Department: {opportunity.location}
Description: {opportunity.description[:500]}
Required Skills: {', '.join(opportunity.required_skills) if opportunity.required_skills else 'Not specified'}
Hours Required: {opportunity.hours_required} per week

CANDIDATE RESUME:
{resume.extracted_text[:2000]}

Please provide a JSON response with the following structure:
{{
    "overall": <score 0-100>,
    "skills_match": <score 0-100>,
    "experience_match": <score 0-100>,
    "education_match": <score 0-100>,
    "grade": "<A+, A, B+, B, C+, C, D, or F>",
    "recommendation": "<Highly Recommended, Recommended, Consider, or Not Recommended>",
    "key_strength": "<brief description>",
    "concerns": "<brief description or empty string>"
}}

Scoring criteria:
- Skills Match: Alignment with required skills
- Experience Match: Relevant volunteer/work experience
- Education Match: Educational background fit
- Overall: Weighted average emphasizing skills and experience

Grade scale: A+ (95-100), A (90-94), B+ (85-89), B (80-84), C+ (75-79), C (70-74), D (65-69), F (0-64)

Respond ONLY with valid JSON. No additional text."""

        return prompt

    def _parse_scoring_response(self, response_text: str) -> Dict:
        """
        Parse OpenAI response into score data.

        Args:
            response_text: Raw response from OpenAI

        Returns:
            Dictionary of score data
        """
        try:
            # Remove markdown code blocks if present
            response_text = response_text.replace('```json', '').replace('```', '').strip()

            # Parse JSON
            data = json.loads(response_text)

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse scoring response: {e}")
            logger.error(f"Response text: {response_text}")

            # Return default values
            return {
                'overall': 0,
                'skills_match': 0,
                'experience_match': 0,
                'education_match': 0,
                'grade': 'F',
                'recommendation': 'Not Recommended',
                'key_strength': 'Error parsing response',
                'concerns': 'Failed to score'
            }