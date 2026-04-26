from django.urls import path
from .views import add_equation, list_equations, manim_generate, manim_template_info, manim_chat

urlpatterns = [
    path("add/", add_equation),
    path("list/", list_equations),
    path("manim/generate/", manim_generate),
    path("manim/template-info/", manim_template_info),
    path("manim/chat/", manim_chat),
]
