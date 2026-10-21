from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from students.models import StudentProfile, Competency
from mentors.models import (
    MentorProfile, MentorStudentAssignment, MentorTask,
    TaskSubmission, CompetencyAssessment, SupportAlert
)


class MentorWorkflowAndReportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "MentorPass123!"

        self.mentor_user = User.objects.create_user(
            username="mentor_lead", email="mentor@vrcf.org", password=self.password, role=User.Role.MENTOR
        )
        self.mentor = MentorProfile.objects.create(
            user=self.mentor_user, name="VRCF Mentor Lead", email="mentor@vrcf.org"
        )

        self.student_user = User.objects.create_user(
            username="scholar_001", email="scholar1@vrcf.org", password=self.password, role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user, vrcf_id="VRCF-001", name="Arun Kumar", cohort="2025-2026",
            course_name="B.E. Computer Science", college_name_district="CIT Coimbatore"
        )

        # Assignment
        MentorStudentAssignment.objects.create(
            mentor=self.mentor, student=self.student, is_active=True
        )

        self.comp = Competency.objects.create(
            name="Problem Solving", code="problem-solving", description="Algorithmic reasoning"
        )

        # Task and submission
        self.task = MentorTask.objects.create(
            assigned_mentor=self.mentor,
            student=self.student,
            title="Data Structures Algorithmic Challenge",
            instructions="Implement dynamic programming",
            due_date=date.today(),
            status=MentorTask.Status.SUBMITTED
        )
        self.submission = TaskSubmission.objects.create(
            task=self.task,
            student=self.student,
            submission_text="Here is the memoized solution with O(N) complexity."
        )

    def test_mentor_dashboard_data(self):
        self.client.login(username="mentor_lead", password=self.password)
        res = self.client.get(reverse('mentor_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "VRCF Mentor Lead")
        self.assertContains(res, "Data Structures Algorithmic Challenge")

    def test_mentor_assign_task(self):
        self.client.login(username="mentor_lead", password=self.password)
        res = self.client.post(reverse('mentor_task_assign'), {
            'title': 'Leadership in Engineering Projects',
            'instructions': 'Write a 400-word reflection on cross-functional team coordination',
            'due_date': '2026-11-15',
            'priority': 'HIGH',
            'target_mode': 'specific',
            'student_ids': [self.student.id],
            'competencies': [self.comp.id]
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        created_task = MentorTask.objects.filter(student=self.student, title='Leadership in Engineering Projects').first()
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task.priority, 'HIGH')
        self.assertTrue(created_task.competencies.filter(id=self.comp.id).exists())

    def test_mentor_submission_review_and_competency_assessment(self):
        self.client.login(username="mentor_lead", password=self.password)
        res = self.client.post(reverse('mentor_submission_review', args=[self.submission.id]), {
            'mentor_rating': '5',
            'mentor_feedback': 'Exceptional algorithmic efficiency and clean code structure.',
            'strengths': 'Optimal time and space trade-offs demonstrated.',
            'areas_for_improvement': 'Consider documenting edge cases.',
            'evaluated_competencies': [self.comp.id],
            f'comp_level_{self.comp.id}': 'ADVANCED',
            f'comp_score_{self.comp.id}': '9.5',
            f'comp_evidence_{self.comp.id}': 'Code implementation of DP table'
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        self.submission.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, MentorTask.Status.REVIEWED)
        self.assertEqual(self.submission.mentor_rating, 5)

        # Verify official mentor assessment was recorded
        assessment = CompetencyAssessment.objects.filter(
            student=self.student,
            competency=self.comp,
            source=CompetencyAssessment.Source.MENTOR
        ).first()
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.level, 'ADVANCED')
        self.assertEqual(float(assessment.score), 9.5)

    def test_download_growth_pdf_report(self):
        self.client.login(username="mentor_lead", password=self.password)
        res = self.client.get(reverse('mentor_report_download', args=[self.student.id]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertTrue(res['Content-Disposition'].startswith('attachment; filename='))
        # Ensure PDF magic bytes %PDF
        self.assertTrue(res.content.startswith(b'%PDF'))
