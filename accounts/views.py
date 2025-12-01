# accounts/views.py
from functools import wraps
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .forms import VolunteerRegisterForm, OrgRegisterForm, AdminRegisterForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import PasswordResetToken, EmailVerificationToken
from core.email import send_email

User = get_user_model()


def send_verification_email(request, user):
    """Helper function to send verification email to a user."""
    token = EmailVerificationToken.create_for_user(user)
    verify_url = request.build_absolute_uri(f'/accounts/verify-email/confirm/{token.token}/')

    email_body = f"""<p>Hi {user.name()},</p>

<p>Welcome to Volunteer Finder! Please verify your email address to complete your registration.</p>

<table role="presentation" cellspacing="0" cellpadding="0" style="margin: 25px 0;">
    <tr>
        <td style="background-color: #4f46e5; border-radius: 6px;">
            <a href="{verify_url}" target="_blank" style="display: inline-block; padding: 14px 30px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">Verify Email Address</a>
        </td>
    </tr>
</table>

<p>This link will expire in 24 hours.</p>

<p>If you did not create an account, you can safely ignore this email.</p>

<p>Best regards,<br>
The Volunteer Finder Team</p>"""

    send_email(
        subject='Verify Your Email - Volunteer Finder',
        body=email_body,
        recipient_list=[user.email]
    )


def email_verified_required(view_func):
    """Decorator that requires the user to have a verified email."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.email_verified:
            return redirect('verify_email_required')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class RegisterVolunteerView(FormView):
    template_name = "accounts/register_volunteer.html"
    form_class = VolunteerRegisterForm
    success_url = reverse_lazy("verify_email_required")

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
        send_verification_email(self.request, user)
        return super().form_valid(form)


class RegisterOrgView(FormView):
    template_name = "accounts/register_org.html"
    form_class = OrgRegisterForm
    success_url = reverse_lazy("verify_email_required")

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
        send_verification_email(self.request, user)
        return super().form_valid(form)


class RegisterAdminView(FormView):
    template_name = "accounts/register_admin.html"
    form_class = AdminRegisterForm
    success_url = reverse_lazy("verify_email_required")

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
        send_verification_email(self.request, user)
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
        # Check if email is verified first
        if not request.user.email_verified:
            return redirect('verify_email_required')
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
            # Check if email is verified
            if not user.email_verified:
                return redirect('verify_email_required')
            # Redirect based on user type
            if user.user_type == 'volunteer':
                return redirect('volunteer_dashboard')
            elif user.user_type == 'organization':
                return redirect('organization_dashboard')
            elif user.user_type == 'admin':
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def password_reset_request(request):
    """Handle password reset request - ask for email."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            # Always show success message regardless of whether account exists (security)
            messages.success(
                request,
                'If an account with that email exists, you will receive an email with instructions to reset your password.'
            )

            # Check if user exists and send email
            try:
                user = User.objects.get(email=email)
                # Create reset token
                reset_token = PasswordResetToken.create_for_user(user)
                # Build reset URL
                reset_url = request.build_absolute_uri(f'/accounts/password-reset/confirm/{reset_token.token}/')
                # Send email with clickable button
                email_body = f"""<p>Hi {user.name()},</p>

<p>We received a request to reset your password for your Volunteer Finder account.</p>

<table role="presentation" cellspacing="0" cellpadding="0" style="margin: 25px 0;">
    <tr>
        <td style="background-color: #4f46e5; border-radius: 6px;">
            <a href="{reset_url}" target="_blank" style="display: inline-block; padding: 14px 30px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">Reset Your Password</a>
        </td>
    </tr>
</table>

<p>This link will expire in 1 hour.</p>

<p>If you did not request a password reset, you can safely ignore this email. Your password will not be changed.</p>

<p>Best regards,<br>
The Volunteer Finder Team</p>"""
                send_email(
                    subject='Reset Your Password - Volunteer Finder',
                    body=email_body,
                    recipient_list=[user.email]
                )
            except User.DoesNotExist:
                # Don't reveal whether the email exists
                pass

            return redirect('password_reset_request')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Handle password reset confirmation - set new password."""
    if request.user.is_authenticated:
        return redirect('home')

    # Find the token
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'This password reset link is invalid.')
        return redirect('login')

    # Check if token is valid
    if not reset_token.is_valid():
        messages.error(request, 'This password reset link has expired or has already been used.')
        return redirect('login')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            # Update password
            user = reset_token.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()

            # Mark token as used
            reset_token.used = True
            reset_token.save()

            messages.success(request, 'Your password has been reset successfully. You can now log in with your new password.')
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'token': token})


@login_required
def verify_email_required(request):
    """Page shown to users who need to verify their email."""
    # If already verified, redirect to dashboard
    if request.user.email_verified:
        if request.user.user_type == 'volunteer':
            return redirect('volunteer_dashboard')
        elif request.user.user_type == 'organization':
            return redirect('organization_dashboard')
        elif request.user.user_type == 'admin':
            return redirect('admin_dashboard')

    return render(request, 'accounts/verify_email_required.html', {
        'email': request.user.email
    })


@login_required
@require_POST
def resend_verification_email(request):
    """Resend verification email to the current user."""
    if request.user.email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('home')

    send_verification_email(request, request.user)
    messages.success(request, 'A new verification email has been sent. Please check your inbox.')
    return redirect('verify_email_required')


def verify_email_confirm(request, token):
    """Confirm email verification from the link."""
    # Find the token
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'This verification link is invalid.')
        return redirect('login')

    # Check if token is valid
    if not verification_token.is_valid():
        messages.error(request, 'This verification link has expired or has already been used. Please request a new one.')
        if request.user.is_authenticated:
            return redirect('verify_email_required')
        return redirect('login')

    # Mark email as verified
    user = verification_token.user
    user.email_verified = True
    user.save()

    # Mark token as used
    verification_token.used = True
    verification_token.save()

    messages.success(request, 'Your email has been verified successfully!')

    # If user is logged in, redirect to their dashboard
    if request.user.is_authenticated and request.user == user:
        if user.user_type == 'volunteer':
            return redirect('volunteer_dashboard')
        elif user.user_type == 'organization':
            return redirect('organization_dashboard')
        elif user.user_type == 'admin':
            return redirect('admin_dashboard')

    # Otherwise redirect to login
    return redirect('login')
