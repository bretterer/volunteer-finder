# accounts/urls.py
from django.urls import path
from .views import (
    RegisterVolunteerView, RegisterOrgView, RegisterAdminView,
    logout_view, login_view, password_reset_request, password_reset_confirm,
    verify_email_required, resend_verification_email, verify_email_confirm
)

urlpatterns = [
    path("register/volunteer/", RegisterVolunteerView.as_view(), name="register_volunteer"),
    path("register/organization/", RegisterOrgView.as_view(), name="register_org"),
    path("register/admin/", RegisterAdminView.as_view(), name="register_admin"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("password-reset/", password_reset_request, name="password_reset_request"),
    path("password-reset/confirm/<str:token>/", password_reset_confirm, name="password_reset_confirm"),
    path("verify-email/", verify_email_required, name="verify_email_required"),
    path("verify-email/resend/", resend_verification_email, name="resend_verification_email"),
    path("verify-email/confirm/<str:token>/", verify_email_confirm, name="verify_email_confirm"),
]
