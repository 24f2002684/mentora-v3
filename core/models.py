from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student Scholar'
        MENTOR = 'MENTOR', 'Mentor'
        TRUSTEE = 'TRUSTEE', 'Trustee'
        ADMIN = 'ADMIN', 'Administrator'

    email = models.EmailField(unique=True, db_index=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT, db_index=True)
    phone = models.CharField(max_length=25, blank=True, null=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')],
        default='light'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_student(self):
        return self.role == self.Role.STUDENT

    def is_mentor(self):
        return self.role == self.Role.MENTOR

    def is_trustee(self):
        return self.role == self.Role.TRUSTEE

    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'New Assignment'
        SUBMISSION_RECEIVED = 'SUBMISSION_RECEIVED', 'Submission Received'
        REVIEW_PUBLISHED = 'REVIEW_PUBLISHED', 'Mentor Feedback'
        FEEDBACK_RECEIVED = 'FEEDBACK_RECEIVED', 'Trustee Feedback'
        SUPPORT_ALERT = 'SUPPORT_ALERT', 'Support Alert'
        GOAL_MILESTONE = 'GOAL_MILESTONE', 'Goal Milestone'
        SYSTEM = 'SYSTEM', 'System Notification'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_notification_type_display()}] To {self.recipient.username}: {self.title}"


class AuditEvent(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    event_type = models.CharField(max_length=60, db_index=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {actor_name} -> {self.event_type}"
