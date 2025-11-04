# accounts/views.py
# accounts/views.py
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import FormView
from .forms import VolunteerRegisterForm, OrgRegisterForm, AdminRegisterForm

class RegisterVolunteerView(FormView):
    template_name = "accounts/register_volunteer.html"
    form_class = VolunteerRegisterForm
    success_url = reverse_lazy("home")  # we’ll add a simple home soon

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class RegisterOrgView(FormView):
    template_name = "accounts/register_org.html"
    form_class = OrgRegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class RegisterAdminView(FormView):
    template_name = "accounts/register_admin.html"
    form_class = AdminRegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
