from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/visualize', views.visualize, name='visualize'),
    path('api/parse', views.parse_only, name='parse_only'),
    path('api/health', views.health_check, name='health_check'),
    path('api/statistics', views.handle_statistics, name='handle_statistics'),
    path('api/statistics/test', views.test_statistics, name='test_statistics'),
]