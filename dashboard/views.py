import os
import random
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from .models import *
from collections import defaultdict
import joblib

import numpy as np

import firebase_admin
from firebase_admin import credentials, db
from tensorflow.keras.models import load_model

cred_path = os.path.join(settings.BASE_DIR, 'esp32-c093e-firebase-adminsdk-fbsvc-e921972cd0.json')
model_path = os.path.join(settings.BASE_DIR, 'risk_classifier_model.h5')
scaler_path = os.path.join(settings.BASE_DIR, 'risk_scaler.pkl')

scaler = joblib.load(scaler_path)
cred = credentials.Certificate(cred_path)
model = load_model(model_path)

firebase_app = firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://esp32-c093e-default-rtdb.firebaseio.com/'
})


def welcome(request):
    return render(request, 'welcome.html')

def signin(request):
    if request.method == "POST":
        # Retrieve email and password from the submitted form
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # Authenticate the user using email as the username
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to dashboard or desired view
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('signin')
    
    # Render the sign-in form for GET requests
    return render(request, 'signin.html')

def signup(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')
        
        # Create a new user using email as the username
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = name
        user.save()
        
        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('signin')
    
    # GET request renders the signup form
    return render(request, "signup.html")

def signout(request):
    logout(request)
    return redirect('signin')

@login_required
def doctor_intake(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        age = request.POST.get("age")
        phone = request.POST.get("phone")
        qualifications = request.POST.get("qualifications")
        gender = request.POST.get("gender", "Not Specified")
        
        if not request.user.is_authenticated:
            messages.error(request, "Please sign in to update your profile.")
            return redirect('signin')
        
        # Create or update the doctor's profile
        doctor_profile, created = DoctorProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'full_name': full_name,
                'age': age,
                'phone': phone,
                'qualifications': qualifications,
                'gender': gender,
            }
        )
        
        messages.success(request, "Doctor profile updated successfully.")
        return redirect('dashboard')  # Change to your actual dashboard URL name
    
    # Render the form on GET request
    return render(request, 'doctor_intake.html')

@login_required
def patient_intake(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        age = request.POST.get("age")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender", "Not Specified")
        hospital_affiliation = request.POST.get("hospital_affiliation")

        if not request.user.is_authenticated:
            messages.error(request, "Please sign in to update your profile.")
            return redirect('signin')
        
        # Create or update the patient's profile
        patient_profile, created = PatientProfile.objects.get_or_create(user=request.user,
                                                                        defaults={
                                                                                'full_name': full_name,
                                                                                'age': age,
                                                                                'phone': phone,
                                                                                'gender': gender,
                                                                                'hospital_affiliation': hospital_affiliation,
                                                                            }
                                                                        )
        patient_profile.save()
        
        messages.success(request, "Patient profile updated successfully.")
        return redirect('dashboard')  # Change this to your desired redirect
        
    # Render the form on GET request
    return render(request, "patient_intake.html")

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('signin')
    
    # If the user has a doctor profile, redirect to the doctor dashboard.
    if hasattr(request.user, 'doctor_profile'):
        return redirect('doctor_dashboard')
    # Otherwise, if they have a patient profile, redirect to the patient dashboard.
    elif hasattr(request.user, 'patient_profile'):
        return redirect('patient_dashboard')
    else:
        messages.error(request, "Profile not found. Please complete your intake form.")
        return redirect('patient_intake')

@login_required(login_url='signin')
def patient_dashboard(request):
    if not hasattr(request.user, 'patient_profile'):
        messages.error(request, "Patient profile not found. Please complete your intake form.")
        return redirect('patient_intake')
    patient = request.user.patient_profile
    ref = db.reference("test", app=firebase_app)
    data = ref.get()

    if not isinstance(data, dict):
        messages.error(request, "No valid data found from live data source.")
        return render(request, 'vitals.html')

    # Extract vitals
    heart_rate = data.get("HeartBit", random.randint(60, 120))
    oxygen_saturation = data.get("Oximeter", random.randint(95, 100))
    temperature = data.get("Temperature", random.randint(36, 37))
    systolic = random.randint(110, 130)
    diastolic = random.randint(70, 90)
    blood_pressure = f"{systolic}/{diastolic}"

    # Prepare input data for risk prediction
    input_data = np.array([[heart_rate, temperature, oxygen_saturation]])
    input_scaled = scaler.transform(input_data)

    # Predict
    prediction = model.predict(input_scaled)
    model_risk_label = "High Risk" if prediction[0][0] > 0.5 else "Normal"

    VitalSign.objects.create(
        patient=request.user.patient_profile,
        heart_rate=heart_rate,
        temperature=temperature,
        blood_pressure=blood_pressure,
        oxygen_saturation=oxygen_saturation,
        risk_prediction=model_risk_label,
    )

    recent_measurements = VitalSign.objects.filter(patient=request.user.patient_profile).order_by('-timestamp')[:6]

    context = {
        "heart_rate": heart_rate,
        "oxygen_saturation": oxygen_saturation,
        "temperature": temperature,
        "blood_pressure": blood_pressure,
        "risk": model_risk_label,
        "recent_measurements": recent_measurements,
        "patient": patient
    }

    return render(request, 'vitals.html', context)

def vitals_data(request):
    # Fetch live data from Firebase
    ref = db.reference("test", app=firebase_app)
    data = ref.get()

    if not isinstance(data, dict):
        return JsonResponse({"error": "No valid data found"}, status=400)

    # Extract vitals from the live data or simulate fallback values
    heart_rate = data.get("HeartBit", random.randint(60, 120))
    oxygen_saturation = data.get("Oximeter", random.randint(95, 100))
    temperature = data.get("Temperature", random.randint(36, 37))

    systolic = random.randint(110, 130)
    diastolic = random.randint(70, 90)
    blood_pressure = f"{systolic}/{diastolic}"

    # Prepare input and scale it
    input_data = np.array([[temperature, heart_rate, oxygen_saturation]])
    input_scaled = scaler.transform(input_data)

    # Predict
    prediction = model.predict(input_scaled)
    model_risk_label = "High Risk" if prediction[0][0] > 0.5 else "Normal"

    return JsonResponse({
        "heart_rate": heart_rate,
        "oxygen_saturation": oxygen_saturation,
        "temperature": temperature,
        "blood_pressure": blood_pressure,
        "risk": model_risk_label
    })

@login_required(login_url='signin')
def doctor_dashboard(request):
    if not hasattr(request.user, 'doctor_profile'):
        messages.error(request, "Doctor profile not found. Please complete your intake form.")
        return redirect('doctor_intake')
    
    patients = PatientProfile.objects.all()
    
    # Group patients by hospital affiliation
    hospital_dict = defaultdict(list)
    for patient in patients:
        hospital_dict[patient.hospital_affiliation].append(patient)
    
    # Convert the dictionary to a list of dictionaries for easier template looping
    hospital_groups = []
    for hospital, patient_list in hospital_dict.items():
        hospital_groups.append({
            'name': hospital,
            'patients': patient_list
        })

    context = {
        'doctor': request.user.doctor_profile,
        'hospital_groups': hospital_groups,
    }
    return render(request, 'doctor_dashboard.html', context)

@login_required(login_url='signin')
def doctor_patient_dashboard(request, patient_id):
    # Ensure the logged in user is a doctor
    if not hasattr(request.user, 'doctor_profile'):
        messages.error(request, "Doctor profile not found. Please complete your intake form.")
        return redirect('doctor_intake')

    # Retrieve the patient using the provided ID
    patient = get_object_or_404(PatientProfile, id=patient_id)

    # Fetch live data from Firebase
    ref = db.reference("test", app=firebase_app)
    data = ref.get()

    if not isinstance(data, dict):
        messages.error(request, "No valid data found from live data source.")
        return render(request, 'vitals.html')

    # Extract vitals from Firebase data
    heart_rate = data.get("HeartBit", random.randint(60, 120))
    oxygen_saturation = data.get("Oximeter", random.randint(95, 100))
    temperature = data.get("Temperature", random.randint(36, 37))
    systolic = random.randint(110, 130)
    diastolic = random.randint(70, 90)
    blood_pressure = f"{systolic}/{diastolic}"

    # Prepare input data for risk prediction
    input_data = np.array([[heart_rate, temperature, oxygen_saturation]])
    input_scaled = scaler.transform(input_data)

    # Predict
    prediction = model.predict(input_scaled)
    model_risk_label = "High Risk" if prediction[0][0] > 0.5 else "Normal"

    VitalSign.objects.create(
        patient=patient,
        heart_rate=heart_rate,
        temperature=temperature,
        blood_pressure=blood_pressure,
        oxygen_saturation=oxygen_saturation,
        risk_prediction=model_risk_label,
    )

    # Fetch the 6 most recent measurements for this patient
    recent_measurements = VitalSign.objects.filter(patient=patient).order_by('-timestamp')[:6]

    context = {
        "heart_rate": heart_rate,
        "oxygen_saturation": oxygen_saturation,
        "temperature": temperature,
        "blood_pressure": blood_pressure,
        "risk": model_risk_label,
        "recent_measurements": recent_measurements,
        "patient": patient,
    }

    return render(request, 'vitals.html', context)
