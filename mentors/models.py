from django.db import models
from django.conf import settings
from students.models import StudentProfile, Competency


class MentorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_profile'
    )
    name = models.CharField(max_length=150, db_index=True)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30, blank=True, default='')
    designation = models.CharField(max_length=150, blank=True, default='')
    organization = models.CharField(max_length=150, blank=True, default='')
    bio = models.TextField(blank=True, default='')
    profile_photo = models.ImageField(upload_to='mentors/photos/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Mentor: {self.name} ({self.organization or 'VRCF'})"


class MentorStudentAssignment(models.Model):
    mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='student_assignments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mentor_assignments')
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('mentor', 'student')
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.mentor.name} -> {self.student.name} ({self.student.vrcf_id})"


class MentorTask(models.Model):
    class Priority(models.TextChoices):
        HIGH = 'HIGH', 'High Priority'
        MEDIUM = 'MEDIUM', 'Medium Priority'
        LOW = 'LOW', 'Low Priority'

    class Status(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Assigned'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        REVIEWED = 'REVIEWED', 'Reviewed'
        RESUBMISSION_REQUESTED = 'RESUBMISSION_REQUESTED', 'Resubmission Requested'

    assigned_mentor = models.ForeignKey(MentorProfile, on_delete=models.CASCADE, related_name='created_tasks')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assigned_tasks')
    title = models.CharField(max_length=255)
    instructions = models.TextField()
    deliverables = models.TextField(blank=True, default='')
    competencies = models.ManyToManyField(Competency, blank=True, related_name='mentor_tasks')
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    due_date = models.DateField(db_index=True)
    evaluation_criteria = models.TextField(blank=True, default='')
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.ASSIGNED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Task: {self.title} -> {self.student.name} [{self.get_status_display()}]"


class TaskSubmission(models.Model):
    task = models.OneToOneField(MentorTask, on_delete=models.CASCADE, related_name='submission')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    submission_text = models.TextField()
    attachment = models.FileField(upload_to='submissions/attachments/', null=True, blank=True)
    student_remarks = models.TextField(blank=True, default='')
    student_reflection = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)

    # Review fields
    reviewed_by = models.ForeignKey(MentorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    mentor_feedback = models.TextField(blank=True, default='')
    mentor_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # e.g. 1 to 5
    strengths = models.TextField(blank=True, default='')
    areas_for_improvement = models.TextField(blank=True, default='')
    next_recommended_action = models.TextField(blank=True, default='')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Submission for {self.task.title} by {self.student.name}"


class CompetencyAssessment(models.Model):
    class Source(models.TextChoices):
        MENTOR = 'MENTOR', 'Mentor Official Assessment'
        AI_FORMATIVE = 'AI_FORMATIVE', 'AI Formative Observation'
        STRUCTURED_ACTIVITY = 'STRUCTURED_ACTIVITY', 'Structured Activity Assessment'

    class Level(models.TextChoices):
        FOUNDATION = 'FOUNDATION', 'Foundation'
        DEVELOPING = 'DEVELOPING', 'Developing'
        PROFICIENT = 'PROFICIENT', 'Proficient'
        ADVANCED = 'ADVANCED', 'Advanced'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='competency_assessments')
    competency = models.ForeignKey(Competency, on_delete=models.CASCADE, related_name='assessments')
    source = models.CharField(max_length=25, choices=Source.choices, default=Source.MENTOR, db_index=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.DEVELOPING)
    score = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)  # e.g. 1.0 to 10.0
    evidence = models.TextField(blank=True, default='')
    feedback = models.TextField(blank=True, default='')
    assessor = models.ForeignKey(MentorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_assessments')
    related_submission = models.ForeignKey(TaskSubmission, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    is_provisional = models.BooleanField(default=False)
    assessed_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-assessed_date']

    def __str__(self):
        return f"{self.student.vrcf_id} - {self.competency.name}: {self.get_level_display()} ({self.get_source_display()})"


class SupportAlert(models.Model):
    class AlertType(models.TextChoices):
        MISSED_DEADLINES = 'MISSED_DEADLINES', 'Repeated Missed Deadlines'
        INACTIVITY = 'INACTIVITY', 'Prolonged Inactivity'
        STUDENT_REQUEST = 'STUDENT_REQUEST', 'Student Requested Help'
        MILESTONE_STRUGGLE = 'MILESTONE_STRUGGLE', 'Milestone Difficulty'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        FOLLOWED_UP = 'FOLLOWED_UP', 'Followed Up'
        DISMISSED = 'DISMISSED', 'Dismissed'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='support_alerts')
    alert_type = models.CharField(max_length=30, choices=AlertType.choices, default=AlertType.INACTIVITY)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    explanation = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    acknowledged_by = models.ForeignKey(MentorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    follow_up_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_severity_display()} Alert] {self.student.name}: {self.get_alert_type_display()}"
