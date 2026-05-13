from django.urls import path

from . import views

urlpatterns = [
    path("generate/", views.generate),
    path("status/<str:job_id>/", views.status),
    path("result/<str:job_id>/", views.result),
]
