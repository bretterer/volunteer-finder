from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('upload/', views.upload_resume, name='upload'),
    path('my-resume/', views.my_resume, name='my_resume'),
    path('delete/', views.delete_resume, name='delete'),
]