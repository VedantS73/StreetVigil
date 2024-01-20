# forms.py
from django import forms
from .models import CapturedImage

class CapturedImageForm(forms.ModelForm):
    class Meta:
        model = CapturedImage
        fields = ['category', 'latitude', 'longitude', 'image'] 

