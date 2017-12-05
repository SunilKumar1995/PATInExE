from django import forms
from django.core import validators
class FormName(forms.Form):
    emailinput = forms.CharField(widget=forms.Textarea(attrs={'class':'textarea','placeholder':'What is there in your new email?','rows':'15', 'cols':'50'}))
