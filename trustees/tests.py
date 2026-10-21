from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Notification
from students.models import StudentProfile, Goal, Competency
from trustees.models import TrusteeProfile, TrusteeFeedback


class TrusteeGovernanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "TrusteePass123!"

        self.trustee_user = User.objects.create_user(
            username="trustee_exec", email="trustee@vrcf.org", password=self.password, role=User.Role.TRUSTEE
        )
        self.trustee = TrusteeProfile.objects.create(
            user=self.trustee_user, name="VRCF Managing Trustee", email="trustee@vrcf.org"
        )

        self.student_user = User.objects.create_user(
            username="scholar_001", email="scholar1@vrcf.org", password=self.password, role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, vrcf_id="VRCF-001", name="Deepa M", cohort="2025-2026",
            course_name="B.Sc Mathematics", college_name_district="PSG CAS Coimbatore"
        )

        self.goal = Goal.objects.create(
            student=self.student, title="Master Data Science Foundations", status=Goal.Status.IN_PROGRESS
        )

    def test_trustee_dashboard_metrics(self):
        self.client.login(username="trustee_exec", password=self.password)
        res = self.client.get(reverse('trustee_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "VRCF Managing Trustee")
        self.assertContains(res, "Total VRCF Scholars")

    def test_send_trustee_feedback_and_notification(self):
        self.client.login(username="trustee_exec", password=self.password)
        res = self.client.post(reverse('trustee_feedback'), {
            'student_id': self.student.id,
            'title': 'Commendation on Quantitative Aptitude',
            'message': 'Keep up the exemplary focus on analytical thinking and mathematical rigor.',
            'linked_goal_id': self.goal.id
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        # Check TrusteeFeedback record
        fb = TrusteeFeedback.objects.filter(student=self.student, title='Commendation on Quantitative Aptitude').first()
        self.assertIsNotNone(fb)
        self.assertEqual(fb.trustee, self.trustee)
        self.assertEqual(fb.linked_goal, self.goal)

        # Check in-app notification delivered to student user
        notif = Notification.objects.filter(recipient=self.student_user).first()
        self.assertIsNotNone(notif)
        self.assertIn("Message from Foundation Trustee", notif.title)

    def test_trustee_analytics_api(self):
        self.client.login(username="trustee_exec", password=self.password)
        res = self.client.get(reverse('trustee_analytics_api'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('cohort', data)
        self.assertIn('competencies', data)
        self.assertIn('tasks', data)
        self.assertIn('goals', data)
        self.assertIn('2025-2026', data['cohort']['labels'])
