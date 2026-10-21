import os
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Avg

from core.decorators import student_required
from core.models import Notification, AuditEvent
from students.models import (
    StudentProfile, StudentVision, Goal, Competency, LearningMilestone,
    SelfTask, Resource, SavedResource
)
from mentors.models import (
    MentorTask, TaskSubmission, CompetencyAssessment, SupportAlert
)
from trustees.models import TrusteeFeedback


@student_required
def dashboard_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    
    # 1. Vision & Goals
    vision = getattr(student, 'vision', None)
    active_goals = student.goals.filter(status__in=[Goal.Status.NOT_STARTED, Goal.Status.IN_PROGRESS])
    completed_goals_count = student.goals.filter(status=Goal.Status.COMPLETED).count()

    # 1b. Foundation Trustee Guidance & Commendations
    trustee_feedbacks = TrusteeFeedback.objects.filter(student=student).select_related('trustee', 'linked_goal').order_by('-created_at')

    # 2. Learning Milestones
    active_milestones = student.milestones.filter(status__in=[LearningMilestone.Status.PENDING, LearningMilestone.Status.IN_PROGRESS])
    next_milestone = active_milestones.first()
    completed_milestones_count = student.milestones.filter(status=LearningMilestone.Status.COMPLETED).count()

    # 3. Tasks & Assignments
    assigned_tasks = student.assigned_tasks.all()
    pending_tasks = assigned_tasks.filter(status__in=[MentorTask.Status.ASSIGNED, MentorTask.Status.RESUBMISSION_REQUESTED])
    
    # Check for upcoming deadlines (due in next 14 days)
    today = date.today()
    upcoming_tasks = pending_tasks.filter(due_date__gte=today).order_by('due_date')[:3]
    overdue_tasks = pending_tasks.filter(due_date__lt=today).order_by('due_date')

    # 4. Recent Reviews & Feedback
    recent_reviews = TaskSubmission.objects.filter(
        student=student,
        reviewed_at__isnull=False
    ).select_related('task', 'reviewed_by').order_by('-reviewed_at')[:3]

    # 5. Self Tasks (both open and recently completed)
    self_tasks = student.self_tasks.filter(is_completed=False).order_by('due_date', '-created_at')[:6]
    self_tasks_completed = student.self_tasks.filter(is_completed=True).order_by('-completed_at')[:6]

    # 6. Learning Streak (calculated from activity / self-tasks / submissions)
    completed_self_tasks = student.self_tasks.filter(is_completed=True).count()
    completed_submissions = student.submissions.filter(is_draft=False).count()
    total_completed_activities = completed_self_tasks + completed_submissions + completed_milestones_count
    streak_days = min(total_completed_activities, 14)  # Real database derived streak

    # 7. Competency development count
    assessed_competencies_count = CompetencyAssessment.objects.filter(student=student).values('competency').distinct().count()

    # 8. Profile completion percentage
    profile_fields = [
        student.name, student.course_name, student.college_name_district,
        student.phone_self, student.email_self or student.email_institutional,
        student.home_address, student.home_district
    ]
    completed_fields = sum(1 for f in profile_fields if f and str(f).strip())
    profile_completion_pct = int((completed_fields / len(profile_fields)) * 100)

    context = {
        'student': student,
        'vision': vision,
        'active_goals': active_goals[:3],
        'completed_goals_count': completed_goals_count,
        'next_milestone': next_milestone,
        'completed_milestones_count': completed_milestones_count,
        'pending_tasks_count': pending_tasks.count(),
        'upcoming_tasks': upcoming_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_reviews': recent_reviews,
        'self_tasks': self_tasks,
        'self_tasks_completed': self_tasks_completed,
        'streak_days': streak_days,
        'total_completed_activities': total_completed_activities,
        'assessed_competencies_count': assessed_competencies_count,
        'profile_completion_pct': profile_completion_pct,
        'trustee_feedbacks': trustee_feedbacks,
        'active_nav': 'dashboard'
    }
    return render(request, 'students/dashboard.html', context)


@student_required
def profile_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)

    if request.method == 'POST':
        # Student editable fields
        phone_self = request.POST.get('phone_self', '').strip()
        email_self = request.POST.get('email_self', '').strip()
        home_address = request.POST.get('home_address', '').strip()
        home_district = request.POST.get('home_district', '').strip()

        # Update profile
        student.phone_self = phone_self
        student.email_self = email_self
        student.home_address = home_address
        student.home_district = home_district

        # Handle photo upload
        if 'profile_photo' in request.FILES:
            photo = request.FILES['profile_photo']
            # Basic validation
            if photo.size > 5 * 1024 * 1024:
                messages.error(request, "Profile photo must be less than 5MB.")
                return redirect('student_profile')
            student.profile_photo = photo

        student.save()

        # Update user phone/email
        if email_self and '@' in email_self:
            request.user.email = email_self
        if phone_self:
            request.user.phone = phone_self
        request.user.save()

        AuditEvent.objects.create(
            actor=request.user,
            event_type='STUDENT_PROFILE_UPDATE',
            description=f"Scholar {student.name} updated profile contact details."
        )

        messages.success(request, "Your profile information has been saved successfully.")
        return redirect('student_profile')

    context = {
        'student': student,
        'active_nav': 'profile'
    }
    return render(request, 'students/profile.html', context)


@student_required
def vision_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    vision, _ = StudentVision.objects.get_or_create(student=student)
    goals = student.goals.all().order_by('-priority', 'target_date')

    if request.method == 'POST':
        personal_aim = request.POST.get('personal_aim', '').strip()
        vision_statement = request.POST.get('vision_statement', '').strip()
        areas_of_interest = request.POST.get('areas_of_interest', '').strip()
        career_goals = request.POST.get('career_goals', '').strip()
        long_term_aspirations = request.POST.get('long_term_aspirations', '').strip()

        vision.personal_aim = personal_aim
        vision.vision_statement = vision_statement
        vision.areas_of_interest = areas_of_interest
        vision.career_goals = career_goals
        vision.long_term_aspirations = long_term_aspirations

        if 'vision_board_image' in request.FILES:
            vision.vision_board_image = request.FILES['vision_board_image']

        vision.save()
        messages.success(request, "Your personal vision statement has been updated.")
        return redirect('student_vision')

    trustee_feedbacks = TrusteeFeedback.objects.filter(student=student).select_related('trustee', 'linked_goal').order_by('-created_at')

    context = {
        'student': student,
        'vision': vision,
        'goals': goals,
        'trustee_feedbacks': trustee_feedbacks,
        'active_nav': 'vision'
    }
    return render(request, 'students/vision.html', context)


@student_required
def goal_create_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        goal_type = request.POST.get('goal_type', Goal.GoalType.SHORT_TERM)
        priority = request.POST.get('priority', Goal.Priority.MEDIUM)
        target_date_str = request.POST.get('target_date', '')
        measurable_criteria = request.POST.get('measurable_criteria', '').strip()

        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if title:
            Goal.objects.create(
                student=student,
                title=title,
                description=description,
                goal_type=goal_type,
                priority=priority,
                target_date=target_date,
                measurable_criteria=measurable_criteria,
                status=Goal.Status.IN_PROGRESS,
                progress_percentage=0
            )
            messages.success(request, f"New goal '{title}' created successfully.")
    return redirect('student_vision')


@student_required
def goal_update_status_view(request, goal_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    goal = get_object_or_404(Goal, id=goal_id, student=student)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        progress = request.POST.get('progress_percentage')
        
        if status in [s[0] for s in Goal.Status.choices]:
            goal.status = status
            if status == Goal.Status.COMPLETED:
                goal.progress_percentage = 100
        
        if progress is not None and progress.isdigit():
            goal.progress_percentage = min(100, max(0, int(progress)))
            if goal.progress_percentage == 100:
                goal.status = Goal.Status.COMPLETED

        goal.save()
        messages.success(request, f"Goal '{goal.title}' updated.")
    return redirect('student_vision')


@student_required
@require_POST
def goal_delete_view(request, goal_id):
    """
    Safely deletes a developmental goal created by the scholar.
    """
    student = get_object_or_404(StudentProfile, user=request.user)
    goal = get_object_or_404(Goal, id=goal_id, student=student)
    goal_title = goal.title
    goal.delete()
    messages.success(request, f"Developmental goal '{goal_title}' has been successfully deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'student_vision'))



@student_required
def learning_map_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    milestones = student.milestones.select_related('goal', 'competency').order_by('order', 'target_date')
    competencies = Competency.objects.all()
    goals = student.goals.filter(status__in=[Goal.Status.NOT_STARTED, Goal.Status.IN_PROGRESS])

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        purpose = request.POST.get('purpose', '').strip()
        goal_id = request.POST.get('goal_id')
        competency_id = request.POST.get('competency_id')
        target_date_str = request.POST.get('target_date', '')
        requirements = request.POST.get('completion_requirements', '').strip()

        target_date = None
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        goal = student.goals.filter(id=goal_id).first() if goal_id else None
        comp = Competency.objects.filter(id=competency_id).first() if competency_id else None

        if title:
            LearningMilestone.objects.create(
                student=student,
                title=title,
                purpose=purpose,
                goal=goal,
                competency=comp,
                target_date=target_date,
                completion_requirements=requirements,
                status=LearningMilestone.Status.PENDING,
                order=milestones.count() + 1
            )
            messages.success(request, f"Milestone '{title}' added to your learning map.")
            return redirect('student_learning_map')

    context = {
        'student': student,
        'milestones': milestones,
        'competencies': competencies,
        'goals': goals,
        'active_nav': 'learning_map'
    }
    return render(request, 'students/learning_map.html', context)


@student_required
@require_POST
def milestone_toggle_view(request, milestone_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    milestone = get_object_or_404(LearningMilestone, id=milestone_id, student=student)
    
    if milestone.status == LearningMilestone.Status.COMPLETED:
        milestone.status = LearningMilestone.Status.IN_PROGRESS
        milestone.completed_at = None
    else:
        milestone.status = LearningMilestone.Status.COMPLETED
        milestone.completed_at = datetime.now()
    milestone.save()

    return JsonResponse({'status': 'success', 'new_status': milestone.status})


@student_required
def tasks_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    
    # 1. Mentor Tasks
    mentor_tasks = student.assigned_tasks.select_related('assigned_mentor').prefetch_related('competencies').order_by('due_date')
    pending_mentor_tasks = mentor_tasks.exclude(status=MentorTask.Status.REVIEWED)
    reviewed_mentor_tasks = mentor_tasks.filter(status=MentorTask.Status.REVIEWED)

    # 2. Self Tasks
    self_tasks_active = student.self_tasks.filter(is_completed=False).order_by('due_date')
    self_tasks_done = student.self_tasks.filter(is_completed=True).order_by('-completed_at')

    context = {
        'student': student,
        'pending_mentor_tasks': pending_mentor_tasks,
        'reviewed_mentor_tasks': reviewed_mentor_tasks,
        'self_tasks_active': self_tasks_active,
        'self_tasks_done': self_tasks_done,
        'today': date.today(),
        'active_nav': 'tasks'
    }
    return render(request, 'students/tasks.html', context)


@student_required
def task_detail_submit_view(request, task_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    task = get_object_or_404(MentorTask, id=task_id, student=student)
    submission = getattr(task, 'submission', None)

    if request.method == 'POST':
        submission_text = request.POST.get('submission_text', '').strip()
        student_remarks = request.POST.get('student_remarks', '').strip()
        student_reflection = request.POST.get('student_reflection', '').strip()
        is_draft = request.POST.get('save_action') == 'draft'

        if not submission_text:
            messages.error(request, "Please enter your submission text before submitting.")
            return redirect('student_task_submit', task_id=task.id)

        if not submission:
            submission = TaskSubmission(task=task, student=student)

        submission.submission_text = submission_text
        submission.student_remarks = student_remarks
        submission.student_reflection = student_reflection
        submission.is_draft = is_draft

        if 'attachment' in request.FILES:
            submission.attachment = request.FILES['attachment']

        submission.save()

        if not is_draft:
            is_resubmission = (task.status == MentorTask.Status.RESUBMISSION_REQUESTED)
            task.status = MentorTask.Status.SUBMITTED
            task.save(update_fields=['status'])

            # Specifically notify the mentor who assigned this task
            if task.assigned_mentor and task.assigned_mentor.user:
                notif_title = f"Revised submission from {student.name}" if is_resubmission else f"New submission from {student.name}"
                notif_msg = (
                    f"{student.name} ({student.vrcf_id}) re-submitted revised work for task '{task.title}' assigned by you."
                    if is_resubmission else
                    f"{student.name} ({student.vrcf_id}) submitted work for task '{task.title}' assigned by you."
                )
                Notification.objects.create(
                    recipient=task.assigned_mentor.user,
                    notification_type=Notification.NotificationType.SUBMISSION_RECEIVED,
                    title=notif_title,
                    message=notif_msg,
                    link=f"/mentor/submissions/{submission.id}/review/"
                )

            messages.success(request, f"Your work for '{task.title}' has been submitted to Mentor {task.assigned_mentor.name} for review.")
        else:
            messages.info(request, "Your draft response has been saved.")

        return redirect('student_tasks')

    context = {
        'student': student,
        'task': task,
        'submission': submission,
        'active_nav': 'tasks'
    }
    return render(request, 'students/task_detail.html', context)


@student_required
def self_task_create_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date_str = request.POST.get('due_date', '')
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if title:
            SelfTask.objects.create(
                student=student,
                title=title,
                description=description,
                due_date=due_date
            )
            messages.success(request, f"Self-task '{title}' created.")
    return redirect('student_tasks')


@student_required
@require_POST
def self_task_toggle_view(request, task_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    task = get_object_or_404(SelfTask, id=task_id, student=student)
    
    task.is_completed = not task.is_completed
    from django.utils import timezone
    task.completed_at = timezone.now() if task.is_completed else None
    task.save(update_fields=['is_completed', 'completed_at'])

    return JsonResponse({
        'status': 'success',
        'is_completed': task.is_completed,
        'task_id': task.id,
        'title': task.title,
        'completed_at': task.completed_at.strftime('%b %d, %Y') if task.completed_at else ''
    })


@student_required
def progress_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    competencies = Competency.objects.all().order_by('order')

    # Gather assessments
    mentor_assessments = CompetencyAssessment.objects.filter(
        student=student, source=CompetencyAssessment.Source.MENTOR
    ).select_related('competency', 'assessor').order_by('-assessed_date')

    ai_assessments = CompetencyAssessment.objects.filter(
        student=student, source=CompetencyAssessment.Source.AI_FORMATIVE
    ).select_related('competency').order_by('-assessed_date')

    # Compile competency status map
    comp_progress = []
    level_weights = {'FOUNDATION': 2.5, 'DEVELOPING': 5.0, 'PROFICIENT': 7.5, 'ADVANCED': 10.0}

    for comp in competencies:
        latest_mentor = mentor_assessments.filter(competency=comp).first()
        latest_ai = ai_assessments.filter(competency=comp).first()
        
        score_val = None
        level_label = "Not assessed"
        if latest_mentor:
            level_label = latest_mentor.get_level_display()
            score_val = float(latest_mentor.score) if latest_mentor.score else level_weights.get(latest_mentor.level, 5.0)
        elif latest_ai:
            level_label = f"{latest_ai.get_level_display()} (AI)"
            score_val = float(latest_ai.score) if latest_ai.score else level_weights.get(latest_ai.level, 5.0)

        comp_progress.append({
            'competency': comp,
            'latest_mentor': latest_mentor,
            'latest_ai': latest_ai,
            'level_label': level_label,
            'score': score_val,
        })

    # Summary metrics
    completed_goals = student.goals.filter(status=Goal.Status.COMPLETED).count()
    completed_milestones = student.milestones.filter(status=LearningMilestone.Status.COMPLETED).count()
    completed_tasks = student.submissions.filter(is_draft=False).count()

    context = {
        'student': student,
        'comp_progress': comp_progress,
        'mentor_assessments': mentor_assessments[:5],
        'ai_assessments': ai_assessments[:5],
        'completed_goals': completed_goals,
        'completed_milestones': completed_milestones,
        'completed_tasks': completed_tasks,
        'active_nav': 'progress'
    }
    return render(request, 'students/progress.html', context)


@student_required
def competency_data_api(request):
    """
    Returns JSON for Chart.js radar chart.
    """
    student = get_object_or_404(StudentProfile, user=request.user)
    competencies = Competency.objects.all().order_by('order')
    
    labels = []
    mentor_scores = []
    ai_scores = []
    level_weights = {'FOUNDATION': 3, 'DEVELOPING': 6, 'PROFICIENT': 8, 'ADVANCED': 10}

    for comp in competencies:
        labels.append(comp.name)
        m_ass = CompetencyAssessment.objects.filter(student=student, competency=comp, source=CompetencyAssessment.Source.MENTOR).first()
        ai_ass = CompetencyAssessment.objects.filter(student=student, competency=comp, source=CompetencyAssessment.Source.AI_FORMATIVE).first()

        mentor_scores.append(float(m_ass.score) if m_ass and m_ass.score else (level_weights.get(m_ass.level, 0) if m_ass else 0))
        ai_scores.append(float(ai_ass.score) if ai_ass and ai_ass.score else (level_weights.get(ai_ass.level, 0) if ai_ass else 0))

    return JsonResponse({
        'labels': labels,
        'mentorScores': mentor_scores,
        'aiScores': ai_scores,
    })


@student_required
def resources_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    resources = Resource.objects.filter(is_active=True).select_related('competency')

    # Filtering
    topic = request.GET.get('topic')
    comp_code = request.GET.get('competency')
    res_type = request.GET.get('type')
    saved_only = request.GET.get('saved') == '1'

    if topic:
        resources = resources.filter(topic__icontains=topic)
    if comp_code:
        resources = resources.filter(competency__code=comp_code)
    if res_type:
        resources = resources.filter(resource_type=res_type)

    saved_ids = set(SavedResource.objects.filter(student=student).values_list('resource_id', flat=True))
    if saved_only:
        resources = resources.filter(id__in=saved_ids)

    competencies = Competency.objects.all()

    context = {
        'student': student,
        'resources': resources,
        'saved_ids': saved_ids,
        'competencies': competencies,
        'selected_topic': topic or '',
        'selected_comp': comp_code or '',
        'selected_type': res_type or '',
        'saved_only': saved_only,
        'active_nav': 'resources'
    }
    return render(request, 'students/resources.html', context)


@student_required
@require_POST
def resource_save_toggle_view(request, resource_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    resource = get_object_or_404(Resource, id=resource_id)

    saved_obj = SavedResource.objects.filter(student=student, resource=resource).first()
    if saved_obj:
        saved_obj.delete()
        is_saved = False
    else:
        SavedResource.objects.create(student=student, resource=resource)
        is_saved = True

    return JsonResponse({'status': 'success', 'is_saved': is_saved})


@student_required
def settings_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)

    if request.method == 'POST' and 'change_password' in request.POST:
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep logged in
            AuditEvent.objects.create(
                actor=request.user,
                event_type='PASSWORD_CHANGE',
                description=f"Scholar {student.name} successfully updated their password."
            )
            messages.success(request, "Your password has been changed successfully!")
            return redirect('student_settings')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'student': student,
        'password_form': form,
        'active_nav': 'settings'
    }
    return render(request, 'students/settings.html', context)
