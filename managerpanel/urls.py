# managerpanel/urls.py
from django.urls import path
from . import views

app_name = 'managerpanel'

urlpatterns = [
    # --- Dashboard ---
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),

    # --- Course Assignment URLs ---
    path('assignments/', views.list_course_assignments, name='list_assignments'),
    path('assign/', views.create_course_assignment, name='create_course_assignment'),
    path('assignments/edit/<int:assignment_id>/', views.edit_course_assignment, name='edit_course_assignment'), # Matched naming convention
    path('assignments/delete/<int:assignment_id>/', views.delete_course_assignment, name='delete_course_assignment'), # Matched naming convention

    # --- Component Creation URLs (e.g., Program, Semester, Year, Course Definition) ---
    path('create/program/', views.create_program_manager, name='create_program_manager'),
    path('create/semester/', views.create_semester_manager, name='create_semester_manager'),
    path('create/year/', views.create_year_manager, name='create_year_manager'),
    path('create/course/', views.create_course_manager, name='create_course_manager'), # For general Course Definitions

    # --- Batch Management URLs ---
    path('batches/', views.list_batches, name='list_batches'),
    path('batches/create/', views.create_batch, name='create_batch'),
    path('batches/edit/<int:batch_id>/', views.edit_batch, name='edit_batch'),
    path('batches/delete/<int:batch_id>/', views.delete_batch, name='delete_batch'),
    path('batches/<int:batch_id>/', views.batch_detail, name='batch_detail'), # Detail view for a specific batch
    path('batches/<int:batch_id>/update-status/', views.update_batch_status, name='update_batch_status'), # For updating batch status

    # --- Student Management URLs ---
    path('students/search/', views.search_students, name='search_students'),
    path('batches/<int:batch_id>/add_student/', views.add_student_manual, name='add_student_manual'), # Add student to a specific batch
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('students/upload/', views.upload_students_csv, name='upload_students_csv'), # CSV upload for students

    # --- Student Progress Editing URLs ---
    path('student/<int:student_id>/update-progress/',
         views.update_student_progress, name='update_student_progress'),
    path('student/<int:student_id>/progress-edit-courses/',
         views.get_student_progress_edit_courses, name='get_student_progress_edit_courses'),
]