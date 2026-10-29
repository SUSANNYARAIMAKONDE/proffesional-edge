from django import forms

from learning.models import Assignment, Module, Resource
from .models import Lesson


class DT(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kw):
        super().__init__(format="%Y-%m-%dT%H:%M", **kw)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "start", "duration_minutes", "mode", "location", "status"]
        widgets = {"start": DT()}


class TutorResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["module", "title", "description", "file", "link", "access_level", "published"]

    def __init__(self, *a, course=None, **kw):
        super().__init__(*a, **kw)
        self.fields["module"].queryset = Module.objects.filter(course=course)
        # tutors may not make material fully public without admin approval
        self.fields["access_level"].choices = [c for c in Resource.Access.choices if c[0] != "public"]

    def clean(self):
        d = super().clean()
        if not d.get("file") and not d.get("link"):
            raise forms.ValidationError("Upload a file or give a link.")
        return d


class TutorAssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["title", "instructions", "due_date", "max_marks", "published"]
        widgets = {"due_date": DT(), "instructions": forms.Textarea(attrs={"rows": 5})}
