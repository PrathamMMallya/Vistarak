from django.urls import path
from . import views

urlpatterns = [
    path('preview/', views.serve_default_story, name='story_preview'),
    path('generate/', views.generate_story, name='story_generate'),
]
