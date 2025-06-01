from django.urls import path
from . import views

app_name = 'supervisor'

urlpatterns = [
    path('dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('user_courses/<int:user_id>/', views.user_courses, name='user_courses'),
]