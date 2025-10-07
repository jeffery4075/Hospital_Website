from django import forms
from django.utils import timezone
from .models import CustomUser, Patient, GENDER_CHOICE, BLOOD_GROUP, STAFF_ROLE_CHOICES,PatientVisit,Prescription

class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    dob = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    pincode = forms.CharField(max_length=6)
    phone_number = forms.CharField(max_length=10)

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email"]

    def clean_dob(self):
        dob = self.cleaned_data.get("dob")
        if not dob:
            return dob
        if dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email"]

class PatientEditForm(forms.ModelForm):
    gender = forms.ChoiceField(choices=GENDER_CHOICE)
    dob = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP, required=False)

    class Meta:
        model = Patient
        fields = [
            "gender", "dob", "blood_group",
            "pincode", "phone_number",
            "address", "city", "state", "country",
        ]

    def clean_dob(self):
        dob = self.cleaned_data.get("dob")
        if dob and dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob
    

class StaffCheckInForm(forms.ModelForm):
    class Meta:
        model = PatientVisit
        fields = ["height_cm", "weight_kg", "blood_pressure", "sugar_level", "notes"]
        widgets = {
            "blood_pressure": forms.TextInput(attrs={"placeholder": "120/80"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["medicine_name", "dosage", "frequency", "duration_days", "notes"]
        widgets = {
            "medicine_name": forms.TextInput(attrs={"placeholder": "e.g., Amoxicillin 500 mg"}),
            "dosage": forms.TextInput(attrs={"placeholder": "1 tablet"}),
            "frequency": forms.TextInput(attrs={"placeholder": "Twice daily"}),
            "duration_days": forms.NumberInput(attrs={"min": 1}),
            "notes": forms.Textarea(attrs={"rows": 2, "placeholder": "After food / any caution"}),
        }

    def clean_duration_days(self):
        val = self.cleaned_data.get("duration_days")
        if val is not None and val <= 0:
            raise forms.ValidationError("Duration must be a positive number of days.")
        return val
    
class VisitSymptomsForm(forms.ModelForm):
    class Meta:
        model = PatientVisit
        fields = ["symptoms"]
        widgets = {
            "symptoms": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "e.g., fever for 3 days, dry cough, headache…"
            })
        }