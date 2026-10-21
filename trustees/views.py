from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg

from core.decorators import trustee_required
from core.models import Notification, AuditEvent
from students.models import StudentProfile, Goal, LearningMilestone, Competency
from mentors.models import (
    MentorProfile, MentorStudentAssignment, MentorTask,
    TaskSubmission, CompetencyAssessment, SupportAlert
)
from trustees.models import TrusteeProfile, TrusteeFeedback


def get_trustee_or_admin_profile(user):
    profile = getattr(user, 'trustee_profile', None)
    if not profile:
        profile, _ = TrusteeProfile.objects.get_or_create(
            user=user,
            defaults={
                'name': user.get_full_name() or user.username,
                'email': user.email or 'trustee@vrcf.org',
                'designation': 'VRCF Foundation Trustee'
            }
        )
    return profile


@trustee_required
def dashboard_view(request):
    trustee = get_trustee_or_admin_profile(request.user)

    # Key organizational metrics
    total_students_count = StudentProfile.objects.count()
    provisioned_accounts_count = StudentProfile.objects.filter(user__isnull=False).count()
    active_mentors_count = MentorProfile.objects.filter(is_active=True).count()
    assigned_students_count = MentorStudentAssignment.objects.filter(is_active=True).values('student').distinct().count()
    
    total_tasks_assigned = MentorTask.objects.count()
    total_tasks_completed = MentorTask.objects.filter(status=MentorTask.Status.REVIEWED).count()
    pending_reviews_count = TaskSubmission.objects.filter(task__status=MentorTask.Status.SUBMITTED).count()
    open_alerts_count = SupportAlert.objects.filter(status=SupportAlert.Status.OPEN).count()

    total_goals_count = Goal.objects.count()
    completed_goals_count = Goal.objects.filter(status=Goal.Status.COMPLETED).count()
    assessed_scholars_count = CompetencyAssessment.objects.values('student').distinct().count()

    # Recent trustee feedback
    recent_feedbacks = TrusteeFeedback.objects.select_related('student', 'trustee').order_by('-created_at')[:5]

    # Cohort breakdown
    cohort_breakdown = StudentProfile.objects.exclude(cohort='').values('cohort').annotate(
        count=Count('id')
    ).order_by('-cohort')

    context = {
        'trustee': trustee,
        'total_students_count': total_students_count,
        'provisioned_accounts_count': provisioned_accounts_count,
        'active_mentors_count': active_mentors_count,
        'assigned_students_count': assigned_students_count,
        'total_tasks_assigned': total_tasks_assigned,
        'total_tasks_completed': total_tasks_completed,
        'pending_reviews_count': pending_reviews_count,
        'open_alerts_count': open_alerts_count,
        'total_goals_count': total_goals_count,
        'completed_goals_count': completed_goals_count,
        'assessed_scholars_count': assessed_scholars_count,
        'recent_feedbacks': recent_feedbacks,
        'cohort_breakdown': cohort_breakdown,
        'active_nav': 'dashboard'
    }
    return render(request, 'trustees/dashboard.html', context)


@trustee_required
def students_list_view(request):
    trustee = get_trustee_or_admin_profile(request.user)
    students_qs = StudentProfile.objects.select_related('user').all()

    q = request.GET.get('q', '').strip()
    if q:
        students_qs = students_qs.filter(
            Q(name__icontains=q) |
            Q(vrcf_id__icontains=q) |
            Q(college_name_district__icontains=q) |
            Q(course_name__icontains=q) |
            Q(cohort__icontains=q)
        )

    cohort = request.GET.get('cohort', '').strip()
    if cohort:
        students_qs = students_qs.filter(cohort=cohort)

    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'vrcf_id':
        students_qs = students_qs.order_by('vrcf_id')
    elif sort_by == 'cohort':
        students_qs = students_qs.order_by('-cohort', 'name')
    else:
        students_qs = students_qs.order_by('name')

    available_cohorts = StudentProfile.objects.exclude(cohort='').values_list('cohort', flat=True).distinct().order_by('-cohort')

    paginator = Paginator(students_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'trustee': trustee,
        'page_obj': page_obj,
        'q': q,
        'selected_cohort': cohort,
        'sort_by': sort_by,
        'available_cohorts': available_cohorts,
        'total_count': students_qs.count(),
        'active_nav': 'students'
    }
    return render(request, 'trustees/students.html', context)


@trustee_required
def student_detail_view(request, student_id):
    trustee = get_trustee_or_admin_profile(request.user)
    student = get_object_or_404(StudentProfile, id=student_id)

    vision = getattr(student, 'vision', None)
    goals = student.goals.all().order_by('-priority', 'target_date')
    milestones = student.milestones.select_related('competency').order_by('order')
    
    assigned_tasks = student.assigned_tasks.select_related('assigned_mentor').order_by('-created_at')
    
    mentor_assessments = CompetencyAssessment.objects.filter(
        student=student, source=CompetencyAssessment.Source.MENTOR
    ).select_related('competency', 'assessor').order_by('-assessed_date')

    sent_feedbacks = TrusteeFeedback.objects.filter(student=student).select_related('trustee').order_by('-created_at')

    context = {
        'trustee': trustee,
        'student': student,
        'vision': vision,
        'goals': goals,
        'milestones': milestones,
        'assigned_tasks': assigned_tasks,
        'mentor_assessments': mentor_assessments,
        'sent_feedbacks': sent_feedbacks,
        'active_nav': 'students'
    }
    return render(request, 'trustees/student_detail.html', context)


@trustee_required
def send_feedback_view(request):
    trustee = get_trustee_or_admin_profile(request.user)
    students = StudentProfile.objects.all().order_by('name')

    preselected_student_id = request.GET.get('student_id')
    preselected_student = None
    if preselected_student_id and preselected_student_id.isdigit():
        preselected_student = StudentProfile.objects.filter(id=int(preselected_student_id)).first()

    student_goals = preselected_student.goals.all() if preselected_student else []

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        goal_id = request.POST.get('linked_goal_id')

        if not student_id or not title or not message:
            messages.error(request, "Please fill in all required fields (Scholar, Title, Message).")
            return redirect('trustee_feedback')

        student = get_object_or_404(StudentProfile, id=student_id)
        linked_goal = Goal.objects.filter(id=goal_id, student=student).first() if goal_id else None

        feedback = TrusteeFeedback.objects.create(
            trustee=trustee,
            student=student,
            title=title,
            message=message,
            linked_goal=linked_goal
        )

        # Notify student
        if student.user:
            Notification.objects.create(
                recipient=student.user,
                notification_type=Notification.NotificationType.FEEDBACK_RECEIVED,
                title=f"Message from Foundation Trustee: {title}",
                message=f"Trustee {trustee.name}: {message[:120]}...",
                link="/student/dashboard/#trustee-feedback"
            )

        AuditEvent.objects.create(
            actor=request.user,
            event_type='TRUSTEE_FEEDBACK_SENT',
            description=f"Trustee {trustee.name} sent feedback to scholar {student.name} ({student.vrcf_id})."
        )

        messages.success(request, f"Feedback successfully delivered to {student.name}.")
        return redirect('trustee_feedback')

    all_feedbacks = TrusteeFeedback.objects.select_related('student', 'trustee').order_by('-created_at')[:20]

    context = {
        'trustee': trustee,
        'students': students,
        'preselected_student': preselected_student,
        'student_goals': student_goals,
        'all_feedbacks': all_feedbacks,
        'active_nav': 'feedback'
    }
    return render(request, 'trustees/feedback.html', context)


@trustee_required
def mentors_view(request):
    trustee = get_trustee_or_admin_profile(request.user)
    
    mentors = MentorProfile.objects.filter(is_active=True).annotate(
        assigned_scholars_count=Count('student_assignments', filter=Q(student_assignments__is_active=True), distinct=True),
        tasks_created_count=Count('created_tasks', distinct=True),
        reviews_conducted_count=Count('reviewed_submissions', distinct=True)
    ).order_by('name')

    total_assignments = MentorStudentAssignment.objects.filter(is_active=True).count()
    unassigned_scholars = StudentProfile.objects.exclude(
        id__in=MentorStudentAssignment.objects.filter(is_active=True).values_list('student_id', flat=True)
    ).count()

    context = {
        'trustee': trustee,
        'mentors': mentors,
        'total_assignments': total_assignments,
        'unassigned_scholars': unassigned_scholars,
        'active_nav': 'mentors'
    }
    return render(request, 'trustees/mentors.html', context)


@trustee_required
def analytics_view(request):
    trustee = get_trustee_or_admin_profile(request.user)
    context = {
        'trustee': trustee,
        'active_nav': 'analytics'
    }
    return render(request, 'trustees/analytics.html', context)


@trustee_required
def analytics_api(request):
    """
    Returns live database aggregates for Chart.js in the trustee portal.
    Never returns fabricated or static mock statistics.
    """
    # 1. Cohort distribution
    cohort_data = StudentProfile.objects.exclude(cohort='').values('cohort').annotate(
        count=Count('id')
    ).order_by('cohort')
    cohort_labels = [c['cohort'] for c in cohort_data]
    cohort_counts = [c['count'] for c in cohort_data]

    # 2. Competency assessment coverage
    competencies = Competency.objects.all().order_by('order')
    comp_labels = [c.name for c in competencies]
    mentor_assessment_counts = []
    ai_assessment_counts = []

    for c in competencies:
        m_count = CompetencyAssessment.objects.filter(competency=c, source=CompetencyAssessment.Source.MENTOR).count()
        ai_count = CompetencyAssessment.objects.filter(competency=c, source=CompetencyAssessment.Source.AI_FORMATIVE).count()
        mentor_assessment_counts.append(m_count)
        ai_assessment_counts.append(ai_count)

    # 3. Task Status Breakdown
    task_statuses = [
        ('ASSIGNED', 'Assigned'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('RESUBMISSION_REQUESTED', 'Revision Requested')
    ]
    task_labels = [s[1] for s in task_statuses]
    task_counts = [MentorTask.objects.filter(status=s[0]).count() for s in task_statuses]

    # 4. Goal Status Breakdown
    goal_statuses = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ]
    goal_labels = [s[1] for s in goal_statuses]
    goal_counts = [Goal.objects.filter(status=s[0]).count() for s in goal_statuses]

    return JsonResponse({
        'cohort': {
            'labels': cohort_labels,
            'counts': cohort_counts
        },
        'competencies': {
            'labels': comp_labels,
            'mentorCounts': mentor_assessment_counts,
            'aiCounts': ai_assessment_counts
        },
        'tasks': {
            'labels': task_labels,
            'counts': task_counts
        },
        'goals': {
            'labels': goal_labels,
            'counts': goal_counts
        }
    })
