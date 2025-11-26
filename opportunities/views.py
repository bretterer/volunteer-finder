from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Opportunity, Application
from .forms import OpportunityForm


@login_required
def create_opportunity(request):
    """
    View for organizations to create new volunteer opportunities.
    Only accessible to users with user_type='organization'.
    """
    # Check if user is an organization
    if request.user.user_type != 'organization':
        messages.error(request, 'Only organizations can create opportunities.')
        return redirect('opportunities:list')

    if request.method == 'POST':
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.organization = request.user
            opportunity.save()
            messages.success(request, 'Opportunity created successfully!')
            return redirect('opportunities:detail', pk=opportunity.pk)
    else:
        form = OpportunityForm()

    return render(request, 'opportunities/create.html', {'form': form})


def list_opportunities(request):
    """
    View to list all active volunteer opportunities.
    Accessible to all users (even non-logged-in).
    Includes top 5 matches for logged-in volunteers with resumes.
    """
    opportunities = Opportunity.objects.filter(status='active').order_by('-created_at')

    # Get top 5 matches for logged-in volunteers
    top_matches = []
    has_resume = False

    if request.user.is_authenticated and hasattr(request.user, 'user_type') and request.user.user_type == 'volunteer':
        # Check if user has a resume
        from resumes.models import Resume, ResumeScore
        resume = Resume.objects.filter(user=request.user).first()

        if resume:
            has_resume = True
            # Get top 5 matching opportunities
            top_matches = ResumeScore.objects.filter(
                resume=resume,
                opportunity__status='active'
            ).select_related('opportunity').order_by('-overall_score')[:5]

    return render(request, 'opportunities/list.html', {
        'opportunities': opportunities,
        'top_matches': top_matches,
        'has_resume': has_resume,
    })


def opportunity_detail(request, pk):
    """
    View to show details of a specific opportunity.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    # Get top 10 candidates for organizations viewing their own opportunities
    top_candidates = []
    if request.user.is_authenticated and request.user == opportunity.organization:
        from resumes.models import ResumeScore
        top_candidates = ResumeScore.objects.filter(
            opportunity=opportunity,
            overall_score__gt=0
        ).select_related('resume', 'resume__user').order_by('-overall_score')[:10]

    return render(request, 'opportunities/detail.html', {
        'opportunity': opportunity,
        'top_candidates': top_candidates,
    })


@login_required
def update_candidate_status(request, pk, score_id, status):
    """
    Update a candidate's acceptance status for an opportunity.
    Only the organization owner can do this.
    """
    from resumes.models import ResumeScore
    from django.utils import timezone

    opportunity = get_object_or_404(Opportunity, pk=pk)

    # Check if user owns this opportunity
    if request.user != opportunity.organization:
        messages.error(request, 'You do not have permission to update candidates.')
        return redirect('opportunities:detail', pk=pk)

    # Get the score and update status
    score = get_object_or_404(ResumeScore, id=score_id, opportunity=opportunity)

    if status in ['accepted', 'rejected', 'waitlist', 'pending']:
        score.acceptance_status = status
        if status == 'accepted':
            score.accepted_at = timezone.now()
            score.accepted_by = request.user
        score.save()
        messages.success(request, f'Candidate status updated to {status}.')
    else:
        messages.error(request, 'Invalid status.')

    return redirect('opportunities:detail', pk=pk)

@login_required
def apply_to_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, id=pk)
    
    # Check if already applied
    existing_application = Application.objects.filter(
        opportunity=opportunity,
        volunteer=request.user
    ).first()
    
    if existing_application:
        messages.warning(request, "You have already applied to this opportunity.")
        return redirect('opportunities:detail', pk=pk)
    
    if request.method == 'POST':
        message = request.POST.get('message', '')
        application = Application.objects.create(
            opportunity=opportunity,
            volunteer=request.user,
            message=message
        )
        messages.success(request, "Your application has been submitted!")
        
        # TODO: Send notification email to organization
        # from notifications.utils import send_application_notification
        # send_application_notification(application)
        
        return redirect('opportunities:detail', pk=pk)
    
    return render(request, 'opportunities/apply.html', {'opportunity': opportunity})

@login_required
def my_applications(request):
    applications = Application.objects.filter(volunteer=request.user)
    return render(request, 'opportunities/my_applications.html', {'applications': applications})

@login_required
def withdraw_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, volunteer=request.user)
    application.status = 'withdrawn'
    application.save()
    messages.success(request, "Application withdrawn successfully.")
    return redirect('my_applications')