from django import forms
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    """
    Form for volunteers to upload their resume.
    """

    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx,.doc,.txt'
            })
        }
        labels = {
            'file': 'Upload Resume'
        }
        help_texts = {
            'file': 'Accepted formats: PDF, DOCX, DOC, TXT (Max 5MB)'
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (5MB max)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 5MB.')

            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'doc', 'txt']:
                raise forms.ValidationError('Only PDF, DOCX, DOC, and TXT files are allowed.')

        return file