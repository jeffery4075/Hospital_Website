from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Patient,Staff,Doctor,DoctorWorkingHours,DoctorUnavailability,Appointment,PatientVisit,Prescription


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter  = ('role', 'is_active', 'is_staff', 'is_superuser')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role',)}),
    )

class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'blood_group', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number')
    
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff_role', 'contact_phone', 'created_at')
    list_filter  = ('staff_role',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'contact_phone')

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'registration_no', 'consultation_duration_min', 'max_daily_appointments', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'specialization', 'registration_no')

class DoctorWorkingHoursAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'weekdays', 'start_time', 'end_time', 'is_active', 'created_at')
    list_filter  = ('weekdays', 'is_active')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name','doctor__specialization')

class DoctorUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'reason', 'created_at')
    list_filter  = ('date',)
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name', 'reason')

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('doctor', 'appointment_date', 'status')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name',
                     'patient__username', 'patient__first_name', 'patient__last_name')
    readonly_fields = ('created_at', 'updated_at') 

from django.contrib import admin
from .models import PatientVisit, Prescription

class PatientVisitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = (
        'patient__user__username',
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__username',
        'doctor__user__first_name',
        'doctor__user__last_name',
    )
    readonly_fields = ('created_at', 'updated_at')

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('medicine_name', 'patient', 'doctor', 'visit', 'created_at')
    list_filter = ('doctor', 'created_at')
    search_fields = (
        'medicine_name',
        'patient__user__username',
        'patient__user__first_name',
        'patient__user__last_name',
        'doctor__user__username',
        'doctor__user__first_name',
        'doctor__user__last_name',
    )
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(DoctorWorkingHours, DoctorWorkingHoursAdmin)
admin.site.register(DoctorUnavailability, DoctorUnavailabilityAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(PatientVisit, PatientVisitAdmin)
admin.site.register(Prescription, PrescriptionAdmin)