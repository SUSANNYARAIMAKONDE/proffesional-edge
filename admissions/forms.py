from django import forms
from .models import Application, ApplicationDocument


class DateInput(forms.DateInput):
    input_type = "date"


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["full_name", "date_of_birth", "guardian_name", "guardian_phone", "guardian_email",
                  "current_school", "level", "subjects", "exam_board", "learning_mode",
                  "timetable_notes", "prior_academic_info"]
        widgets = {"date_of_birth": DateInput(), "subjects": forms.Textarea(attrs={"rows": 3}),
                   "timetable_notes": forms.Textarea(attrs={"rows": 2}),
                   "prior_academic_info": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        data = super().clean()
        dob = data.get("date_of_birth")
        if dob:
            from datetime import date
            t = date.today()
            age = t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))
            if age < 18 and not (data.get("guardian_name") and (data.get("guardian_phone") or data.get("guardian_email"))):
                raise forms.ValidationError("Applicants under 18 need a parent/guardian name and a phone or email.")
        return data


class DocumentForm(forms.ModelForm):
    class Meta:
        model = ApplicationDocument
        fields = ["purpose", "file"]


class DecisionForm(forms.Form):
    ACTIONS = [("under_review", "Mark under review"), ("more_info", "Request more information"),
               ("approved", "Approve"), ("declined", "Decline"), ("on_hold", "Put on hold")]
    action = forms.ChoiceField(choices=ACTIONS)
    approved_programme = forms.CharField(required=False, max_length=200,
                                         help_text="Required when approving, e.g. Cambridge IGCSE English Language 0500")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}),
                           help_text="Shown to the applicant in the notification.")

    def clean(self):
        d = super().clean()
        if d.get("action") == "approved" and not d.get("approved_programme"):
            self.add_error("approved_programme", "Enter the approved programme/subjects.")
        if d.get("action") == "more_info" and not d.get("note"):
            self.add_error("note", "Say what information is missing.")
        return d
