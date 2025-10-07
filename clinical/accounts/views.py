from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash, login as auth_login,authenticate
from django.utils import timezone
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, PatientEditForm, UserEditForm,StaffCheckInForm,PrescriptionForm,VisitSymptomsForm
from .models import Patient, Appointment, PatientVisit, Prescription,Doctor, DoctorWorkingHours, DoctorUnavailability,Appointment,Staff
from django.db import IntegrityError
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

def HomePage(request):
    return render(request,"Home/Home_Page.html")

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "patient"
            user.set_password(form.cleaned_data["password1"])
            user.save()

            Patient.objects.create(
                user=user,
                gender=form.cleaned_data["gender"],
                dob=form.cleaned_data["dob"],
                pincode=form.cleaned_data["pincode"],
                phone_number=form.cleaned_data["phone_number"],
            )

            login(request, user)
            return redirect("patient_dashboard")
    else:
        form = SignUpForm()

    return render(request,"Patient/signup.html",{"form":form})

def patient_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('patient_register')
    if getattr(request.user, 'role', '') != 'patient':
        return redirect('/admin/')

    patient_profile = getattr(request.user, 'patient', None)


    today = timezone.localdate()
    now_time = timezone.localtime().time()
    upcoming_appointments = (
        Appointment.objects
        .filter(patient=request.user)
        .filter(
            Q(appointment_date__gt=today) |
            Q(appointment_date=today, appointment_time__gte=now_time)
        )
        .order_by('appointment_date', 'appointment_time')[:10]
    )

    visits = (
        PatientVisit.objects.filter(patient=patient_profile)
        .order_by('-created_at')[:10]
        if patient_profile else []
    )
    prescriptions = (
        Prescription.objects.filter(patient=patient_profile)
        .order_by('-created_at')[:10]
        if patient_profile else []
    )
    return render(
        request,
        "Patient/Patient_dashboard.html",
        {
            "upcoming_appointments": upcoming_appointments,
            "visits": visits,
            "prescriptions": prescriptions,
        },
    )

def logout_view(request):

    if request.user.is_authenticated:
        logout(request)
    return redirect('login')


def edit_profile(request):
    if not request.user.is_authenticated:
        return redirect('patient_register')
    if getattr(request.user, "role", "") != "patient":
        return redirect('/admin/')

    patient = getattr(request.user, "patient", None)
    if patient is None:
        from .models import Patient
        patient = Patient.objects.create(
            user=request.user,
            gender="O",
            dob=timezone.localdate(),
            pincode="000000",
            phone_number="0000000000",
        )

    if request.method == "POST":
        uform = UserEditForm(request.POST, instance=request.user)
        pform = PatientEditForm(request.POST, instance=patient)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            return redirect('patient_dashboard')
    else:
        uform = UserEditForm(instance=request.user)
        pform = PatientEditForm(instance=patient)

    return render(
        request,
        "Patient/profile_edit.html",
        {"uform": uform, "pform": pform}
    )

def change_password(request):
    if not request.user.is_authenticated:
        return redirect('patient_register')
    if getattr(request.user, 'role', '') != 'patient':
        return redirect('/admin/')

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('patient_dashboard')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request,"Patient/change_password.html",{"form":form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('patient_dashboard')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect(next_url or 'patient_dashboard')
    else:
        form = AuthenticationForm(request)

    return render(request,'Patient/login.html',{'form':form,'next':next_url})

def book_appointment(request):
    if not request.user.is_authenticated:
        return redirect('patient_register')
    if getattr(request.user, 'role', '') != 'patient':
        return redirect('/admin/')

    doctors = Doctor.objects.select_related('user').order_by('user__first_name', 'user__last_name')
    context = {
        "doctors": doctors,
        "selected_doctor_id": None,
        "selected_date": None,
        "slots": [],
    }
    def compute_slots(doctor, day):
        weekday = day.weekday()
        blocks = DoctorWorkingHours.objects.filter(
            doctor=doctor, weekdays=weekday, is_active=True
        ).order_by('start_time')

        if not blocks.exists():
            return []

        appt_qs = Appointment.objects.filter(
            doctor=doctor, appointment_date=day
        ).exclude(status='canceled')

        if doctor.max_daily_appointments and appt_qs.count() >= doctor.max_daily_appointments:
            return []

        already = set(appt_qs.values_list('appointment_time', flat=True))

        unavail = list(DoctorUnavailability.objects.filter(doctor=doctor, date=day))

        def is_blocked(t):
            for u in unavail:
                if u.start_time is None and u.end_time is None:
                    return True

                if u.start_time and u.end_time and u.start_time <= t <= u.end_time:
                    return True
            return False

        step = doctor.consultation_duration_min or 15
        out = []
        now_local_time = timezone.localtime().time() if day == timezone.localdate() else None

        for b in blocks:
            cur_dt = datetime.combine(day, b.start_time)
            end_dt = datetime.combine(day, b.end_time)
            while cur_dt < end_dt:
                t = cur_dt.time()

                if now_local_time and t <= now_local_time:
                    cur_dt += timedelta(minutes=step)
                    continue

                booked = t in already
                blocked = is_blocked(t)

                out.append({
                    "time_value": t.strftime('%H:%M'),
                    "time_display": t.strftime('%H:%M'),
                    "booked": booked,
                    "blocked": blocked,
                })
                cur_dt += timedelta(minutes=step)

        seen, slots = set(), []
        for s in sorted(out, key=lambda x: x["time_value"]):
            if s["time_value"] in seen:
                continue
            seen.add(s["time_value"])
            slots.append(s)
        return slots

    if request.method == "POST":
        action = request.POST.get("action")
        doctor_id = request.POST.get("doctor_id")
        date_str  = request.POST.get("date")

        if not doctor_id or not date_str:
            context["error_message"] = "Please choose a doctor and date."
            return render(request, "Patient/appointment_book.html", context)

        try:
            doctor = Doctor.objects.select_related('user').get(pk=int(doctor_id))
        except (Doctor.DoesNotExist, ValueError):
            context["error_message"] = "Doctor not found."
            return render(request, "Patient/appointment_book.html", context)

        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            context["error_message"] = "Invalid date format."
            return render(request, "Patient/appointment_book.html", context)

        context["selected_doctor_id"] = doctor.id
        context["selected_date"] = selected_date.strftime("%Y-%m-%d")

        if action == "search":
            slots = compute_slots(doctor, selected_date)
            if not slots:
                context["error_message"] = "No slots available for the selected date."
            context["slots"] = slots
            return render(request, "Patient/appointment_book.html", context)

        elif action == "book":
            time_str = request.POST.get("time")
            if not time_str:
                context["error_message"] = "Pick a time slot."
                context["slots"] = compute_slots(doctor, selected_date)
                return render(request, "Patient/appointment_book.html", context)
            try:
                appt_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                context["error_message"] = "Invalid time slot."
                context["slots"] = compute_slots(doctor, selected_date)
                return render(request, "Patient/appointment_book.html", context)

            appt = Appointment(
                doctor=doctor,
                patient=request.user,
                appointment_date=selected_date,
                appointment_time=appt_time,
                status='pending',
            )
            try:
                appt.clean()
            except ValidationError as e:
                context["error_message"] = "; ".join(e.messages)
                context["slots"] = compute_slots(doctor, selected_date)
                return render(request, "Patient/appointment_book.html", context)

            try:
                appt.save()
            except IntegrityError:
                context["error_message"] = "That slot was just taken. Please pick another."
                context["slots"] = compute_slots(doctor, selected_date)
                return render(request, "Patient/appointment_book.html", context)

            return redirect('patient_dashboard')

    return render(request,"Patient/appointment_book.html",context)

def cancel_appointment(request, pk):
    if not request.user.is_authenticated:
        return redirect('patient_register')
    if getattr(request.user, 'role', '') != 'patient':
        return redirect('/admin/')

    if request.method != 'POST':
        return redirect('patient_dashboard')

    appt = get_object_or_404(Appointment, pk=pk, patient=request.user)

    today = timezone.localdate()
    now_t = timezone.localtime().time()
    is_past = (appt.appointment_date < today) or (
        appt.appointment_date == today and appt.appointment_time < now_t
    )
    if is_past:
       
        return redirect('patient_dashboard')

    if appt.status != 'canceled':
        appt.status = 'canceled'
        appt.save()

    return redirect('patient_dashboard')


def staff_login(request):
    if request.user.is_authenticated:
        role = getattr(request.user, 'role', '')
        if role == 'staff':
            return redirect('staff_dashboard')
        if role == 'patient':
            return redirect('patient_dashboard')
        if role == 'doctor':
            return redirect('patient_dashboard')
        if request.user.is_superuser:
            return redirect('admin:index')
        return redirect('patient_dashboard')

    ctx = {}
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)

        if not user:
            ctx['error'] = 'Invalid username or password.'
        elif getattr(user, 'role', '') != 'staff':
            ctx['error'] = 'This page is only for staff accounts.'
        else:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect('staff_dashboard')

    ctx['next'] = next_url
    return render(request,'Staff/staff_login.html', ctx)

def staff_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if getattr(request.user, 'role', '') != 'staff':
        if getattr(request.user, 'role', '') == 'patient':
            return redirect('patient_dashboard')
        return redirect('admin:index')


    date_str = request.GET.get('date', '')
    doctor_id = request.GET.get('doctor_id', '')

    day = timezone.localdate()
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    appts = (Appointment.objects
             .select_related('doctor__user')
             .filter(appointment_date=day)
             .exclude(status='canceled')
             .order_by('appointment_time'))

    if doctor_id:
        appts = appts.filter(doctor_id=doctor_id)

    doctors = Doctor.objects.select_related('user').order_by('user__first_name', 'user__last_name')

    ctx = {
        'selected_date': day.isoformat(),
        'appointments': appts,
        'doctors': doctors,
        'selected_doctor_id': int(doctor_id) if doctor_id else '',
    }
    return render(request,'Staff/staff_dashboard.html',ctx)

def staff_logout(request):
    """
    Logs out the current user and sends them to the staff login page.
    Works for GET or POST; supports ?next=/some/url if you pass it.
    """
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    logout(request)
    return redirect(next_url or 'staff_login')


def _ensure_staff(request):
    if not request.user.is_authenticated or getattr(request.user, "role", "") != "staff":
        return False
    return True

def staff_appointment_detail(request, pk):
    if not _ensure_staff(request):
        return redirect("staff_login")

    appt = get_object_or_404(Appointment, pk=pk)

    visit = PatientVisit.objects.filter(appointment=appt).first()

    if request.method == "POST":
        action = request.POST.get("action", "save")
        if action == "cancel":
            appt.status = "canceled"
            appt.save()
            return redirect("staff_dashboard")

        form = StaffCheckInForm(request.POST, instance=visit)
        if form.is_valid():
            v = form.save(commit=False)
            v.doctor = appt.doctor
            v.patient = appt.patient.patient
            v.appointment = appt
            v.save()

            appt.status = "confirmed"
            appt.save()
            return redirect("staff_dashboard")
    else:
        initial = {}
        form = StaffCheckInForm(instance=visit, initial=initial)

    ctx = {
        "appointment": appt,
        "form": form,
        "has_visit": bool(visit),
    }
    return render(request,"Staff/appointment_detail.html", ctx)


def doctor_login(request):
    if request.user.is_authenticated:
        role = getattr(request.user, 'role', '')
        if role == 'doctor':
            return redirect('doctor_dashboard')
        if role == 'staff':
            return redirect('staff_dashboard')
        if role == 'patient':
            return redirect('patient_dashboard')
        if request.user.is_superuser:
            return redirect('admin:index')
        return redirect('patient_dashboard')

    ctx = {}
    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)

        if not user:
            ctx['error'] = 'Invalid username or password.'
        elif getattr(user, 'role', '') != 'doctor':
            ctx['error'] = 'This page is only for doctor accounts.'
        else:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                return redirect(next_url)
            return redirect('doctor_dashboard')

    ctx['next'] = next_url
    return render(request,'Doctor/doctor_login.html', ctx)


def doctor_logout(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    logout(request)
    return redirect(next_url or 'doctor_login')


def doctor_dashboard(request):
    if not request.user.is_authenticated or getattr(request.user, 'role', '') != 'doctor':
        return redirect('doctor_login')

    doctor_profile = getattr(request.user, 'doctor', None)
    if doctor_profile is None:
        return render(request, 'Doctor/doctor_dashboard.html', {
            'error': 'Doctor profile is missing for this account.'
        })

    date_str = request.GET.get('date') or timezone.localdate().isoformat()
    try:
        selected_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        selected_date = timezone.localdate()

    appts = (
        Appointment.objects
        .select_related('patient', 'doctor__user')
        .filter(doctor=doctor_profile, appointment_date=selected_date)
        .order_by('appointment_time')
    )

    return render(request, 'Doctor/doctor_dashboard.html', {
        'selected_date': selected_date.isoformat(),
        'appointments': appts,
    })

def doctor_appointment_detail(request, pk):
    if not request.user.is_authenticated or getattr(request.user, "role", "") != "doctor":
        return redirect("doctor_login")

    appt = get_object_or_404(
        Appointment.objects.select_related("doctor__user", "patient"),
        pk=pk
    )
    doctor_profile = getattr(request.user, "doctor", None)
    if doctor_profile is None or appt.doctor_id != doctor_profile.id:
        return redirect("doctor_dashboard")

    visit, _ = PatientVisit.objects.get_or_create(
        appointment=appt,
        defaults={"doctor": appt.doctor, "patient": appt.patient.patient}
    )

    can_edit = (appt.status == "confirmed")

    if request.method == "POST":
        action = request.POST.get("action", "")

        # Save symptoms
        if action == "save_symptoms":
            if not can_edit:
                return redirect("doctor_appointment_detail", pk=appt.pk)
            sym_form = VisitSymptomsForm(request.POST, instance=visit)
            if sym_form.is_valid():
                sym_form.save()
                return redirect("doctor_appointment_detail", pk=appt.pk)

        # Add prescription (your existing logic)
        if action == "add_prescription":
            if not can_edit:
                return redirect("doctor_appointment_detail", pk=appt.pk)
            form = PrescriptionForm(request.POST)
            if form.is_valid():
                p = form.save(commit=False)
                p.visit = visit
                p.doctor = appt.doctor
                p.patient = visit.patient
                p.save()
                return redirect("doctor_appointment_detail", pk=appt.pk)

    else:
        sym_form = VisitSymptomsForm(instance=visit) if can_edit else None
        form = PrescriptionForm() if can_edit else None

    prescriptions = visit.prescriptions.select_related("doctor__user").order_by("-created_at")

    return render(request, "Doctor/appointment_prescribe.html", {
        "appointment": appt,
        "visit": visit,
        "form": form,
        "sym_form": sym_form,
        "prescriptions": prescriptions,
        "can_prescribe": can_edit, 
    })