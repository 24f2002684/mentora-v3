from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages

from core.decorators import student_required
from students.models import StudentProfile, Competency
from ai_assistant.models import AIConversation, AIMessage, StructuredActivity
from ai_assistant.services import SocraticMentorService


@student_required
def chat_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    conversations = student.ai_conversations.filter(is_archived=False).order_by('-updated_at')

    # Selected or active conversation
    conv_id = request.GET.get('conversation')
    is_new = request.GET.get('new') == '1'
    current_conv = None
    if conv_id and not is_new:
        current_conv = conversations.filter(id=conv_id).first()
    elif not is_new:
        current_conv = conversations.first()

    messages_list = current_conv.messages.all() if current_conv else []
    starter_prompt = request.GET.get('prompt', '')

    activities = student.structured_activities.all()[:4]
    competencies = Competency.objects.all()

    context = {
        'student': student,
        'conversations': conversations,
        'current_conversation': current_conv,
        'messages_list': messages_list,
        'starter_prompt': starter_prompt,
        'activities': activities,
        'competencies': competencies,
        'active_nav': 'ai_mentor'
    }
    return render(request, 'students/ai_mentor.html', context)


@student_required
@require_POST
def send_message_api(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    prompt = request.POST.get('prompt', '').strip()
    conv_id = request.POST.get('conversation_id')

    if not prompt:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    conv = None
    if conv_id and conv_id.isdigit():
        conv = student.ai_conversations.filter(id=int(conv_id), is_archived=False).first()

    conversation, ai_msg = SocraticMentorService.generate_socratic_reply(
        student=student,
        prompt=prompt,
        conversation=conv
    )

    return JsonResponse({
        'status': 'success',
        'conversation_id': conversation.id,
        'conversation_title': conversation.title,
        'user_message': {
            'role': 'user',
            'content': prompt,
            'time': 'Just now'
        },
        'ai_message': {
            'role': 'model',
            'content': ai_msg.content,
            'time': 'Just now'
        }
    })


@student_required
@require_POST
def rename_conversation_api(request, conv_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    conv = get_object_or_404(AIConversation, id=conv_id, student=student)
    new_title = request.POST.get('title', '').strip()

    if new_title:
        conv.title = new_title[:100]
        conv.save(update_fields=['title'])
        return JsonResponse({'status': 'success', 'title': conv.title})
    return JsonResponse({'error': 'Invalid title'}, status=400)


@student_required
@require_POST
def delete_conversation_api(request, conv_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    conv = get_object_or_404(AIConversation, id=conv_id, student=student)
    conv.is_archived = True
    conv.save(update_fields=['is_archived'])
    return JsonResponse({'status': 'success'})


@student_required
def create_activity_view(request):
    student = get_object_or_404(StudentProfile, user=request.user)
    comp_code = request.GET.get('competency', 'critical-thinking')
    activity = SocraticMentorService.generate_activity(student, comp_code)
    messages.success(request, f"Generated developmental challenge: '{activity.title}'")
    return redirect('student_ai_mentor')


@student_required
def submit_activity_view(request, activity_id):
    student = get_object_or_404(StudentProfile, user=request.user)
    activity = get_object_or_404(StructuredActivity, id=activity_id, student=student)

    if request.method == 'POST':
        response_text = request.POST.get('student_response', '').strip()
        reflection = request.POST.get('reflection_response', '').strip()

        if response_text:
            SocraticMentorService.evaluate_activity(activity, response_text, reflection)
            messages.success(request, "Activity submitted! AI formative feedback generated and logged.")
            return redirect('student_progress')
        else:
            messages.error(request, "Please enter your response before submitting.")

    return render(request, 'students/activity_detail.html', {'activity': activity, 'active_nav': 'ai_mentor'})
