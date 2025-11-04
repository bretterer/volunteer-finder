# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import VolunteerProfile, OrganizationProfile

User = get_user_model()


class BaseRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name", "phone")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (user.email or "").lower()
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class VolunteerRegisterForm(BaseRegisterForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "volunteer"
        if commit:
            user.save()
            # create minimal profile row
            VolunteerProfile.objects.get_or_create(user=user)
        return user


class OrgRegisterForm(BaseRegisterForm):
    organization_name = forms.CharField(max_length=255, required=True)
    contact_person = forms.CharField(max_length=255, required=True)
    website = forms.URLField(required=False)

    class Meta(BaseRegisterForm.Meta):
        fields = BaseRegisterForm.Meta.fields + ("organization_name", "contact_person", "website")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "organization"
        if commit:
            user.save()
            OrganizationProfile.objects.get_or_create(
                user=user,
                defaults={
                    "organization_name": self.cleaned_data["organization_name"],
                    "contact_person": self.cleaned_data["contact_person"],
                    "website": self.cleaned_data.get("website") or "",
                },
            )
        return user


class AdminRegisterForm(BaseRegisterForm):
    admin_code = forms.CharField(required=True, help_text="Admin invite code")

    def clean_admin_code(self):
        code = self.cleaned_data["admin_code"]
        # TODO: move to settings/ENV later
        if code != "ADM1N-INV1TE":
            raise ValidationError("Invalid admin code")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = "admin"
        user.is_staff = True
        if commit:
            user.save()
        return user
