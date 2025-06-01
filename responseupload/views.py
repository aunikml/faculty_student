# responseupload/views.py
import csv
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash # Import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy # Import reverse_lazy
from collections import Counter
from .forms import (
     ProgramForm, CourseForm, FacultyForm, # Removed CourseSectionForm
    CustomPasswordChangeForm, SemesterForm, YearForm # Removed CourseSectionForm
)
from .models import (
    FacultyResponse, CourseResponse, Program, Course, Faculty,
    Semester, Year # Removed CourseSection
)
# Import models from managerpanel app
from managerpanel.models import CourseAssignment, Batch, Student # Import managerpanel models
# Import manager check function if needed for protection here
from managerpanel.views import is_manager # Import is_manager for security checks
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.db.models import Count
from datetime import datetime # Keep if used elsewhere

# ==============================================================================
# Home and Authentication Views
# ==============================================================================

def home(request):
    """Redirects the base URL to the login page."""
    if request.user.is_authenticated:
        return redirect('responseupload:dashboard') # Redirect logged-in users to dashboard
    return redirect('responseupload:login')

def user_login(request):
    """Handles user login using the standard AuthenticationForm."""
    if request.user.is_authenticated:
         return redirect('responseupload:dashboard') # Redirect already logged-in users

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password) # Pass request to authenticate
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                # Optional: Redirect based on role
                # if is_manager(user):
                #     return redirect('managerpanel:manager_dashboard')
                # else:
                #     return redirect('responseupload:dashboard')
                return HttpResponseRedirect(reverse('responseupload:dashboard')) # Default redirect
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Improve error feedback
            error_list = [f"{field.capitalize()}: {'; '.join(errors)}" for field, errors in form.errors.items()]
            error_string = " ".join(error_list) if error_list else "Invalid submission details."
            messages.error(request, f"Login failed. {error_string}")
    else:
        form = AuthenticationForm(request) # Pass request for GET as well
    return render(request, 'responseupload/login.html', {'form': form})


def user_logout(request):
    """Logs out the user and redirects to the login page."""
    logout(request)
    messages.info(request, 'You have been successfully logged out.') # Use info level message
    return redirect('responseupload:login')

# ==============================================================================
# Password Change View
# ==============================================================================

@login_required # Ensure user is logged in to change password
def change_password(request):
    """Handles user password changes."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Form handles saving the new password and updating the session
            user = form.save()
            # Important: Update the session authentication hash to prevent logout
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('responseupload:dashboard') # Redirect back to dashboard
        else:
            error_message = 'Please correct the errors below.'
            messages.error(request, error_message)
    else:
        # For GET request, show an empty form bound to the user
        form = CustomPasswordChangeForm(user=request.user)
    # Render the template with the form
    return render(request, 'responseupload/change_password.html', {'form': form})

# ==============================================================================
# Faculty Dashboard and Detail Views
# ==============================================================================

@login_required
def dashboard(request):
    """Displays the faculty dashboard showing assigned courses and evaluation links."""
    user = request.user # The logged-in faculty member

    # 1. Get all CourseAssignments where this user is listed as a faculty member
    assigned_course_assignments = CourseAssignment.objects.filter(
        faculty_members=user
    ).select_related(
        'course', 'course__program', 'course__semester', 'course__year', 'batch'
    ).prefetch_related('faculty_members', 'f2f_sessions'
    ).order_by('-start_date', 'course__code')

    assigned_course_ids = {a.course_id for a in assigned_course_assignments}

    # 2. Check which assigned courses have faculty responses BY THIS USER
    faculty_response_course_ids = set(
        FacultyResponse.objects.filter(
            faculty=user, course_id__in=assigned_course_ids
        ).values_list('course_id', flat=True)
    )
    # 3. Check which assigned courses have course responses BY THIS USER
    course_response_course_ids = set(
        CourseResponse.objects.filter(
            faculty=user, course_id__in=assigned_course_ids
        ).values_list('course_id', flat=True)
    )

    # 4. Calculate response counts for display
    faculty_response_counts = {}
    if faculty_response_course_ids:
        faculty_counts_agg = FacultyResponse.objects.filter(
            faculty=user, course_id__in=faculty_response_course_ids
        ).values('course_id').annotate(count=Count('id'))
        faculty_response_counts = {item['course_id']: item['count'] for item in faculty_counts_agg}

    course_response_counts = {}
    if course_response_course_ids:
        course_counts_agg = CourseResponse.objects.filter(
            faculty=user, course_id__in=course_response_course_ids
        ).values('course_id').annotate(count=Count('id'))
        course_response_counts = {item['course_id']: item['count'] for item in course_counts_agg}

    # --- Get Available Semesters/Years for Filtering (Optional Enhancement) ---
    available_years = Year.objects.filter(
        course__courseassignment__in=assigned_course_assignments
    ).distinct().order_by('-name')
    available_semesters = Semester.objects.filter(
        course__courseassignment__in=assigned_course_assignments
    ).distinct().order_by('name')
    # --- End Optional Enhancement ---

    context = {
        'assigned_course_assignments': assigned_course_assignments,
        'faculty_response_course_ids': faculty_response_course_ids,
        'course_response_course_ids': course_response_course_ids,
        'faculty_response_counts': faculty_response_counts,
        'course_response_counts': course_response_counts,
        'available_years': available_years,
        'available_semesters': available_semesters,
    }

    return render(request, 'responseupload/dashboard.html', context)

@login_required
def course_detail(request, assignment_id): # Changed to use assignment_id
    """Displays faculty evaluation details for a specific course assignment."""
    assignment = get_object_or_404(
        CourseAssignment.objects.select_related(
            'course', 'course__program', 'course__semester', 'course__year', 'batch'
        ).prefetch_related('faculty_members'),
        pk=assignment_id
    )
    course = assignment.course
    user = request.user # Logged-in faculty viewing their own report

    # --- Security Check ---
    if user not in assignment.faculty_members.all():
       if not is_manager(request.user):
           messages.error(request, "You are not authorized to view this assignment's report.")
           return redirect('responseupload:dashboard')
    # --- End Security Check ---

    faculty_responses = FacultyResponse.objects.filter(course=course, faculty=user)

    question_labels = { # Faculty questions
        'q1': 'The organization of session materials and contents prepared by the instructor was-',
        'q2': 'Instructor\'s effort to make the concept clear to the class was-',
        'q3': 'The teaching learning methods (e.g., lecture, group work) followed by the instructor was-',
        'q4': 'The use of learning materials/ resources/ examples/ cases, etc. by the instructor was-',
        'q5': 'Instructor\'s effort to engage the students in learning was-',
        'q6': 'Instructor’s encouragement for the participation, discussion and questions from students was-',
        'q7': 'The guidance for assignment/class activity (group work, presentation, etc.) provided by the instructor was-',
        'q8': 'Instructor’s class time management was-',
    }

    chart_data = {}
    for i in range(1, 9):
        question_field = f'q{i}'
        data = faculty_responses.values(question_field).annotate(count=Count('id')).order_by(question_field)
        filtered_data = [item for item in data if item[question_field] is not None]
        chart_data[question_field] = {
            'labels': [item[question_field] for item in filtered_data],
            'values': [item['count'] for item in filtered_data],
            'label': question_labels.get(question_field, f'Question {i}')
        }

    general_comments = faculty_responses.exclude(general_comments__isnull=True).exclude(general_comments__exact='').values_list('general_comments', flat=True)

    evaluation_scores = { 'A: Excellent': 5, 'B: Very Good': 4, 'C: Good': 3, 'D: Satisfactory': 2, 'E: Not Satisfactory': 1 }
    averages = {}; total_score = 0; num_questions_with_data = 0;
    total_respondents = faculty_responses.count()

    for i in range(1, 9):
        question_field = f'q{i}'
        question_responses = faculty_responses.values_list(question_field, flat=True)
        valid_responses = [resp for resp in question_responses if resp in evaluation_scores]
        question_scores = [evaluation_scores.get(response) for response in valid_responses]
        if question_scores:
            average_score = sum(question_scores) / len(question_scores)
            averages[question_field] = average_score; total_score += average_score; num_questions_with_data += 1
        else: averages[question_field] = 0

    overall_total_out_of_40 = total_score
    max_possible_score = (num_questions_with_data * 5) if num_questions_with_data > 0 else 1
    overall_total_out_of_60 = (total_score / max_possible_score) * 60 if total_score > 0 else 0
    overall_average = total_score / num_questions_with_data if num_questions_with_data > 0 else 0

    context = {
        'assignment': assignment,
        'course': course,
        'chart_data': json.dumps(chart_data),
        'general_comments': general_comments,
        'question_labels': question_labels,
        'averages': averages,
        'overall_total_out_of_40': overall_total_out_of_40,
        'overall_total_out_of_60': overall_total_out_of_60,
        'overall_average': overall_average,
        'total_respondents': total_respondents,
        'faculty_name': user.get_full_name() or user.username
    }
    return render(request, 'responseupload/course_detail.html', context)


@login_required
def course_response_detail(request, assignment_id): # Changed to use assignment_id
    """Displays course evaluation details for a specific course assignment."""
    assignment = get_object_or_404(
        CourseAssignment.objects.select_related(
            'course', 'course__program', 'course__semester', 'course__year', 'batch'
        ).prefetch_related('faculty_members'),
        pk=assignment_id
    )
    course = assignment.course
    user = request.user # Logged-in user viewing their own report

    # --- Security Check ---
    if user not in assignment.faculty_members.all():
       if not is_manager(request.user): # Allow managers too
           messages.error(request, "You are not authorized to view this assignment's report.")
           return redirect('responseupload:dashboard')
    # --- End Security Check ---

    # Filter course responses for THIS assignment (course) and THIS user (faculty)
    course_responses = CourseResponse.objects.filter(course=course, faculty=user)

    question_labels = { # Course questions
        'q1': 'The course provided an opportunity to develop relevant learning and competencies.',
        'q2': 'Textbooks/reading materials used in the course were appropriate.',
        'q3': 'Total time allocated for the course is appropriate to cover all the contents.',
        'q4': 'The contents specified in the syllabus for the course were covered.',
    }

    chart_data = {}
    for i in range(1, 5): # Only 4 questions for course response
        question_field = f'q{i}'
        data = course_responses.values(question_field).annotate(count=Count('id')).order_by(question_field)
        filtered_data = [item for item in data if item[question_field] is not None]
        chart_data[question_field] = {
            'labels': [item[question_field] for item in filtered_data],
            'values': [item['count'] for item in filtered_data],
            'label': question_labels.get(question_field, f'Question {i}')
        }

    general_comments = course_responses.exclude(general_comments__isnull=True).exclude(general_comments__exact='').values_list('general_comments', flat=True)

    evaluation_scores = { 'A: Strongly Agree': 5, 'B: Agree': 4, 'C: Neutral': 3, 'D: Disagree': 2, 'E: Strongly Disagree': 1 }
    averages = {}; total_score = 0; num_questions_with_data = 0;
    total_respondents = course_responses.count()

    for i in range(1, 5):
        question_field = f'q{i}'
        question_responses = course_responses.values_list(question_field, flat=True)
        valid_responses = [resp for resp in question_responses if resp in evaluation_scores]
        question_scores = [evaluation_scores.get(response) for response in valid_responses]
        if question_scores:
            average_score = sum(question_scores) / len(question_scores)
            averages[question_field] = average_score; total_score += average_score; num_questions_with_data += 1
        else: averages[question_field] = 0

    overall_total_out_of_20 = total_score
    max_possible_score = (num_questions_with_data * 5) if num_questions_with_data > 0 else 1
    overall_total_out_of_60 = (total_score / max_possible_score) * 60 if total_score > 0 else 0
    overall_average = total_score / num_questions_with_data if num_questions_with_data > 0 else 0

    context = {
        'assignment': assignment,
        'course': course,
        'chart_data': json.dumps(chart_data),
        'general_comments': general_comments,
        'question_labels': question_labels,
        'averages': averages,
        'overall_total_out_of_20': overall_total_out_of_20,
        'overall_total_out_of_60': overall_total_out_of_60,
        'overall_average': overall_average,
        'total_respondents': total_respondents,
        'faculty_name': user.get_full_name() or user.username
    }
    return render(request, 'responseupload/course_response_detail.html', context)

# ==============================================================================
# Faculty/Course Response List Views (ADDED BACK)
# ==============================================================================

@login_required
def view_faculty_responses(request):
    """Displays a list of faculty responses only for the logged-in user."""
    # Use select_related to optimize fetching related Course data
    responses = FacultyResponse.objects.filter(
        faculty=request.user
    ).select_related(
        'course', 'course__program', 'course__semester', 'course__year'
    ).order_by('-uploaded_at', 'course__code') # Order by upload time first, then course

    context = {'responses': responses}
    return render(request, 'responseupload/faculty_response_list.html', context)

@login_required
def view_course_responses(request):
    """Displays a list of course responses only for the logged-in user."""
    # Use select_related for optimization
    responses = CourseResponse.objects.filter(
        faculty=request.user
    ).select_related(
        'course', 'course__program', 'course__semester', 'course__year'
    ).order_by('-uploaded_at', 'course__code') # Order by upload time first, then course

    context = {'responses': responses}
    return render(request, 'responseupload/course_response_list.html', context)


# ==============================================================================
# Faculty Batch Detail View
# ==============================================================================

@login_required
def faculty_batch_detail(request, batch_id):
    """ Displays the student list for a specific batch (Faculty access check). """
    batch = get_object_or_404(Batch.objects.prefetch_related('students', 'students__enrollment_semester'), pk=batch_id)
    user = request.user

    is_assigned_to_batch_course = CourseAssignment.objects.filter(batch=batch, faculty_members=user).exists()
    if not is_assigned_to_batch_course:
        messages.error(request, "You are not authorized to view students for this batch.")
        return redirect('responseupload:dashboard')

    # Fetch students related to the batch
    students = batch.students.all().order_by('last_name', 'first_name')

    # Add pagination for students if the list can be long
    paginator = Paginator(students, 25) # Show 25 students per page
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)

    context = {
        'batch': batch,
        'students_page': students_page # Pass paginated list
    }
    return render(request, 'responseupload/faculty_batch_detail.html', context)


# ==============================================================================
# Component Creation Views (Protected within the handler)
# ==============================================================================

@csrf_protect
def handle_create_view(request, form_class, success_message, template_name, redirect_url_name='responseupload:dashboard'):
    """Handles the creation of new model instances using the provided form."""
    if not request.user.is_authenticated:
         return redirect(reverse_lazy('responseupload:login'))

    # --- Add Manager Check ---
    if not is_manager(request.user):
       messages.error(request, "You are not authorized to perform this action.")
       # Redirect non-managers to faculty dashboard
       return redirect('responseupload:dashboard')
    # --- End Manager Check ---

    if request.method == 'POST':
        form = form_class(request.POST);
        if form.is_valid():
            form.save()
            messages.success(request, success_message)
            return redirect(redirect_url_name) # Use the specific redirect name passed
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = form_class()

    model_name = getattr(form_class._meta.model._meta, 'verbose_name', form_class._meta.model.__name__)
    form_title = f"Create New {model_name}"
    # Make sure the template name passed exists in responseupload or managerpanel templates
    return render(request, template_name, {'form': form, 'form_title': form_title})

# Specific views calling the generalized handler
@login_required
def create_semester(request):
    # Redirects to manager dashboard on success now
    return handle_create_view(request, SemesterForm, 'Semester created successfully.', 'responseupload/create_component.html', 'managerpanel:manager_dashboard')

@login_required
def create_year(request):
    # Redirects to manager dashboard on success now
    return handle_create_view(request, YearForm, 'Year created successfully.', 'responseupload/create_component.html', 'managerpanel:manager_dashboard')

# Removed create_course_section

@login_required
def create_program(request):
    # Redirects to manager dashboard on success now
    return handle_create_view(request, ProgramForm, 'Program created successfully.', 'responseupload/create_program.html', 'managerpanel:manager_dashboard')

@login_required
def create_course(request):
    # Uses updated CourseForm
    # Redirects to manager dashboard on success now
    return handle_create_view(request, CourseForm, 'Course created successfully.', 'responseupload/create_course.html', 'managerpanel:manager_dashboard')

@login_required
def create_faculty(request):
    # This view is likely obsolete and should probably be removed
    # If kept, it should be protected and redirect appropriately
    return handle_create_view(request, FacultyForm, 'Faculty created successfully.', 'responseupload/create_faculty.html', 'managerpanel:manager_dashboard')