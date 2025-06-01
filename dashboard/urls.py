# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    # Add other dashboard-related URLs here if needed later
]