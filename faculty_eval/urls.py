from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('responseupload/', include('responseupload.urls')),
     path('', lambda request: redirect('responseupload:login')),  # Add this line for the homepage
     path('supervisor/', include('supervisor.urls')),
    path('managerpanel/', include('managerpanel.urls')), # Add 
]