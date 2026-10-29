from django import forms
from .models import Enquiry


class EnquiryForm(forms.ModelForm):
    privacy = forms.BooleanField(label="I agree that Professional Edge may use these details to respond to my enquiry.")
    website = forms.CharField(required=False, widget=forms.HiddenInput)  # honeypot against bots

    class Meta:
        model = Enquiry
        fields = ["name", "email", "phone", "category", "message"]

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
