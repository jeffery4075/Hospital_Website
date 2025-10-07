"""
URL configuration for clinical project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Homepage Url
    path('', views.HomePage, name='HomePage'),

    # Patient Url
    path('register/',views.signup,name='patient_register'),
    path('patient_dashboard/',views.patient_dashboard,name='patient_dashboard'),
    path('logout/',views.logout_view,name='logout'),
    path('edit-profile/',views.edit_profile,name='edit_profile'),
    path('change-password/',views.change_password,name='change_password'),
    path('login/', views.login_view, name='login'),

    # Appointment booking
    path('book_appointment',views.book_appointment, name='book_appointment'),
    path('appointments/<int:pk>/cancel/', views.cancel_appointment, name='cancel_appointment'),

    # Staff Url
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/dashboard/',views.staff_dashboard,name='staff_dashboard'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/appointment/<int:pk>/', views.staff_appointment_detail, name='staff_appointment_detail'),

    # Doctor Url
    path('doctor/login/',views.doctor_login,name='doctor_login'),
    path('doctor/logout/',views.doctor_logout,name='doctor_logout'),
    path('doctor/dashboard/',views.doctor_dashboard,name='doctor_dashboard'),
    path('doctor/appointment/<int:pk>/',views.doctor_appointment_detail,name='doctor_appointment_detail'),

]


