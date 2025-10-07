from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import RegexValidator,MinValueValidator,MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q,F

class CustomUser(AbstractUser):
    Role_Choice=(
        ('patient','Patient'),
        ('staff','Staff'),
        ('doctor','Doctor'),
        ('admin','Admin'),
    )
    role = models.CharField(max_length=20, choices=Role_Choice,default='patient', 
                            help_text='User role controls access in the system')

    def __str__(self):
        return f" {self.username} {self.role} "


GENDER_CHOICE= (
    ('M','Male'),
    ('F','Female'),
    ('O','Other'),
)
BLOOD_GROUP = (
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
)

pin_validator = RegexValidator(r'^\d{6}$', 'Enter a valid 6 digit code')
phone_validator = RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit phone number')

class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient')

    # Patient Details
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    dob = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India', blank=True)
    pincode = models.CharField(max_length=6, validators=[pin_validator])
    phone_number = models.CharField(max_length=10, validators=[phone_validator])

    # Patient Medical Records

    height_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(50), MaxValueValidator(250)])
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(2), MaxValueValidator(300)])
    allergies = models.TextField(blank=True, null=True)
    chronic_diseases = models.TextField(blank=True, null=True)
    current_medications = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def clean(self):
        if self.dob and self.dob > timezone.localdate():
            raise ValidationError('Date of birth cannot be in the future')

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return full_name or self.user.username

# Staff Model
STAFF_ROLE_CHOICES = (
    ('receptionist','Receptionist'),
    ('nurse','Nurse'),
    ('pharmacist','Pharmacist'),
    ('lab','Lab Technician'),
    ('billing','Billing'),
    ('other','Other'),
)
class Staff(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='staff')
    staff_role = models.CharField(max_length=30, choices=STAFF_ROLE_CHOICES)

    contact_phone = models.CharField(max_length=10, validators=[phone_validator], blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'

    def __str__(self):
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        return full_name or self.user.username
    
class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor')

    # Professional info
    specialization = models.CharField(max_length=120, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)

    registration_no = models.CharField(max_length=60, blank=True)
    consultation_duration_min = models.PositiveSmallIntegerField(default=15, validators=[MinValueValidator(5), MaxValueValidator(120)], help_text='Minutes per appointment')
    max_daily_appointments = models.PositiveSmallIntegerField(default=0,)
    clinic_location = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'

    def __str__(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full or self.user.username
    
WEEKDAY_CHOICES = (
    (0,'Monday'),
    (1,'Tuesday'),
    (2,'Wednesday'),
    (3,'Thursday'),
    (4,'Friday'),
    (5,'Saturday'),
    (6,'Sunday'),
)
class DoctorWorkingHours(models.Model):

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='working_hours')
    weekdays = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES, validators=[MinValueValidator(0), MaxValueValidator(6)])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doctor Working Hours'
        verbose_name_plural = 'Doctor Working Hours'
        constraints = [
            models.CheckConstraint(
                name='dwh_start_before_end',
                check=Q(start_time__lt=F('end_time'))
            ),
            models.UniqueConstraint(
                fields=['doctor', 'weekdays', 'start_time', 'end_time'],
                name='uniq_doctor_weekday_time_block'
            ),
        ]

    def __str__(self):
        return f"{self.doctor} {self.get_weekdays_display()} {self.start_time} {self.end_time}"
    
class DoctorUnavailability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='unavailability')
    date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time   = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doctor Unavailability'
        verbose_name_plural = 'DoctorUnavailability'
        constraints = [
            models.CheckConstraint(
                name='du_valid_time_or_full_day',
                check=(Q(start_time__isnull=True, end_time__isnull=True) | Q(start_time__lt=F('end_time')))
            ),
            models.UniqueConstraint(
                fields=['doctor', 'date', 'start_time', 'end_time'],
                name='uniq_doctor_date_time_unavail'
            ),
        ]
    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.doctor} {self.date} {self.start_time} {self.end_time}"
        return f"{self.doctor} {self.date}"

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    STATUS_CHOICES = (
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('canceled','Canceled'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                condition=Q(status__in=['pending', 'confirmed']),
                name='uniq_active_appointment_per_slot',
            ),
        ]

    def __str__(self):
        return f"Appointment {self.id} with Dr. {self.doctor} on {self.appointment_date} at {self.appointment_time}"
    
    def clean(self):
        doctor_working_hour = DoctorWorkingHours.objects.filter(
            doctor=self.doctor, weekdays=self.appointment_date.weekday()
        )

        if not doctor_working_hour.exists():
            raise ValidationError(f"Dr. {self.doctor} is not available on {self.appointment_date.weekday()}")

        working_hours = doctor_working_hour.first()
        if not (working_hours.start_time <= self.appointment_time <= working_hours.end_time):
            raise ValidationError(f"Appointment time must be between {working_hours.start_time} and {working_hours.end_time}")

        doctor_unavailability = DoctorUnavailability.objects.filter(
            doctor=self.doctor, date=self.appointment_date
        ).filter(
            Q(start_time__isnull=True, end_time__isnull=True) |
            Q(start_time__lte=self.appointment_time, end_time__gte=self.appointment_time)
        )
        if doctor_unavailability.exists():
            raise ValidationError(f"Dr. {self.doctor} is unavailable at the selected time")

        # <-- exclude canceled and this same row
        if Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date,
            appointment_time=self.appointment_time,
        ).exclude(pk=self.pk).exclude(status='canceled').exists():
            raise ValidationError("This time slot is already booked")
        
class PatientVisit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='visits')
    appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True, related_name='visit')

    height_cm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    blood_pressure = models.CharField(max_length=20, blank=True, null=True)
    sugar_level = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Patient Visit'
        verbose_name_plural = 'Patient Visits'


    def __str__(self):
        return f"Visit {self.id} {self.patient} by {self.doctor} on {self.created_at.date()}"

class Prescription(models.Model):
    visit = models.ForeignKey(PatientVisit, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')

    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.CharField(max_length=100, blank=True, null=True)
    duration_days = models.PositiveIntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Prescription'
        verbose_name_plural = 'Prescriptions'

    def __str__(self):
        return f"{self.medicine_name} for {self.patient} by {self.doctor}"
