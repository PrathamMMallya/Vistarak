from django.urls import path
from . import views
urlpatterns = [
    path('', views.index),
    path('video_transcribe/', views.video_transcribe),  # commented — requires gRPC
    # path('stt/', views.stt),                            # commented — requires IndicF5 service
    # Emotion TTS (ChatterboxTurboTTS pipeline)
    path('tts/generate/', views.emotion_tts, name='emotion_tts'),
    path('all-urls/', views.all_urls),
]