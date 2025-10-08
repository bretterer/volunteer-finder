from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Opportunity
from .forms import OpportunityForm

# Create your views here.

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
    """
    opportunities = Opportunity.objects.filter(status='active').order_by('-created_at')
    return render(request, 'opportunities/list.html', {'opportunities': opportunities})


def opportunity_detail(request, pk):
    """
    View to show details of a specific opportunity.
    """
    opportunity = get_object_or_404(Opportunity, pk=pk)
    return render(request, 'opportunities/detail.html', {'opportunity': opportunity})
