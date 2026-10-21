from django.db import models
from django.conf import settings


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    vrcf_id = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150, db_index=True)
    cohort = models.CharField(max_length=50, db_index=True)
    profile_photo = models.ImageField(upload_to='students/photos/', null=True, blank=True)
    course_name = models.CharField(max_length=255, db_index=True)
    year_of_study = models.CharField(max_length=100, blank=True, default='')
    college_name_district = models.CharField(max_length=255, db_index=True)
    college_district = models.CharField(max_length=100, blank=True, default='')
    total_academic_years = models.CharField(max_length=100, blank=True, default='')
    hostel_or_dayscholar = models.CharField(max_length=100, blank=True, default='')
    phone_self = models.CharField(max_length=60, blank=True, default='')
    phone_parents = models.CharField(max_length=100, blank=True, default='')
    email_self = models.EmailField(blank=True, default='')
    email_institutional = models.EmailField(blank=True, default='')
    home_address = models.TextField(blank=True, default='')
    home_district = models.CharField(max_length=100, blank=True, default='')
    tuition_fee_term = models.CharField(max_length=100, blank=True, default='')
    tuition_fee_amount = models.CharField(max_length=100, blank=True, default='')
    hostel_fee = models.CharField(max_length=100, blank=True, default='')
    
    # Tracking
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vrcf_id']

    def __str__(self):
        return f"{self.vrcf_id} - {self.name} ({self.cohort})"

    @property
    def primary_email(self):
        if self.user and self.user.email:
            return self.user.email
        return self.email_self or self.email_institutional

    @property
    def display_phone(self):
        return self.phone_self or (self.user.phone if self.user else '')


class StudentVision(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='vision')
    personal_aim = models.CharField(max_length=255, blank=True, default='')
    vision_statement = models.TextField(blank=True, default='')
    vision_board_image = models.ImageField(upload_to='students/vision_boards/', null=True, blank=True)
    areas_of_interest = models.TextField(blank=True, default='')
    career_goals = models.TextField(blank=True, default='')
    long_term_aspirations = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vision of {self.student.name} ({self.student.vrcf_id})"


class Competency(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=60, unique=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, default='bi-star')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Competencies'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Goal(models.Model):
    class GoalType(models.TextChoices):
        SHORT_TERM = 'SHORT_TERM', 'Short-Term Goal'
        LONG_TERM = 'LONG_TERM', 'Long-Term Goal'

    class Priority(models.TextChoices):
        HIGH = 'HIGH', 'High Priority'
        MEDIUM = 'MEDIUM', 'Medium Priority'
        LOW = 'LOW', 'Low Priority'

    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        ARCHIVED = 'ARCHIVED', 'Archived'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    goal_type = models.CharField(max_length=20, choices=GoalType.choices, default=GoalType.SHORT_TERM)
    category = models.CharField(max_length=100, blank=True, default='')
    target_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    measurable_criteria = models.TextField(blank=True, default='')
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', '-priority', '-created_at']

    def __str__(self):
        return f"{self.student.vrcf_id}: {self.title} ({self.get_status_display()})"


class LearningMilestone(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='milestones')
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='milestones')
    competency = models.ForeignKey(Competency, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    purpose = models.TextField(blank=True, default='')
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    completion_requirements = models.TextField(blank=True, default='')
    completion_evidence = models.TextField(blank=True, default='')
    order = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'target_date', 'id']

    def __str__(self):
        return f"{self.student.vrcf_id} Milestone: {self.title}"


class SelfTask(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='self_tasks')
    goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='self_tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    reflection = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_completed', 'due_date', '-created_at']

    def __str__(self):
        return f"SelfTask [{self.student.vrcf_id}]: {self.title}"


class Resource(models.Model):
    class ResourceType(models.TextChoices):
        ARTICLE = 'ARTICLE', 'Article / Reading'
        VIDEO = 'VIDEO', 'Video / Lecture'
        COURSE = 'COURSE', 'Online Course'
        WEBSITE = 'WEBSITE', 'Educational Website'
        TOOL = 'TOOL', 'Tool / Application'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    url = models.URLField(max_length=500)
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices, default=ResourceType.ARTICLE)
    topic = models.CharField(max_length=120, blank=True, default='')
    competency = models.ForeignKey(Competency, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    career_path = models.CharField(max_length=150, blank=True, default='')
    publisher = models.CharField(max_length=150, blank=True, default='')
    is_verified = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"[{self.get_resource_type_display()}] {self.title}"


class SavedResource(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='saved_resources')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='saved_by_students')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'resource')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.student.vrcf_id} saved {self.resource.title}"
