from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Count

from core.decorators import role_required
from core.models import User, AuditEvent
from students.models import StudentProfile, Competency
from mentors.models import MentorProfile, MentorStudentAssignment


@role_required('ADMIN', 'TRUSTEE', 'MENTOR')
def admin_student_add_view(request):
    """
    Allows authorized administrators/mentors to provision a new VRCF scholar profile
    and associated login credentials, with rigorous uniqueness validation.
    """
    if request.method == 'POST':
        vrcf_id_raw = request.POST.get('vrcf_id', '').strip()
        name = request.POST.get('name', '').strip()
        cohort = request.POST.get('cohort', '').strip()
        course_name = request.POST.get('course_name', '').strip()
        year_of_study = request.POST.get('year_of_study', '').strip()
        college_name = request.POST.get('college_name_district', '').strip()
        phone_self = request.POST.get('phone_self', '').strip()
        email_self = request.POST.get('email_self', '').strip().lower()
        home_district = request.POST.get('home_district', '').strip()
        hostel = request.POST.get('hostel_or_dayscholar', 'Day Scholar').strip()
        custom_password = request.POST.get('password', '').strip()

        # Format VRCF ID (e.g., 052 -> VRCF-052)
        vrcf_id = vrcf_id_raw
        if vrcf_id.isdigit():
            vrcf_id = f"VRCF-{int(vrcf_id):03d}"
        elif not vrcf_id.upper().startswith("VRCF-"):
            vrcf_id = f"VRCF-{vrcf_id.upper()}"

        if not vrcf_id or not name:
            messages.error(request, "VRCF ID and Scholar Name are strictly required.")
            return render(request, 'admin_tools/add_student.html')

        # Check for duplicate VRCF ID
        if StudentProfile.objects.filter(vrcf_id__iexact=vrcf_id).exists():
            messages.error(request, f"A scholar with VRCF ID '{vrcf_id}' already exists in the system.")
            return render(request, 'admin_tools/add_student.html')

        # Check for duplicate email in User model
        if email_self and User.objects.filter(email__iexact=email_self).exists():
            messages.error(request, f"A user with email '{email_self}' is already registered.")
            return render(request, 'admin_tools/add_student.html')

        # Username from VRCF ID
        clean_id_num = ''.join(c for c in vrcf_id if c.isdigit()) or '000'
        username = f"vrcf_{clean_id_num.lower()}"
        if User.objects.filter(username=username).exists():
            username = f"{username}_{StudentProfile.objects.count() + 1}"

        # Default password: vrcf<number> e.g. vrcf52
        default_pwd = custom_password or f"vrcf{int(clean_id_num)}"

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email_self or f"{username}@vrcf.local",
                    password=default_pwd,
                    role=User.Role.STUDENT,
                    first_name=name.split()[0] if name else '',
                    last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                    phone=phone_self
                )

                student = StudentProfile.objects.create(
                    user=user,
                    vrcf_id=vrcf_id,
                    name=name,
                    cohort=cohort,
                    course_name=course_name,
                    year_of_study=year_of_study,
                    college_name_district=college_name,
                    phone_self=phone_self,
                    email_self=email_self,
                    home_district=home_district,
                    hostel_or_dayscholar=hostel
                )

                # Assign to lead mentor if exists
                lead_mentor = MentorProfile.objects.first()
                if lead_mentor:
                    MentorStudentAssignment.objects.create(
                        mentor=lead_mentor,
                        student=student,
                        is_active=True
                    )

                AuditEvent.objects.create(
                    actor=request.user,
                    event_type='SCHOLAR_PROVISIONED',
                    description=f"Provisioned scholar account {name} ({vrcf_id}) with username '{username}'."
                )

            messages.success(request, f"Scholar {name} ({vrcf_id}) successfully provisioned! Initial password is '{default_pwd}'.")
            return redirect('mentor_students' if request.user.role == 'MENTOR' else 'trustee_students')
        except Exception as e:
            messages.error(request, f"Error provisioning scholar: {str(e)}")
            return render(request, 'admin_tools/add_student.html')

    return render(request, 'admin_tools/add_student.html', {'active_nav': 'add_student'})


@role_required('ADMIN', 'TRUSTEE')
def admin_import_view(request):
    """
    Renders import audit status, verification report, and records metrics.
    """
    total_scholars = StudentProfile.objects.count()
    cohort_breakdown = StudentProfile.objects.values('cohort').annotate(count=Count('id')).order_by('-cohort')
    audit_events = AuditEvent.objects.filter(event_type__in=['DATA_IMPORT', 'SCHOLAR_PROVISIONED', 'MENTOR_PROVISIONED']).order_by('-created_at')[:20]

    context = {
        'total_scholars': total_scholars,
        'cohort_breakdown': cohort_breakdown,
        'audit_events': audit_events,
        'active_nav': 'import'
    }
    return render(request, 'admin_tools/import_audit.html', context)


@role_required('ADMIN', 'TRUSTEE')
def admin_mentor_add_view(request):
    """
    Allows Foundation Trustees and Admins to onboard new VRCF Mentors
    with account credentials and organization profile.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        designation = request.POST.get('designation', 'VRCF Mentor').strip()
        organization = request.POST.get('organization', 'Vasumathi Ramaswami Centenary Foundation').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        custom_password = request.POST.get('password', '').strip()

        if not name or not email:
            messages.error(request, "Mentor Full Name and Email Address are strictly required.")
            return render(request, 'admin_tools/add_mentor.html', {'active_nav': 'add_mentor'})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, f"A user with email '{email}' already exists in the system.")
            return render(request, 'admin_tools/add_mentor.html', {'active_nav': 'add_mentor'})

        # Derive clean username from email or name
        base_username = email.split('@')[0].lower().replace('.', '_').replace('-', '_')
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        default_pwd = custom_password or f"mentor@{MentorProfile.objects.count() + 1}"

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=default_pwd,
                    role=User.Role.MENTOR,
                    first_name=name.split()[0] if name else '',
                    last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                    phone=phone
                )
                mentor = MentorProfile.objects.create(
                    user=user,
                    name=name,
                    email=email,
                    phone=phone,
                    designation=designation or 'VRCF Mentor',
                    organization=organization or 'Vasumathi Ramaswami Centenary Foundation',
                    bio=bio
                )
                AuditEvent.objects.create(
                    actor=request.user,
                    event_type='MENTOR_PROVISIONED',
                    description=f"Provisioned new VRCF Mentor {name} ({email}) with username '{username}'."
                )

            messages.success(request, f"Mentor {name} successfully added! Username: '{username}', Default Password: '{default_pwd}'.")
            return redirect('trustee_mentors')
        except Exception as e:
            messages.error(request, f"Error adding mentor: {str(e)}")
            return render(request, 'admin_tools/add_mentor.html', {'active_nav': 'add_mentor'})

    return render(request, 'admin_tools/add_mentor.html', {'active_nav': 'add_mentor'})


@role_required('ADMIN', 'TRUSTEE')
def admin_mentor_reset_password_view(request, mentor_id):
    """
    Allows Trustees and Admins to reset password for a mentor.
    """
    mentor = get_object_or_404(MentorProfile, id=mentor_id)
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        if not new_password:
            messages.error(request, "New password cannot be blank.")
            return redirect('trustee_mentors')

        mentor.user.set_password(new_password)
        mentor.user.save()

        AuditEvent.objects.create(
            actor=request.user,
            event_type='PASSWORD_RESET',
            description=f"Trustee {request.user.username} reset password for mentor {mentor.name} ({mentor.user.username})."
        )
        messages.success(request, f"Password for mentor {mentor.name} ({mentor.user.username}) successfully updated to '{new_password}'.")
        return redirect('trustee_mentors')

    return redirect('trustee_mentors')

