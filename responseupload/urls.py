# responseupload/urls.py
from django.urls import path
from . import views

app_name = 'responseupload' # Namespace for this app's URLs

urlpatterns = [
    # Home/Root URL - Redirects to login
    path('', views.home, name='home'),

    # Authentication URLs
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('change_password/', views.change_password, name='change_password'),

    # Faculty Dashboard URL
    path('dashboard/', views.dashboard, name='dashboard'),

    # URLs for viewing evaluation details linked from the dashboard
    # Now using assignment_id to identify the specific offering/context
    path('assignment/<int:assignment_id>/faculty_eval/', views.course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/course_eval/', views.course_response_detail, name='course_response_detail'),

    # URL for faculty to view students in a batch they are assigned to
    path('batch/<int:batch_id>/students/', views.faculty_batch_detail, name='faculty_batch_detail'),

    # URLs for viewing lists of user's own responses (optional)
    path('my_faculty_responses/', views.view_faculty_responses, name='view_faculty_responses'),
    path('my_course_responses/', views.view_course_responses, name='view_course_responses'),

    # --- Component Creation URLs ---
    # These might be better placed in managerpanel/urls.py and protected,
    # but kept here based on previous structure. Ensure views are protected if needed.
    path('create/program/', views.create_program, name='create_program'),
    path('create/course/', views.create_course, name='create_course'),
    # path('create/faculty/', views.create_faculty, name='create_faculty'), # This is likely obsolete
    path('create/semester/', views.create_semester, name='create_semester'),
    path('create/year/', views.create_year, name='create_year'),
    # Removed create_course_section as the model is removed
]