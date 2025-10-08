from django import forms
from .models import Opportunity

class OpportunityForm(forms.ModelForm):
    """
    Form for creating and editing volunteer opportunities.
    """
    # Custom widget for required_skills (comma-separated input)
    skills_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Python, Teaching, Event Planning (comma-separated)'
        }),
        help_text='Enter skills separated by commas'
    )

    class Meta:
        model = Opportunity
        fields = [
            'title',
            'description',
            'location',
            'start_date',
            'end_date',
            'hours_required',
            'spots_available',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Community Garden Volunteer'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the volunteer opportunity, responsibilities, and expectations...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 123 Main St, Dearborn, MI'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hours_required': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10'
            }),
            'spots_available': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '5'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing opportunity, populate skills field
        if self.instance.pk and self.instance.required_skills:
            self.fields['skills_input'].initial = ', '.join(self.instance.required_skills)

    def clean_skills_input(self):
        """Convert comma-separated skills into a list"""
        skills_str = self.cleaned_data.get('skills_input', '')
        if skills_str:
            # Split by comma, strip whitespace, and filter empty strings
            skills = [skill.strip() for skill in skills_str.split(',') if skill.strip()]
            return skills
        return []

    def save(self, commit=True):
        """Save the form and update required_skills from skills_input"""
        opportunity = super().save(commit=False)
        opportunity.required_skills = self.cleaned_data.get('skills_input', [])
        if commit:
            opportunity.save()
        return opportunity
