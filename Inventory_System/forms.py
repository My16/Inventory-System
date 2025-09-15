from django import forms
from .models import Office, WebsiteUploadRequest, WebsiteUploadAttachment

class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['office_name', 'abbreviation', 'location']

class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class WebsiteUploadRequestForm(forms.ModelForm):
    class Meta:
        model = WebsiteUploadRequest
        fields = ["area_section", "details_of_request", "prepared_by"]
        widgets = {
            "area_section": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your Area/Section"
            }),
            "details_of_request": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Describe your request here..."
            }),
            "prepared_by": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter your name"
            }),
        }


class WebsiteUploadAttachmentForm(forms.ModelForm):
    class Meta:
        model = WebsiteUploadAttachment
        fields = ["file"]
        widgets = {
            "file": MultiFileInput(attrs={
                "class": "form-control",
            }),
        }