# Generated by Django 5.2 on 2025-04-06 00:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patientprofile',
            name='dob',
        ),
        migrations.AddField(
            model_name='vitalsign',
            name='ipfs_hash',
            field=models.TextField(blank=True, null=True),
        ),
    ]
