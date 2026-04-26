from django.urls import path
from .views import add_equation, list_equations, manim_generate

urlpatterns = [
    path("add/", add_equation),
    path("list/", list_equations),
    path("manim/generate/", manim_generate),
]
