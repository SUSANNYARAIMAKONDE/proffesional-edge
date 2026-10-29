from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30, help_text="Include country code, e.g. +263...")
    country = forms.CharField(max_length=60, initial="Zimbabwe")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")
    accept_terms = forms.BooleanField(label="I accept the Privacy Notice and Terms of Use")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "Passwords do not match.")
            else:
                validate_password(p1)
        return data
