from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # New Fields requested
    address = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username

# Signals to automatically create a Profile when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PatientProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # This check prevents errors if the profile was deleted or doesn't exist yet
    if hasattr(instance, 'patientprofile'):
        instance.patientprofile.save()

class ScreeningResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='screenings/')
    diagnosis = models.CharField(max_length=100)
    confidence = models.CharField(max_length=20)
    all_probs = models.JSONField(null=True, blank=True) # Store all probabilities
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.diagnosis} - {self.date.strftime('%Y-%m-%d')}"

class Specialist(models.Model):
    name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255) # e.g. Glaucoma Specialist
    location = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.name} ({self.specialty})"

# Model for the Chatbot:
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ChatMessage(models.Model):
    # Link messages to a specific session (The "Box" in your sidebar)
    session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    # Link to the User (Required by your database constraint)
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    query = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username}: {self.query[:20]}"


from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.user.username} on {self.created_at}"