from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User
from students.models import StudentProfile, Competency
from ai_assistant.models import AIConversation, AIMessage, StructuredActivity
from ai_assistant.services import SocraticMentorService
from mentors.models import CompetencyAssessment


class AISocraticMentorTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "ScholarPass123!"

        self.user = User.objects.create_user(
            username="scholar_007", email="scholar7@vrcf.org", password=self.password, role=User.Role.STUDENT
        )
        self.student = StudentProfile.objects.create(
            user=self.user, vrcf_id="VRCF-007", name="Kavitha S", cohort="2025-2026",
            course_name="B.Tech IT"
        )

        self.comp = Competency.objects.create(
            name="Critical Thinking", code="critical-thinking", description="Objective evaluation"
        )

    @patch.object(SocraticMentorService, 'get_client', return_value=None)
    def test_socratic_mentor_service_persistence_and_fallback(self, mock_client):
        # Test that generate_socratic_reply produces an AI response, persists both messages,
        # and gracefully provides Socratic coaching when offline or without external credentials.
        prompt = "How can I improve my analytical thinking for college projects?"
        conv, ai_msg = SocraticMentorService.generate_socratic_reply(
            student=self.student,
            prompt=prompt
        )

        self.assertIsNotNone(conv)
        self.assertEqual(conv.student, self.student)
        self.assertEqual(conv.messages.count(), 2)
        
        user_msg = conv.messages.filter(role=AIMessage.Role.USER).first()
        self.assertEqual(user_msg.content, prompt)

        model_msg = conv.messages.filter(role=AIMessage.Role.MODEL).first()
        self.assertIsNotNone(model_msg.content)
        self.assertTrue(len(model_msg.content) > 10)

    def test_ai_formative_assessment_separation(self):
        # Generate and evaluate a structured activity
        activity = SocraticMentorService.generate_activity(self.student, "critical-thinking")
        self.assertIsNotNone(activity)
        self.assertEqual(activity.competency, self.comp)

        # Submit response and evaluate
        evaluated_act = SocraticMentorService.evaluate_activity(
            activity,
            student_response="I analyzed the root causes by segmenting data into cohorts and challenging our primary assumptions.",
            reflection="I learned that first impressions often hide confounding variables."
        )

        self.assertEqual(evaluated_act.status, StructuredActivity.Status.COMPLETED)

        # Verify that the created CompetencyAssessment has source=AI_FORMATIVE and is NOT MENTOR
        ai_assessment = CompetencyAssessment.objects.filter(
            student=self.student,
            competency=self.comp,
            source=CompetencyAssessment.Source.AI_FORMATIVE
        ).first()

        self.assertIsNotNone(ai_assessment)
        self.assertTrue(ai_assessment.is_provisional)
        self.assertNotEqual(ai_assessment.source, CompetencyAssessment.Source.MENTOR)

    @patch.object(SocraticMentorService, 'get_client', return_value=None)
    def test_ai_chat_views_and_api(self, mock_client):
        self.client.login(username="scholar_007", password=self.password)
        
        # Test chat page render
        res = self.client.get(reverse('student_ai_mentor'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AI Socratic Mentor")

        # Test send message API
        res = self.client.post(reverse('ai_send_message'), {
            'prompt': 'What strategies should I use to prioritize my semester goals?'
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('conversation_id', data)
        self.assertIn('ai_message', data)
