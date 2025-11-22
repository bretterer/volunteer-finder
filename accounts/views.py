# accounts/views.py
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .forms import VolunteerRegisterForm, OrgRegisterForm, AdminRegisterForm

class RegisterVolunteerView(FormView):
    template_name = "accounts/register_volunteer.html"
    form_class = VolunteerRegisterForm
    success_url = reverse_lazy("volunteer_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect to appropriate dashboard based on user type
            if request.user.user_type == 'volunteer':
                return redirect('volunteer_dashboard')
            elif request.user.user_type == 'organization':
                return redirect('organization_dashboard')
            elif request.user.user_type == 'admin':
                return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class RegisterOrgView(FormView):
    template_name = "accounts/register_org.html"
    form_class = OrgRegisterForm
    success_url = reverse_lazy("organization_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect to appropriate dashboard based on user type
            if request.user.user_type == 'volunteer':
                return redirect('volunteer_dashboard')
            elif request.user.user_type == 'organization':
                return redirect('organization_dashboard')
            elif request.user.user_type == 'admin':
                return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class RegisterAdminView(FormView):
    template_name = "accounts/register_admin.html"
    form_class = AdminRegisterForm
    success_url = reverse_lazy("admin_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Redirect to appropriate dashboard based on user type
            if request.user.user_type == 'volunteer':
                return redirect('volunteer_dashboard')
            elif request.user.user_type == 'organization':
                return redirect('organization_dashboard')
            elif request.user.user_type == 'admin':
                return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

@require_POST
@login_required
def logout_view(request):
    """Logout view that requires POST request."""
    logout(request)
    return redirect('home')

def login_view(request):
    """Login view for all user types."""
    # Redirect to appropriate dashboard if already logged in
    if request.user.is_authenticated:
        if request.user.user_type == 'volunteer':
            return redirect('volunteer_dashboard')
        elif request.user.user_type == 'organization':
            return redirect('organization_dashboard')
        elif request.user.user_type == 'admin':
            return redirect('admin_dashboard')

    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect based on user type
            if user.user_type == 'volunteer':
                return redirect('volunteer_dashboard')
            elif user.user_type == 'organization':
                return redirect('organization_dashboard')
            elif user.user_type == 'admin':
                return redirect('admin_dashboard')
        else:
            from django.contrib import messages
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')
