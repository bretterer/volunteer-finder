from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Resume, ResumeScore
from .forms import ResumeUploadForm


@login_required
def upload_resume(request):
    """
    View for volunteers to upload their resume.
    Only accessible to users with user_type='volunteer'.
    """
    if request.user.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can upload resumes.')
        return redirect('home')

    existing_resume = Resume.objects.filter(user=request.user).first()

    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # If updating, delete old resume and its scores first
                    if existing_resume:
                        # Delete all scores for old resume
                        ResumeScore.objects.filter(resume=existing_resume).delete()
                        # Delete the old resume
                        existing_resume.delete()

                    # Create new resume
                    resume = form.save(commit=False)
                    resume.user = request.user
                    resume.original_filename = request.FILES['file'].name
                    resume.file_size = request.FILES['file'].size
                    resume.extracted_text = ''  # Will be extracted on save
                    resume.save()

                messages.success(request,
                                 'Resume uploaded successfully! It is now being scored against all opportunities.')
                return redirect('resumes:my_resume')

            except Exception as e:
                messages.error(request, f'Error uploading resume: {str(e)}')
    else:
        form = ResumeUploadForm()

    return render(request, 'resumes/upload.html', {
        'form': form,
        'existing_resume': existing_resume
    })


@login_required
def my_resume(request):
    """
    View for volunteers to see their resume and match scores.
    """
    if request.user.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can view resumes.')
        return redirect('home')

    resume = Resume.objects.filter(user=request.user).first()
    scores = []

    if resume:
        # Get top matching opportunities for this resume (exclude 0 scores)
        scores = ResumeScore.objects.filter(
            resume=resume,
            overall_score__gt=0  # Only show scores > 0
        ).order_by('-overall_score')[:20]

    return render(request, 'resumes/my_resume.html', {
        'resume': resume,
        'scores': scores
    })


@login_required
def delete_resume(request):
    """
    View for volunteers to delete their resume.
    """
    if request.user.user_type != 'volunteer':
        messages.error(request, 'Only volunteers can delete resumes.')
        return redirect('home')

    try:
        with transaction.atomic():
            resume = Resume.objects.filter(user=request.user).first()

            if resume:
                # First delete all scores for this resume
                scores_deleted = ResumeScore.objects.filter(resume=resume).delete()
                # Then delete the resume
                resume.delete()
                messages.success(request, 'Resume and all associated scores deleted successfully.')
            else:
                messages.info(request, 'No resume to delete.')

    except Exception as e:
        messages.error(request, f'Error deleting resume: {str(e)}')

    return redirect('resumes:upload')