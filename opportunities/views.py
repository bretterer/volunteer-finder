from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
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


@login_required
def edit_opportunity(request, pk):
    """
    View for organizations to edit their volunteer opportunities.
    Only the organization that created the opportunity can edit it.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)

    # Check if user owns this opportunity
    if request.user != opportunity.organization:
        messages.error(request, 'You do not have permission to edit this opportunity.')
        return redirect('opportunities:detail', pk=pk)

    if request.method == 'POST':
        form = OpportunityForm(request.POST, instance=opportunity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Opportunity updated successfully!')
            return redirect('opportunities:detail', pk=opportunity.pk)
    else:
        form = OpportunityForm(instance=opportunity)

    return render(request, 'opportunities/edit.html', {
        'form': form,
        'opportunity': opportunity,
    })


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
    volunteer_score = None
    volunteer_application = None

    if request.user.is_authenticated:
        from resumes.models import Resume, ResumeScore

        if request.user == opportunity.organization:
            # Organization viewing their own opportunity - show top candidates
            top_candidates = ResumeScore.objects.filter(
                opportunity=opportunity,
                overall_score__gt=0
            ).select_related('resume', 'resume__user').order_by('-overall_score')[:10]

            # Attach application status to each candidate
            for candidate in top_candidates:
                candidate.application = Application.objects.filter(
                    opportunity=opportunity,
                    volunteer=candidate.resume.user
                ).first()

        elif request.user.user_type == 'volunteer':
            # Volunteer viewing opportunity - show their match score if available
            resume = Resume.objects.filter(user=request.user).first()
            if resume:
                volunteer_score = ResumeScore.objects.filter(
                    resume=resume,
                    opportunity=opportunity
                ).first()

            # Check if volunteer has already applied
            volunteer_application = Application.objects.filter(
                opportunity=opportunity,
                volunteer=request.user
            ).first()

    return render(request, 'opportunities/detail.html', {
        'opportunity': opportunity,
        'top_candidates': top_candidates,
        'volunteer_score': volunteer_score,
        'volunteer_application': volunteer_application,
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

    # Block if application is pending or accepted
    if existing_application and existing_application.status in ['pending', 'accepted']:
        messages.warning(request, "You have already applied to this opportunity.")
        return redirect('opportunities:detail', pk=pk)

    if request.method == 'POST':
        message = request.POST.get('message', '')

        # If withdrawn or rejected, reactivate the existing application
        if existing_application:
            existing_application.status = 'pending'
            existing_application.message = message
            existing_application.save()
            application = existing_application
        else:
            application = Application.objects.create(
                opportunity=opportunity,
                volunteer=request.user,
                message=message
            )
        messages.success(request, "Your application has been submitted successfully!")

        # Send notification email to organization
        org_email = opportunity.organization.email
        org_name = opportunity.organization.organization_profile.organization_name if hasattr(opportunity.organization, 'organization_profile') else opportunity.organization.username
        volunteer_name = request.user.get_full_name() or request.user.username

        if org_email:
            subject = f"New Application for {opportunity.title}"
            email_message = f"""Hello {org_name},

You have received a new volunteer application!

Opportunity: {opportunity.title}
Applicant: {volunteer_name}
Email: {request.user.email}

"""
            if message:
                email_message += f"""Message from applicant:
{message}

"""

            email_message += f"""Log in to your dashboard to review this application.

Best regards,
Volunteer Finder"""

            try:
                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[org_email],
                    fail_silently=False,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send application notification email: {e}")

        return redirect('opportunities:detail', pk=pk)
    
    return render(request, 'opportunities/apply.html', {'opportunity': opportunity})

@login_required
def withdraw_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, volunteer=request.user)
    application.status = 'withdrawn'
    application.save()
    messages.success(request, "Application withdrawn successfully.")
    return redirect('volunteer_dashboard')


@login_required
def invite_volunteer(request, pk, volunteer_id):
    """
    Send an invitation email to a volunteer asking them to apply for an opportunity.
    Only the organization that owns the opportunity can send invitations.
    """
    from accounts.models import User

    opportunity = get_object_or_404(Opportunity, pk=pk)
    volunteer = get_object_or_404(User, id=volunteer_id, user_type='volunteer')

    # Check if user owns this opportunity
    if request.user != opportunity.organization:
        messages.error(request, 'You do not have permission to invite volunteers.')
        return redirect('opportunities:detail', pk=pk)

    # Check if volunteer has already applied
    existing_application = Application.objects.filter(
        opportunity=opportunity,
        volunteer=volunteer
    ).first()

    if existing_application and existing_application.status in ['pending', 'accepted']:
        messages.warning(request, f'{volunteer.username} has already applied to this opportunity.')
        return redirect('opportunities:detail', pk=pk)

    # Send invitation email
    org_name = opportunity.organization.organization_profile.organization_name if hasattr(opportunity.organization, 'organization_profile') else opportunity.organization.username
    volunteer_email = volunteer.email

    if volunteer_email:
        subject = f"You're Invited to Apply: {opportunity.title}"
        email_message = f"""Hello {volunteer.get_full_name() or volunteer.username},

{org_name} thinks you'd be a great fit for their volunteer opportunity!

Opportunity: {opportunity.title}
Location: {opportunity.location}
Hours: {opportunity.hours_required} hours

Description:
{opportunity.description[:500]}{'...' if len(opportunity.description) > 500 else ''}

We encourage you to log in and apply for this opportunity.

Best regards,
Volunteer Finder"""

        try:
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[volunteer_email],
                fail_silently=False,
            )
            messages.success(request, f'Invitation sent to {volunteer.username}!')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send invitation email: {e}")
            messages.error(request, 'Failed to send invitation email. Please try again.')
    else:
        messages.error(request, f'{volunteer.username} does not have an email address on file.')

    return redirect('opportunities:detail', pk=pk)


@login_required
def review_application(request, application_id):
    """
    View for organizations to review a volunteer application.
    Shows application details and allows accept/reject with feedback.
    """
    application = get_object_or_404(Application, id=application_id)

    # Check if user is the organization that owns this opportunity
    if request.user != application.opportunity.organization:
        messages.error(request, 'You do not have permission to review this application.')
        return redirect('organization_dashboard')

    # Get volunteer's resume and score if available
    volunteer_resume = None
    resume_score = None
    try:
        from resumes.models import Resume, ResumeScore
        volunteer_resume = Resume.objects.filter(user=application.volunteer).first()
        if volunteer_resume:
            resume_score = ResumeScore.objects.filter(
                resume=volunteer_resume,
                opportunity=application.opportunity
            ).first()
    except:
        pass

    # Get volunteer profile if available
    volunteer_profile = None
    try:
        volunteer_profile = application.volunteer.volunteer_profile
    except:
        pass

    if request.method == 'POST':
        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '')

        if action == 'accept':
            application.status = 'accepted'
            application.save()
            messages.success(request, f'Application from {application.volunteer.username} has been accepted!')

            # Send acceptance email to volunteer
            try:
                subject = f'Application Accepted: {application.opportunity.title}'
                email_message = f"""Congratulations!

Your application for "{application.opportunity.title}" has been accepted!

"""
                if feedback:
                    email_message += f"""Message from the organization:
{feedback}

"""
                email_message += """Please log in to your dashboard for next steps.

Best regards,
Volunteer Finder"""

                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.volunteer.email],
                    fail_silently=True,
                )
            except:
                pass

        elif action == 'reject':
            application.status = 'rejected'
            application.save()
            messages.success(request, f'Application from {application.volunteer.username} has been declined.')

            # Send rejection email to volunteer
            try:
                subject = f'Application Update: {application.opportunity.title}'
                email_message = f"""Thank you for your interest in "{application.opportunity.title}".

Unfortunately, we are unable to accept your application at this time.

"""
                if feedback:
                    email_message += f"""Feedback from the organization:
{feedback}

"""
                email_message += """We encourage you to apply for other opportunities that match your skills.

Best regards,
Volunteer Finder"""

                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[application.volunteer.email],
                    fail_silently=True,
                )
            except:
                pass

        return redirect('opportunities:review_application', application_id=application.id)

    return render(request, 'opportunities/review_application.html', {
        'application': application,
        'volunteer_resume': volunteer_resume,
        'resume_score': resume_score,
        'volunteer_profile': volunteer_profile,
    })