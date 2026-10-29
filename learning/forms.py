from django import forms
from .models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["text", "file"]
        widgets = {"text": forms.Textarea(attrs={"rows": 6})}

    def clean(self):
        d = super().clean()
        if not d.get("text") and not d.get("file") and not (self.instance and self.instance.file):
            raise forms.ValidationError("Enter a written response or upload a file.")
        return d


class MarkForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["marks", "feedback", "released"]
        widgets = {"feedback": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *a, max_marks=100, **kw):
        super().__init__(*a, **kw)
        self.max_marks = max_marks

    def clean_marks(self):
        m = self.cleaned_data.get("marks")
        if m is not None and (m < 0 or m > self.max_marks):
            raise forms.ValidationError(f"Marks must be between 0 and {self.max_marks}.")
        return m
