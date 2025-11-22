# accounts/urls.py
from django.urls import path
from .views import RegisterVolunteerView, RegisterOrgView, RegisterAdminView, logout_view, login_view

urlpatterns = [
    path("register/volunteer/", RegisterVolunteerView.as_view(), name="register_volunteer"),
    path("register/organization/", RegisterOrgView.as_view(), name="register_org"),
    path("register/admin/", RegisterAdminView.as_view(), name="register_admin"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
