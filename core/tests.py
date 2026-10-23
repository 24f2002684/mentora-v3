from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Notification, AuditEvent
from students.models import StudentProfile
from mentors.models import MentorProfile
from trustees.models import TrusteeProfile


class AuthenticationAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "Secr3t!P@ssword"
        
        self.student_user = User.objects.create_user(
            username="scholar_001",
            email="scholar001@vrcf.org",
            password=self.password,
            role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            vrcf_id="VRCF-001",
            name="Test Scholar",
            cohort="2025-2026"
        )

        self.mentor_user = User.objects.create_user(
            username="mentor_lead",
            email="mentor@vrcf.org",
            password=self.password,
            role=User.Role.MENTOR
        )
        self.mentor = MentorProfile.objects.create(
            user=self.mentor_user,
            name="Test Mentor",
            email="mentor@vrcf.org"
        )

        self.trustee_user = User.objects.create_user(
            username="trustee_gov",
            email="trustee@vrcf.org",
            password=self.password,
            role=User.Role.TRUSTEE
        )
        self.trustee = TrusteeProfile.objects.create(
            user=self.trustee_user,
            name="Test Trustee",
            email="trustee@vrcf.org"
        )

    def test_login_with_username(self):
        response = self.client.post(reverse('auth_login'), {
            'username': 'scholar_001',
            'password': self.password
        }, follow=True)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.role, User.Role.STUDENT)

    def test_login_with_email(self):
        response = self.client.post(reverse('auth_login'), {
            'username': 'scholar001@vrcf.org',
            'password': self.password
        }, follow=True)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('auth_login'), {
            'username': 'scholar_001',
            'password': 'WrongPassword123'
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_role_based_redirects(self):
        # Student redirect
        self.client.login(username='scholar_001', password=self.password)
        res = self.client.get(reverse('role_redirect'))
        self.assertRedirects(res, reverse('student_dashboard'))
        self.client.logout()

        # Mentor redirect
        self.client.login(username='mentor_lead', password=self.password)
        res = self.client.get(reverse('role_redirect'))
        self.assertRedirects(res, reverse('mentor_dashboard'))
        self.client.logout()

        # Trustee redirect
        self.client.login(username='trustee_gov', password=self.password)
        res = self.client.get(reverse('role_redirect'))
        self.assertRedirects(res, reverse('trustee_dashboard'))

    def test_unauthorized_access_protection(self):
        # Unauthenticated redirect to login
        res = self.client.get(reverse('student_dashboard'))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.url.startswith('/auth/login/'))

        # Student attempting to access mentor dashboard
        self.client.login(username='scholar_001', password=self.password)
        res = self.client.get(reverse('mentor_dashboard'))
        # Should be redirected to student dashboard
        self.assertRedirects(res, reverse('student_dashboard'))

    def test_remember_me_session_setting(self):
        response = self.client.post(reverse('auth_login'), {
            'username': 'scholar_001',
            'password': self.password,
            'remember_me': 'on'
        })
        self.assertEqual(self.client.session.get_expiry_age(), 60 * 60 * 24 * 30)

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'ok')

    def test_db_health_check_endpoint(self):
        response = self.client.get(reverse('health_check_db'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')
