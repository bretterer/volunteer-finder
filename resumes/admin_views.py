"""
Custom admin views for resume matching interface.
"""

from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
import re

from .models import Resume, ResumeScore
from opportunities.models import Opportunity


@method_decorator(staff_member_required, name='dispatch')
class OpportunityMatchingView(View):
    """Custom view for opportunity matching interface."""

    def extract_leader_name(self, opportunity):
        """Extract first organizational leader from opportunity description."""
        # Check if organization username is system_admin (default)
        if opportunity.organization.username == 'system_admin':
            # Try to extract from description
            org_match = re.search(
                r'ORGANIZATIONAL LEADERS?:\s*(.+?)(?:\n\n|REQUIREMENTS|ABOUT)',
                opportunity.description,
                re.IGNORECASE | re.DOTALL
            )
            if org_match:
                leaders_text = org_match.group(1).strip()
                # Extract first leader name
                first_leader = re.search(
                    r'[\\-•*]\s*(?:Prof\.|Dr\.|Professor|Doctor)?\s*([A-Z][a-zA-Z\s\.]+?)(?:\n|$)',
                    leaders_text
                )
                if first_leader:
                    return first_leader.group(1).strip()

        # Otherwise return organization username formatted
        return opportunity.organization.username.replace('_', ' ').title()

    def get(self, request, opportunity_id=None):
        """Display matching interface."""

        # Get all active opportunities
        opportunities = Opportunity.objects.filter(status='active').annotate(
            total_candidates=Count('resume_scores'),
            accepted_count=Count('resume_scores', filter=Q(resume_scores__acceptance_status='accepted'))
        ).order_by('title')

        # Add leader names to opportunities
        opportunities_with_leaders = []
        for opp in opportunities:
            opportunities_with_leaders.append({
                'opportunity': opp,
                'leader_name': self.extract_leader_name(opp)
            })

        # Get selected opportunity (or first one)
        if opportunity_id:
            selected_opportunity = Opportunity.objects.get(id=opportunity_id)
        else:
            selected_opportunity = opportunities.first()

        # Get top candidates for selected opportunity
        top_candidates = []
        if selected_opportunity:
            # Get candidates who haven't been accepted elsewhere (or show with indicator)
            candidates = ResumeScore.objects.filter(
                opportunity=selected_opportunity,
                overall_score__gte=65  # Only show qualified candidates
            ).select_related('resume', 'resume__user').order_by('-overall_score')[:20]

            for score in candidates:
                # Check if candidate has been accepted elsewhere
                other_acceptances = ResumeScore.objects.filter(
                    resume=score.resume,
                    acceptance_status='accepted'
                ).exclude(opportunity=selected_opportunity)

                top_candidates.append({
                    'score': score,
                    'rank': None,  # Will be set below
                    'is_placed': other_acceptances.exists(),
                    'placement_info': other_acceptances.first() if other_acceptances.exists() else None,
                    'is_available': not other_acceptances.exists() or score.acceptance_status != 'pending'
                })

            # Re-rank available candidates
            available_rank = 1
            for candidate in top_candidates:
                if candidate['is_available'] and candidate['score'].acceptance_status == 'pending':
                    candidate['rank'] = available_rank
                    available_rank += 1
                elif candidate['score'].acceptance_status == 'accepted':
                    candidate['rank'] = '✓'
                elif candidate['score'].acceptance_status == 'rejected':
                    candidate['rank'] = '✗'
                elif candidate['score'].acceptance_status == 'waitlist':
                    candidate['rank'] = 'W'

        context = {
            'opportunities_with_leaders': opportunities_with_leaders,
            'opportunities': opportunities,  # Keep for compatibility
            'selected_opportunity': selected_opportunity,
            'selected_leader': self.extract_leader_name(selected_opportunity) if selected_opportunity else '',
            'top_candidates': top_candidates[:10],  # Show top 10
            'title': 'Opportunity Matching Dashboard',
            'site_header': admin.site.site_header,
            'site_title': admin.site.site_title,
            'has_permission': True,
        }

        return render(request, 'admin/resumes/matching_dashboard.html', context)

    def post(self, request, opportunity_id):
        """Handle acceptance/rejection actions."""

        action = request.POST.get('action')
        score_id = request.POST.get('score_id')

        try:
            score = ResumeScore.objects.get(id=score_id)

            if action == 'accept':
                score.acceptance_status = 'accepted'
                score.accepted_at = timezone.now()
                score.accepted_by = request.user
                score.save()
                messages.success(request, f'Accepted {score.resume.user.username} for {score.opportunity.title}')

            elif action == 'reject':
                score.acceptance_status = 'rejected'
                score.save()
                messages.success(request, f'Rejected {score.resume.user.username}')

            elif action == 'waitlist':
                score.acceptance_status = 'waitlist'
                score.save()
                messages.success(request, f'Moved {score.resume.user.username} to waitlist')

            elif action == 'reset':
                score.acceptance_status = 'pending'
                score.accepted_at = None
                score.accepted_by = None
                score.save()
                messages.success(request, f'Reset status for {score.resume.user.username}')

        except ResumeScore.DoesNotExist:
            messages.error(request, 'Score not found')

        return redirect('admin:opportunity-matching', opportunity_id=opportunity_id)