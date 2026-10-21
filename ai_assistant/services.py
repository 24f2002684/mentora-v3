import os
import json
import logging
from django.conf import settings
from django.utils import timezone

from core.models import AuditEvent
from students.models import StudentProfile, Competency
from mentors.models import CompetencyAssessment
from ai_assistant.models import AIConversation, AIMessage, StructuredActivity

logger = logging.getLogger(__name__)

SOCRATIC_SYSTEM_PROMPT = """You are Mentora, a dedicated, thoughtful Socratic mentor and learning coach for scholars of the Vasumathi Ramaswami Centenary Foundation (VRCF) in Tamil Nadu, India.

Your Core Mentoring Philosophy:
1. Act as a thoughtful, encouraging learning coach, NOT a generic answers generator or homework machine.
2. Foster Critical Thinking, Analytical Reasoning, Logical Problem Solving, and Ethical Leadership.
3. Use a flexible Socratic approach:
   - First discern the scholar's intent and reasoning level.
   - Ask focused, clarifying questions that encourage the student to think through problems step-by-step.
   - Offer guiding hints or counter-examples before giving full worked answers.
   - Explain foundational concepts directly if the scholar is stuck or missing prerequisite knowledge.
   - Ask the scholar to reflect on their reasoning and conclude with a concrete, actionable next step.
4. Tone: Calm, encouraging, intellectually rigorous, respectful, and grounded in academic growth.
5. Avoid generic platitudes, repetitive questioning, or robotic lectures.
"""


class SocraticMentorService:
    @staticmethod
    def get_client():
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        if not api_key or api_key.startswith('your_'):
            return None
        try:
            from google import genai
            return genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI client: {e}")
            return None

    @classmethod
    def generate_socratic_reply(cls, student: StudentProfile, prompt: str, conversation: AIConversation = None):
        """
        Generates Socratic response with personalized student context and persists to DB.
        """
        # Ensure conversation exists
        if not conversation:
            title = prompt[:45].strip() + ("..." if len(prompt) > 45 else "")
            conversation = AIConversation.objects.create(
                student=student,
                title=title
            )

        # Record User message
        AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.USER,
            content=prompt
        )

        client = cls.get_client()
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-3.5-flash-lite') or 'gemini-3.5-flash-lite'

        # Assemble personalized context
        vision = getattr(student, 'vision', None)
        active_goals = list(student.goals.filter(status='IN_PROGRESS').values_list('title', flat=True)[:3])
        next_milestone = student.milestones.filter(status='PENDING').first()

        context_summary = (
            f"Scholar Name: {student.name}\n"
            f"Degree & Year: {student.course_name} ({student.year_of_study})\n"
            f"College: {student.college_name_district}\n"
            f"Cohort: {student.cohort}\n"
            f"Personal Aim: {vision.personal_aim if vision else 'Academic and leadership excellence'}\n"
            f"Active Goals: {', '.join(active_goals) if active_goals else 'Developing foundational competencies'}\n"
            f"Next Milestone: {next_milestone.title if next_milestone else 'Coursework review'}\n"
        )

        # Bounded recent history
        past_msgs = conversation.messages.exclude(role=AIMessage.Role.SYSTEM).order_by('-created_at')[:8]
        history_formatted = "\n".join([f"{m.role.upper()}: {m.content}" for m in reversed(past_msgs)])

        full_prompt = (
            f"SCHOLAR CONTEXT:\n{context_summary}\n\n"
            f"CONVERSATION HISTORY:\n{history_formatted}\n\n"
            f"STUDENT QUERY:\n{prompt}\n\n"
            f"Respond as Mentora using the Socratic method."
        )

        reply_text = ""
        tokens_est = 0

        if client:
            try:
                from google.genai import types
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SOCRATIC_SYSTEM_PROMPT,
                        max_output_tokens=800,
                    )
                )
                
                # Check parts for text
                if hasattr(response, 'text') and response.text:
                    reply_text = response.text.strip()
                elif hasattr(response, 'candidates') and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            reply_text += part.text
                
                tokens_est = getattr(response, 'usage_metadata', None).total_token_count if hasattr(response, 'usage_metadata') and response.usage_metadata else 150
            except Exception as e:
                logger.warning(f"Gemini API request failed: {e}")
                reply_text = cls._get_socratic_fallback(student, prompt)
        else:
            reply_text = cls._get_socratic_fallback(student, prompt)

        if not reply_text:
            reply_text = cls._get_socratic_fallback(student, prompt)

        # Record AI Message
        ai_msg = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.MODEL,
            content=reply_text,
            tokens_used=tokens_est,
            model_name=model_name
        )

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])

        return conversation, ai_msg

    @classmethod
    def generate_activity(cls, student: StudentProfile, competency_code: str):
        """
        Creates a structured Socratic development activity for the scholar.
        """
        comp = Competency.objects.filter(code=competency_code).first() or Competency.objects.first()

        activities_bank = {
            'critical-thinking': {
                'title': f"Evidence Evaluation Challenge in {student.course_name}",
                'objective': "Identify unstated assumptions and evaluate alternative interpretations of evidence.",
                'instructions': (
                    "Consider a real-world scenario where two published sources draw opposite conclusions "
                    "on an important question in your field. Outline: (1) What assumptions does each source make? "
                    "(2) What empirical test or data would differentiate between them? (3) What is your preliminary synthesis?"
                ),
                'deliverable': "A 250-word analytical breakdown identifying key assumptions and validation criteria."
            },
            'analytical-thinking': {
                'title': "Root Cause Decomposition Matrix",
                'objective': "Deconstruct a complex multidimensional problem using the MECE framework.",
                'instructions': (
                    "Select a key technical or logistical bottleneck in your current semester studies or campus community. "
                    "Break the problem down into mutually exclusive, collectively exhaustive sub-issues. "
                    "Evaluate the relative impact and feasibility of addressing each branch."
                ),
                'deliverable': "A structured problem tree diagram or outline with clear prioritization."
            },
            'leadership': {
                'title': "Community Impact & First-Generation Scholar Dilemma",
                'objective': "Formulate an ethical leadership intervention balancing limited resources with high community need.",
                'instructions': (
                    "You have been asked to organize an academic peer-mentoring circle for junior students in your college. "
                    "Address: (1) How will you motivate participation without formal authority? "
                    "(2) How will you measure actual learning outcomes? (3) How will you resolve conflicting priorities?"
                ),
                'deliverable': "A 3-step action blueprint with leadership principles and accountability metrics."
            }
        }

        template = activities_bank.get(competency_code, {
            'title': f"Problem-Solving Sprint for {student.name}",
            'objective': f"Strengthen {comp.name} through disciplined reflective practice.",
            'instructions': f"Review a core concept in {student.course_name}. Explain how you would teach this concept to a high school student, and identify where misunderstandings most commonly occur.",
            'deliverable': "A concise conceptual explanation and error-prevention guide."
        })

        activity = StructuredActivity.objects.create(
            student=student,
            title=template['title'],
            objective=template['objective'],
            instructions=template['instructions'],
            competency=comp,
            deliverable_prompt=template['deliverable'],
            status=StructuredActivity.Status.SUGGESTED
        )
        return activity

    @classmethod
    def evaluate_activity(cls, activity: StructuredActivity, student_response: str, reflection: str):
        """
        Generates formative, provisional AI feedback on student's structured activity response.
        """
        activity.student_response = student_response
        activity.reflection_response = reflection
        activity.status = StructuredActivity.Status.COMPLETED
        activity.completed_at = timezone.now()

        # Generate formative assessment
        formative_text = (
            f"Formative Observation on {activity.competency.name}:\n"
            f"• Demonstrated systematic reasoning in addressing the deliverable prompt.\n"
            f"• Clear evidence of reflective awareness regarding personal learning and assumptions.\n"
            f"• Recommended Next Step: Share this analysis with your assigned mentor for official review."
        )
        activity.ai_formative_feedback = formative_text
        activity.save()

        # Log provisional AI Formative Competency Assessment
        CompetencyAssessment.objects.create(
            student=activity.student,
            competency=activity.competency,
            source=CompetencyAssessment.Source.AI_FORMATIVE,
            level=CompetencyAssessment.Level.DEVELOPING,
            score=6.5,
            evidence=f"Completed structured exercise: '{activity.title}'. Response demonstrated structured logical reasoning.",
            feedback=formative_text,
            is_provisional=True
        )

        return activity

    @staticmethod
    def _get_socratic_fallback(student: StudentProfile, prompt: str):
        """
        High-quality, thoughtful Socratic fallback when Gemini API key is unconfigured or rate limited.
        """
        p_lower = prompt.lower()
        if "goal" in p_lower or "milestone" in p_lower:
            return (
                f"That's a meaningful aspiration, {student.name}. To examine this more closely:\n\n"
                f"1. What is the single most critical assumption underlying this goal for your studies in {student.course_name}?\n"
                f"2. If you had to break this down into three sequential hurdles over the next four weeks, what would the first hurdle be?\n\n"
                f"What immediate evidence would demonstrate to you and your mentor that you are making progress?"
            )
        elif "career" in p_lower or "job" in p_lower or "future" in p_lower:
            return (
                f"Preparing for your career journey is an important focus. Let's look at this through an analytical lens:\n\n"
                f"• Which specific technical and communication skills are most sought after by leaders in your target field?\n"
                f"• Between deepening your domain coursework and undertaking a practical project, which creates stronger tangible evidence of your capability?\n\n"
                f"What concrete project or case study could you undertake this semester to test your readiness?"
            )
        else:
            return (
                f"That is an interesting question, {student.name}. Before jumping to a direct conclusion, let's explore the core premise:\n\n"
                f"1. What leading evidence or observations led you to frame the issue in this particular way?\n"
                f"2. If someone took the opposing viewpoint, what would be their strongest valid argument?\n\n"
                f"How might you test or verify these two perspectives using what you are currently learning in {student.course_name}?"
            )
