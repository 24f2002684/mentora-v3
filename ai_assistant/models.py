from django.db import models
from students.models import StudentProfile, Competency


class AIConversation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='ai_conversations')
    title = models.CharField(max_length=255, default='Socratic Mentoring Session')
    focus_competency = models.ForeignKey(Competency, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    is_archived = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.vrcf_id}: {self.title}"


class AIMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'Student'
        MODEL = 'model', 'Mentora AI'
        SYSTEM = 'system', 'System Instructions'

    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=15, choices=Role.choices, default=Role.USER)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)
    model_name = models.CharField(max_length=60, default='gemini-2.5-flash')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}..."


class StructuredActivity(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Foundation / Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Developing / Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced / Leadership'

    class Status(models.TextChoices):
        SUGGESTED = 'SUGGESTED', 'Suggested'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        REJECTED = 'REJECTED', 'Dismissed'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='structured_activities')
    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_activities')
    title = models.CharField(max_length=255)
    objective = models.TextField()
    instructions = models.TextField()
    difficulty = models.CharField(max_length=15, choices=Difficulty.choices, default=Difficulty.INTERMEDIATE)
    competency = models.ForeignKey(Competency, on_delete=models.SET_NULL, null=True, blank=True)
    deliverable_prompt = models.TextField(blank=True, default='')
    student_response = models.TextField(blank=True, default='')
    reflection_response = models.TextField(blank=True, default='')
    ai_formative_feedback = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUGGESTED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Activity [{self.get_difficulty_display()}]: {self.title} for {self.student.name}"
