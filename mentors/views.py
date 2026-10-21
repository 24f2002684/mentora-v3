import io
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_POST

from core.decorators import mentor_required
from core.models import Notification, AuditEvent
from students.models import StudentProfile, Goal, LearningMilestone, Competency
from mentors.models import (
    MentorProfile, MentorStudentAssignment, MentorTask,
    TaskSubmission, CompetencyAssessment, SupportAlert
)
from mentors.reports import generate_student_growth_pdf


def get_mentor_or_admin_profile(user):
    """
    Returns the MentorProfile for the user. If user is ADMIN/Superuser without a profile,
    gets or creates an administrator-mentor profile.
    """
    profile = getattr(user, 'mentor_profile', None)
    if not profile:
        profile, _ = MentorProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': user.get_full_name() or user.username,
                'email': user.email or 'mentor@vrcf.org',
                'designation': 'VRCF Mentor Administrator',
                'organization': 'Vasumathi Ramaswami Centenary Foundation'
            }
        )
    return profile


def get_authorized_students(mentor, user):
    """
    Returns queryset of StudentProfiles that this mentor has authorization to view.
    All mentors (Manikandan, Avanthikaa, Ram Kumar, and VRCF foundation mentors)
    have full access to view, mentor, and assign tasks across all 43 scholars.
    """
    return StudentProfile.objects.all()


@mentor_required
def dashboard_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)

    assigned_students_count = authorized_students.count()
    active_tasks = MentorTask.objects.filter(assigned_mentor=mentor, status=MentorTask.Status.ASSIGNED)
    active_tasks_count = active_tasks.count()
    
    # Submissions awaiting review: show tasks assigned by this mentor, or all if admin/superuser
    my_pending_submissions = TaskSubmission.objects.filter(
        task__assigned_mentor=mentor,
        is_draft=False,
        task__status=MentorTask.Status.SUBMITTED
    ).select_related('student', 'task', 'task__assigned_mentor').order_by('-submitted_at')

    if my_pending_submissions.exists() or not (request.user.is_superuser or request.user.role == 'ADMIN'):
        pending_submissions = my_pending_submissions
    else:
        pending_submissions = TaskSubmission.objects.filter(
            is_draft=False,
            task__status=MentorTask.Status.SUBMITTED
        ).select_related('student', 'task', 'task__assigned_mentor').order_by('-submitted_at')

    pending_reviews_count = pending_submissions.count()

    # Overdue tasks
    today = date.today()
    if request.user.is_superuser or request.user.role == 'ADMIN':
        overdue_tasks_count = MentorTask.objects.filter(
            status__in=[MentorTask.Status.ASSIGNED, MentorTask.Status.RESUBMISSION_REQUESTED],
            due_date__lt=today
        ).count()
    else:
        overdue_tasks_count = MentorTask.objects.filter(
            assigned_mentor=mentor,
            status__in=[MentorTask.Status.ASSIGNED, MentorTask.Status.RESUBMISSION_REQUESTED],
            due_date__lt=today
        ).count()

    # Open support alerts
    open_alerts = SupportAlert.objects.filter(
        student__in=authorized_students,
        status=SupportAlert.Status.OPEN
    ).select_related('student').order_by('-created_at')
    open_alerts_count = open_alerts.count()

    # Recent completed reviews by this mentor (or all if admin)
    recent_reviews = TaskSubmission.objects.filter(
        reviewed_by=mentor,
        reviewed_at__isnull=False
    ).select_related('student', 'task', 'reviewed_by').order_by('-reviewed_at')[:5]

    if not recent_reviews.exists() and (request.user.is_superuser or request.user.role == 'ADMIN'):
        recent_reviews = TaskSubmission.objects.filter(
            reviewed_at__isnull=False
        ).select_related('student', 'task', 'reviewed_by').order_by('-reviewed_at')[:5]

    # Recent student activity
    recent_submissions = pending_submissions[:5]

    context = {
        'mentor': mentor,
        'assigned_students_count': assigned_students_count,
        'active_tasks_count': active_tasks_count,
        'pending_reviews_count': pending_reviews_count,
        'overdue_tasks_count': overdue_tasks_count,
        'open_alerts_count': open_alerts_count,
        'open_alerts': open_alerts[:4],
        'recent_submissions': recent_submissions,
        'recent_reviews': recent_reviews,
        'active_nav': 'dashboard'
    }
    return render(request, 'mentors/dashboard.html', context)


@mentor_required
def students_list_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    students_qs = get_authorized_students(mentor, request.user).select_related('user')

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        students_qs = students_qs.filter(
            Q(name__icontains=q) |
            Q(vrcf_id__icontains=q) |
            Q(college_name_district__icontains=q) |
            Q(course_name__icontains=q) |
            Q(cohort__icontains=q)
        )

    # Cohort filter
    cohort = request.GET.get('cohort', '').strip()
    if cohort:
        students_qs = students_qs.filter(cohort=cohort)

    # Sorting
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'vrcf_id':
        students_qs = students_qs.order_by('vrcf_id')
    elif sort_by == 'cohort':
        students_qs = students_qs.order_by('-cohort', 'name')
    else:
        students_qs = students_qs.order_by('name')

    # Distinct cohorts for filter dropdown
    available_cohorts = StudentProfile.objects.exclude(cohort='').values_list('cohort', flat=True).distinct().order_by('-cohort')

    paginator = Paginator(students_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'mentor': mentor,
        'page_obj': page_obj,
        'q': q,
        'selected_cohort': cohort,
        'sort_by': sort_by,
        'available_cohorts': available_cohorts,
        'total_count': students_qs.count(),
        'active_nav': 'students'
    }
    return render(request, 'mentors/students.html', context)


@mentor_required
def student_detail_view(request, student_id):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)
    student = get_object_or_404(authorized_students, id=student_id)

    vision = getattr(student, 'vision', None)
    goals = student.goals.all().order_by('-priority', 'target_date')
    milestones = student.milestones.select_related('competency').order_by('order')
    
    # Tasks and submissions
    assigned_tasks = student.assigned_tasks.select_related('assigned_mentor').order_by('-created_at')
    submissions = student.submissions.select_related('task').order_by('-submitted_at')
    
    # Assessments
    mentor_assessments = CompetencyAssessment.objects.filter(
        student=student, source=CompetencyAssessment.Source.MENTOR
    ).select_related('competency', 'assessor').order_by('-assessed_date')

    ai_assessments = CompetencyAssessment.objects.filter(
        student=student, source=CompetencyAssessment.Source.AI_FORMATIVE
    ).select_related('competency').order_by('-assessed_date')

    support_alerts = student.support_alerts.all().order_by('-created_at')

    context = {
        'mentor': mentor,
        'student': student,
        'vision': vision,
        'goals': goals,
        'milestones': milestones,
        'assigned_tasks': assigned_tasks,
        'submissions': submissions,
        'mentor_assessments': mentor_assessments,
        'ai_assessments': ai_assessments,
        'support_alerts': support_alerts,
        'active_nav': 'students'
    }
    return render(request, 'mentors/student_detail.html', context)


@mentor_required
def task_assign_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user).order_by('name')
    competencies = Competency.objects.all().order_by('order')

    preselected_student_id = request.GET.get('student_id')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        instructions = request.POST.get('instructions', '').strip()
        deliverables = request.POST.get('deliverables', '').strip()
        due_date_str = request.POST.get('due_date', '')
        priority = request.POST.get('priority', MentorTask.Priority.MEDIUM)
        evaluation_criteria = request.POST.get('evaluation_criteria', '').strip()
        
        target_mode = request.POST.get('target_mode')  # 'all' or 'specific'
        selected_student_ids = request.POST.getlist('student_ids')
        selected_comp_ids = request.POST.getlist('competencies')

        if not title or not instructions or not due_date_str:
            messages.error(request, "Please fill in all required fields (Title, Instructions, Due Date).")
            return redirect('mentor_task_assign')

        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid due date format.")
            return redirect('mentor_task_assign')

        if target_mode == 'all':
            target_students = authorized_students
        else:
            target_students = authorized_students.filter(id__in=selected_student_ids)

        if not target_students.exists():
            messages.error(request, "Please select at least one scholar for this assignment.")
            return redirect('mentor_task_assign')

        comp_objs = Competency.objects.filter(id__in=selected_comp_ids)

        created_count = 0
        for student in target_students:
            task = MentorTask.objects.create(
                assigned_mentor=mentor,
                student=student,
                title=title,
                instructions=instructions,
                deliverables=deliverables,
                due_date=due_date,
                priority=priority,
                evaluation_criteria=evaluation_criteria,
                status=MentorTask.Status.ASSIGNED
            )
            if comp_objs.exists():
                task.competencies.set(comp_objs)

            # In-app notification for scholar
            if student.user:
                Notification.objects.create(
                    recipient=student.user,
                    notification_type=Notification.NotificationType.TASK_ASSIGNED,
                    title=f"New Assignment from {mentor.name}: {title}",
                    message=f"Mentor {mentor.name} assigned you a new development task: '{title}' due on {due_date.strftime('%b %d, %Y')}.",
                    link=f"/student/tasks/{task.id}/"
                )
            created_count += 1

        AuditEvent.objects.create(
            actor=request.user,
            event_type='MENTOR_TASK_ASSIGNED',
            description=f"Mentor {mentor.name} assigned task '{title}' to {created_count} scholar(s)."
        )

        messages.success(request, f"Task successfully assigned to {created_count} scholar(s).")
        return redirect('mentor_dashboard')

    context = {
        'mentor': mentor,
        'authorized_students': authorized_students,
        'competencies': competencies,
        'preselected_student_id': int(preselected_student_id) if preselected_student_id and preselected_student_id.isdigit() else None,
        'active_nav': 'assign_task'
    }
    return render(request, 'mentors/task_assign.html', context)


@mentor_required
def submissions_list_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)

    status_filter = request.GET.get('status', 'all')
    mentor_id = request.GET.get('mentor_id', '')
    q = request.GET.get('q', '').strip()

    submissions_qs = TaskSubmission.objects.filter(
        student__in=authorized_students,
        is_draft=False
    ).select_related('student', 'task', 'task__assigned_mentor', 'reviewed_by').order_by('-submitted_at')

    if status_filter == 'awaiting':
        submissions_qs = submissions_qs.filter(task__status=MentorTask.Status.SUBMITTED)
    elif status_filter == 'reviewed':
        submissions_qs = submissions_qs.filter(task__status=MentorTask.Status.REVIEWED)
    elif status_filter == 'resubmission':
        submissions_qs = submissions_qs.filter(task__status=MentorTask.Status.RESUBMISSION_REQUESTED)

    if mentor_id and mentor_id.isdigit():
        submissions_qs = submissions_qs.filter(task__assigned_mentor_id=int(mentor_id))

    if q:
        submissions_qs = submissions_qs.filter(
            Q(student__name__icontains=q) |
            Q(student__vrcf_id__icontains=q) |
            Q(task__title__icontains=q) |
            Q(task__assigned_mentor__name__icontains=q)
        )

    paginator = Paginator(submissions_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    all_mentors = MentorProfile.objects.filter(is_active=True).order_by('name')

    context = {
        'mentor': mentor,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'selected_mentor_id': int(mentor_id) if mentor_id and mentor_id.isdigit() else None,
        'all_mentors': all_mentors,
        'q': q,
        'total_count': submissions_qs.count(),
        'active_nav': 'submissions'
    }
    return render(request, 'mentors/submissions.html', context)


@mentor_required
def submission_review_view(request, submission_id):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)
    
    submission = get_object_or_404(
        TaskSubmission.objects.select_related('student', 'task'),
        id=submission_id,
        student__in=authorized_students
    )
    task = submission.task
    student = submission.student
    task_competencies = task.competencies.all()
    all_competencies = Competency.objects.all().order_by('order')

    if request.method == 'POST':
        mentor_feedback = request.POST.get('mentor_feedback', '').strip()
        mentor_rating_str = request.POST.get('mentor_rating', '')
        strengths = request.POST.get('strengths', '').strip()
        areas_for_improvement = request.POST.get('areas_for_improvement', '').strip()
        next_action = request.POST.get('next_recommended_action', '').strip()
        request_resubmission = request.POST.get('request_resubmission') == '1'

        if not mentor_feedback:
            messages.error(request, "Please provide written mentor feedback before completing the review.")
            return redirect('mentor_submission_review', submission_id=submission.id)

        mentor_rating = None
        if mentor_rating_str and mentor_rating_str.isdigit():
            mentor_rating = max(1, min(5, int(mentor_rating_str)))

        # Update submission
        submission.reviewed_by = mentor
        submission.mentor_feedback = mentor_feedback
        submission.mentor_rating = mentor_rating
        submission.strengths = strengths
        submission.areas_for_improvement = areas_for_improvement
        submission.next_recommended_action = next_action
        submission.reviewed_at = datetime.now()
        submission.save()

        # Update task status
        if request_resubmission:
            task.status = MentorTask.Status.RESUBMISSION_REQUESTED
            notif_title = f"Resubmission Requested: {task.title}"
            notif_msg = f"Mentor {mentor.name} requested a revision on '{task.title}'. Feedback: {mentor_feedback[:100]}..."
        else:
            task.status = MentorTask.Status.REVIEWED
            notif_title = f"Task Reviewed: {task.title}"
            notif_msg = f"Mentor {mentor.name} reviewed your submission for '{task.title}' with rating {mentor_rating or 'Completed'}/5."

        task.save(update_fields=['status'])

        # Save competency evaluations
        selected_comps = request.POST.getlist('evaluated_competencies')
        for comp_id in selected_comps:
            comp = Competency.objects.filter(id=comp_id).first()
            if comp:
                level = request.POST.get(f'comp_level_{comp_id}', CompetencyAssessment.Level.DEVELOPING)
                score_str = request.POST.get(f'comp_score_{comp_id}', '')
                score = float(score_str) if score_str else None
                evidence = request.POST.get(f'comp_evidence_{comp_id}', f"Observed in submission for task: {task.title}")

                CompetencyAssessment.objects.create(
                    student=student,
                    competency=comp,
                    source=CompetencyAssessment.Source.MENTOR,
                    level=level,
                    score=score,
                    evidence=evidence,
                    feedback=mentor_feedback,
                    assessor=mentor,
                    related_submission=submission,
                    is_provisional=False
                )

        # Notify student
        if student.user:
            Notification.objects.create(
                recipient=student.user,
                notification_type=Notification.NotificationType.REVIEW_PUBLISHED,
                title=notif_title,
                message=notif_msg,
                link=f"/student/tasks/{task.id}/"
            )

        AuditEvent.objects.create(
            actor=request.user,
            event_type='MENTOR_REVIEW_PUBLISHED',
            description=f"Mentor {mentor.name} reviewed submission for '{task.title}' by {student.name}."
        )

        messages.success(request, f"Review for '{task.title}' successfully published.")
        return redirect('mentor_submissions')

    context = {
        'mentor': mentor,
        'submission': submission,
        'task': task,
        'student': student,
        'task_competencies': task_competencies,
        'all_competencies': all_competencies,
        'active_nav': 'submissions'
    }
    return render(request, 'mentors/submission_review.html', context)


@mentor_required
def reports_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user).order_by('name')

    q = request.GET.get('q', '').strip()
    if q:
        authorized_students = authorized_students.filter(
            Q(name__icontains=q) |
            Q(vrcf_id__icontains=q) |
            Q(college_name_district__icontains=q)
        )

    context = {
        'mentor': mentor,
        'students': authorized_students,
        'q': q,
        'active_nav': 'reports'
    }
    return render(request, 'mentors/reports.html', context)


@mentor_required
def download_pdf_report_view(request, student_id):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)
    student = get_object_or_404(authorized_students, id=student_id)

    pdf_buffer = generate_student_growth_pdf(student, assessor_name=mentor.name)
    
    AuditEvent.objects.create(
        actor=request.user,
        event_type='PDF_REPORT_GENERATED',
        description=f"Mentor {mentor.name} generated growth report for {student.name} ({student.vrcf_id})."
    )

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    safe_vrcf_id = student.vrcf_id.replace('/', '_')
    response['Content-Disposition'] = f'attachment; filename="Mentora_Growth_Report_{safe_vrcf_id}.pdf"'
    return response


@mentor_required
def support_alerts_view(request):
    mentor = get_mentor_or_admin_profile(request.user)
    authorized_students = get_authorized_students(mentor, request.user)

    alerts_qs = SupportAlert.objects.filter(
        student__in=authorized_students
    ).select_related('student', 'acknowledged_by').order_by('-created_at')

    status_filter = request.GET.get('status', 'OPEN')
    if status_filter != 'ALL':
        alerts_qs = alerts_qs.filter(status=status_filter)

    if request.method == 'POST':
        action = request.POST.get('action')
        alert_id = request.POST.get('alert_id')
        notes = request.POST.get('follow_up_notes', '').strip()

        if action and alert_id:
            alert = get_object_or_404(SupportAlert, id=alert_id, student__in=authorized_students)
            if action == 'acknowledge':
                alert.status = SupportAlert.Status.ACKNOWLEDGED
                alert.acknowledged_by = mentor
            elif action == 'resolve':
                alert.status = SupportAlert.Status.FOLLOWED_UP
                alert.acknowledged_by = mentor
                alert.resolved_at = datetime.now()
            elif action == 'dismiss':
                alert.status = SupportAlert.Status.DISMISSED

            if notes:
                alert.follow_up_notes = notes
            alert.save()
            messages.success(request, f"Alert for {alert.student.name} updated.")
            return redirect('mentor_support_alerts')

    context = {
        'mentor': mentor,
        'alerts': alerts_qs,
        'status_filter': status_filter,
        'active_nav': 'support_alerts'
    }
    return render(request, 'mentors/support_alerts.html', context)
