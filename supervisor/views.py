from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from responseupload.models import Course, FacultyResponse, CourseResponse
from .models import Supervisor

@login_required
def supervisor_dashboard(request):
    if not Supervisor.objects.filter(user=request.user).exists():
        return HttpResponseForbidden("You do not have permission to view this page.")

    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'supervisor/supervisor_dashboard.html', context)

@login_required
def user_courses(request, user_id):
    if not Supervisor.objects.filter(user=request.user).exists():
        return HttpResponseForbidden("You do not have permission to view this page.")

    user = get_object_or_404(User, pk=user_id)

    # Get Faculty Responses for the user
    faculty_responses = FacultyResponse.objects.filter(faculty=user)

    # Get Course Responses for the user
    course_responses = CourseResponse.objects.filter(faculty=user)

    # Get unique courses from both response types
    faculty_courses = faculty_responses.values_list('course', flat=True).distinct()
    course_courses = course_responses.values_list('course', flat=True).distinct()

    # Combine the unique course IDs
    all_course_ids = set(faculty_courses) | set(course_courses)

    # Get the actual course objects
    user_courses = Course.objects.filter(id__in=all_course_ids)

    # Separate courses based on whether they have faculty or course responses
    faculty_response_courses = Course.objects.filter(id__in=faculty_courses)
    course_response_courses = Course.objects.filter(id__in=course_courses)

    context = {
        'selected_user': user,
        'faculty_response_courses': faculty_response_courses,
        'course_response_courses': course_response_courses,
    }
    return render(request, 'supervisor/user_courses.html', context)