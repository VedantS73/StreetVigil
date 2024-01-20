from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    points = models.IntegerField(default=0)

# class CapturedImage(models.Model):
#     image = models.FileField(upload_to='captured_images/')

# class ReportCategory(models.TextChoices):
#     CRIME = 'CR', 'Crime'
#     ACCIDENT = 'AC', 'Accident'
#     SUSPICIOUS_ACTIVITY = 'SA', 'Suspicious Activity'
#     LOST_AND_FOUND = 'LF', 'Lost and Found'
#     OTHER = 'OT', 'Other'

class CapturedImage(models.Model):
    image = models.ImageField(upload_to='captured_images/')
    category = models.CharField(max_length=200, blank =  True , null = True)
    description = models.TextField(default='No description provided')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    verified = models.BooleanField(default=False )
    rewards = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"Report #{self.id} - {self.category}"

    class Meta:
        ordering = ['-created_at']
