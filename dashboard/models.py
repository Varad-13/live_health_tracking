from django.db import models
from django.contrib.auth.models import User
from .utils import pin_donation_to_ipfs

# Define common choices
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    qualifications = models.CharField(max_length=200)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.full_name

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    hospital_affiliation = models.CharField(max_length=100)

    def __str__(self):
        return self.full_name

class VitalSign(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='vital_signs')
    timestamp = models.DateTimeField(auto_now_add=True)
    heart_rate = models.PositiveIntegerField(help_text="Beats per minute")
    temperature = models.FloatField(help_text="Temperature in °F or °C")
    blood_pressure = models.CharField(max_length=20, help_text="Blood pressure e.g., '120/80'")
    oxygen_saturation = models.FloatField(help_text="Oxygen saturation percentage")
    risk_prediction = models.CharField(max_length=20, help_text="Risk label (e.g., 'High Risk' or 'Low Risk')")
    ipfs_hash = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def save(self, *args, **kwargs):
        # Save the object to the database
        super().save(*args, **kwargs)
        
        # Create a donation_data payload from the vital sign data
        donation_data = {
            "patient": self.patient.full_name,
            "timestamp": self.timestamp.isoformat(),
            "heart_rate": self.heart_rate,
            "temperature": self.temperature,
            "blood_pressure": self.blood_pressure,
            "oxygen_saturation": self.oxygen_saturation,
            "risk_prediction": self.risk_prediction,
        }
        
        # Pin the data to IPFS via Pinata
        ipfs_hash = pin_donation_to_ipfs(donation_data)
        if ipfs_hash:
            self.__class__.objects.filter(pk=self.pk).update(ipfs_hash=ipfs_hash)
        else:
            pass
