from django.db import models
from django.conf import settings
from students.models import StudentProfile, Goal


class TrusteeProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trustee_profile'
    )
    name = models.CharField(max_length=150, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30, blank=True, default='')
    designation = models.CharField(max_length=150, blank=True, default='VRCF Trustee')
    profile_photo = models.ImageField(upload_to='trustees/photos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trustee: {self.name} ({self.designation})"


class TrusteeFeedback(models.Model):
    trustee = models.ForeignKey(TrusteeProfile, on_delete=models.CASCADE, related_name='sent_feedbacks')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='trustee_feedbacks')
    title = models.CharField(max_length=255)
    message = models.TextField()
    linked_goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='trustee_feedbacks')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.trustee.name} to {self.student.name}: {self.title}"
