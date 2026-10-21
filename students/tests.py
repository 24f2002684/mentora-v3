from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from students.models import (
    StudentProfile, StudentVision, Goal, Competency, LearningMilestone, SelfTask
)
from mentors.models import MentorProfile, MentorTask, TaskSubmission


class StudentExperienceAndIsolationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Password123!"

        # Student A
        self.user_a = User.objects.create_user(
            username="scholar_a", email="a@vrcf.org", password=self.password, role=User.Role.STUDENT
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a, vrcf_id="VRCF-091", name="Scholar A", cohort="2025-2026"
        )

        # Student B
        self.user_b = User.objects.create_user(
            username="scholar_b", email="b@vrcf.org", password=self.password, role=User.Role.STUDENT
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b, vrcf_id="VRCF-092", name="Scholar B", cohort="2025-2026"
        )

        # Mentor
        self.mentor_user = User.objects.create_user(
            username="mentor_lead", email="mentor@vrcf.org", password=self.password, role=User.Role.MENTOR
        )
        self.mentor = MentorProfile.objects.create(
            user=self.mentor_user, name="Lead Mentor", email="mentor@vrcf.org"
        )

        # Competency
        self.comp = Competency.objects.create(
            name="Critical Thinking", code="critical-thinking", description="Objective analysis"
        )

        # Task assigned specifically to Student A
        self.task_a = MentorTask.objects.create(
            assigned_mentor=self.mentor,
            student=self.student_a,
            title="Ethics in AI Case Study",
            instructions="Write a reflective critique",
            due_date=date.today(),
            status=MentorTask.Status.ASSIGNED
        )

    def test_student_dashboard_access(self):
        self.client.login(username="scholar_a", password=self.password)
        res = self.client.get(reverse('student_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Scholar A")
        self.assertContains(res, "VRCF-091")

    def test_student_profile_update(self):
        self.client.login(username="scholar_a", password=self.password)
        res = self.client.post(reverse('student_profile'), {
            'phone_self': '9988776655',
            'email_self': 'scholar_a_new@vrcf.org',
            'home_address': '45 Lake View Road',
            'home_district': 'Coimbatore'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.student_a.refresh_from_db()
        self.assertEqual(self.student_a.phone_self, '9988776655')
        self.assertEqual(self.student_a.home_district, 'Coimbatore')

    def test_goal_creation_and_update(self):
        self.client.login(username="scholar_a", password=self.password)
        res = self.client.post(reverse('student_goal_create'), {
            'title': 'Publish Research Paper on Generative AI',
            'description': 'Target IEEE conference in final year',
            'goal_type': 'LONG_TERM',
            'priority': 'HIGH'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        
        goal = Goal.objects.filter(student=self.student_a, title='Publish Research Paper on Generative AI').first()
        self.assertIsNotNone(goal)
        self.assertEqual(goal.priority, 'HIGH')

        # Update progress
        self.client.post(reverse('student_goal_update', args=[goal.id]), {
            'status': 'IN_PROGRESS',
            'progress_percentage': '75'
        })
        goal.refresh_from_db()
        self.assertEqual(goal.progress_percentage, 75)

    def test_task_submission_by_assigned_student(self):
        self.client.login(username="scholar_a", password=self.password)
        res = self.client.post(reverse('student_task_submit', args=[self.task_a.id]), {
            'submission_text': 'Here is my comprehensive ethical framework analysis...',
            'student_remarks': 'Focused on bias mitigation',
            'save_action': 'submit'
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        self.task_a.refresh_from_db()
        self.assertEqual(self.task_a.status, MentorTask.Status.SUBMITTED)
        self.assertIsNotNone(self.task_a.submission)
        self.assertEqual(self.task_a.submission.student, self.student_a)

    def test_cross_student_isolation_forbidden(self):
        # Student B attempts to submit work for Student A's task
        self.client.login(username="scholar_b", password=self.password)
        res = self.client.post(reverse('student_task_submit', args=[self.task_a.id]), {
            'submission_text': 'Malicious cross-student submission attempt',
            'save_action': 'submit'
        })
        # Must return 404 because student B does not own task_a
        self.assertEqual(res.status_code, 404)
