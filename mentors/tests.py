from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Notification
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

    def test_multi_mentor_assignment_and_isolated_notifications(self):
        # 1. Create mentors Manikandan and Avanthikaa
        mani_user = User.objects.create_user(
            username="manikandan", email="manikandan@vrcf.org", password=self.password, role=User.Role.MENTOR
        )
        mani_mentor = MentorProfile.objects.create(
            user=mani_user, name="Manikandan", email="manikandan@vrcf.org"
        )

        avan_user = User.objects.create_user(
            username="avanthikaa", email="avanthikaa@vrcf.org", password=self.password, role=User.Role.MENTOR
        )
        avan_mentor = MentorProfile.objects.create(
            user=avan_user, name="Avanthikaa", email="avanthikaa@vrcf.org"
        )

        # 2. Manikandan assigns a task to Arun Kumar (self.student)
        self.client.login(username="manikandan", password=self.password)
        res_mani = self.client.post(reverse('mentor_task_assign'), {
            'title': 'AI System Design by Manikandan',
            'instructions': 'Design a scalable multi-tier neural network pipeline',
            'due_date': '2026-11-20',
            'priority': 'HIGH',
            'target_mode': 'specific',
            'student_ids': [self.student.id],
        }, follow=True)
        self.assertEqual(res_mani.status_code, 200)

        # 3. Avanthikaa assigns a different task to Arun Kumar (self.student)
        self.client.login(username="avanthikaa", password=self.password)
        res_avan = self.client.post(reverse('mentor_task_assign'), {
            'title': 'Ethical Governance by Avanthikaa',
            'instructions': 'Write an analysis on stakeholder accountability',
            'due_date': '2026-11-25',
            'priority': 'MEDIUM',
            'target_mode': 'specific',
            'student_ids': [self.student.id],
        }, follow=True)
        self.assertEqual(res_avan.status_code, 200)

        # 4. Student views their tasks: both tasks must be present and distinct with mentor labels
        self.client.login(username="scholar_001", password=self.password)
        res_student = self.client.get(reverse('student_tasks'))
        self.assertEqual(res_student.status_code, 200)
        self.assertContains(res_student, "AI System Design by Manikandan")
        self.assertContains(res_student, "Ethical Governance by Avanthikaa")
        self.assertContains(res_student, "Manikandan")
        self.assertContains(res_student, "Avanthikaa")

        # 5. Student submits Manikandan's task
        task_mani = MentorTask.objects.get(title="AI System Design by Manikandan")
        res_submit = self.client.post(reverse('student_task_submit', args=[task_mani.id]), {
            'submission_text': 'Here is the detailed neural system design architecture...',
            'save_action': 'submit'
        }, follow=True)
        self.assertEqual(res_submit.status_code, 200)

        # 6. Verify notification was sent specifically to Manikandan, NOT to Avanthikaa
        mani_notifs = Notification.objects.filter(recipient=mani_user, notification_type=Notification.NotificationType.SUBMISSION_RECEIVED)
        avan_notifs = Notification.objects.filter(recipient=avan_user, notification_type=Notification.NotificationType.SUBMISSION_RECEIVED)
        self.assertEqual(mani_notifs.count(), 1)
        self.assertEqual(avan_notifs.count(), 0)
        self.assertIn("Arun Kumar", mani_notifs.first().message)
        self.assertIn("AI System Design by Manikandan", mani_notifs.first().message)

