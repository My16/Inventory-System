from django import forms
from .models import Office

class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['office_name', 'abbreviation', 'location']
