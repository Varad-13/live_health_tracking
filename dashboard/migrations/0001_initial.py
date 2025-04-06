# Generated by Django 5.2 on 2025-04-05 22:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100)),
                ('age', models.PositiveIntegerField()),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('qualifications', models.CharField(max_length=200)),
                ('gender', models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=20, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='doctor_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PatientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100)),
                ('age', models.PositiveIntegerField()),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('dob', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=20, null=True)),
                ('hospital_affiliation', models.CharField(max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='VitalSign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('heart_rate', models.PositiveIntegerField(help_text='Beats per minute')),
                ('temperature', models.FloatField(help_text='Temperature in °F or °C')),
                ('blood_pressure', models.CharField(help_text="Blood pressure e.g., '120/80'", max_length=20)),
                ('oxygen_saturation', models.FloatField(help_text='Oxygen saturation percentage')),
                ('risk_prediction', models.CharField(help_text="Risk label (e.g., 'High Risk' or 'Low Risk')", max_length=20)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vital_signs', to='dashboard.patientprofile')),
            ],
        ),
    ]
