from .services.audio_utils import extract_audio_local
from .services.grpc_client import extract_audio_via_grpc, is_grpc_alive
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from modules.models import Transcript
import requests
import traceback
import uuid
import os
import json
import tempfile

audio_to_trans = "http://172.16.2.131:9003/process_audio/"

def index(request):
    return JsonResponse({"message": "Emotion TTS active"})

from django.urls import get_resolver
from django.http import JsonResponse

def all_urls(request):
    urls = []

    def extract(patterns, prefix=''):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                extract(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                urls.append(prefix + str(pattern.pattern))

    extract(get_resolver().url_patterns)
    return JsonResponse({"urls": urls})
# ─────────────────────────────────────────────────────────────────
# OLD views — commented out (require gRPC / IndicF5 / Transcript)
# Uncomment when those services are available again.
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
def video_transcribe(request):
    """
    POST /modules/video_transcribe/
    Expects 'video' file in request.FILES
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    video = request.FILES.get("video_file")
    if not video:
        return JsonResponse({"error": "No video file provided"}, status=400)

    try:
        print("📹 Extracting audio via gRPC (Port 9004)...")
        audio = extract_audio_via_grpc(video)
        print(f"✅ Audio extracted: {len(audio)} bytes")
        
        # Prepare the file for the POST request
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {"task": "transcribe", "language": "en"}

        response = requests.post(audio_to_trans, files=files, data=data, timeout=300)
        
        if response.status_code != 200:
            return JsonResponse({
                "error": f"STT service error: {response.status_code}",
                "details": response.text
            }, status=500)

        result = response.json()
        print(f"✅ STT Result: {result}")
        transcript_content = result.get("only_transcript")
        transcript_id = str(uuid.uuid4())
        Transcript.objects.create(
            transcript_id=transcript_id,
            transcript_text=transcript_content,
            source_lan=result.get("source_lan")
        )
        return JsonResponse({
            "status": "success",
            "transcript": result.get("srt_content", ""),
            "json_data": result.get("json_content", {}),
            "message": result.get("message", "Processing complete"),
            "only_transcript": result.get("only_transcript", ""),
        })
    except requests.exceptions.ConnectionError as e:
        return JsonResponse({"error": "Cannot connect to STT service", "details": str(e)}, status=503)
    except requests.exceptions.Timeout as e:
        return JsonResponse({"error": "STT processing timeout", "details": str(e)}, status=504)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


@csrf_exempt
def stt(request):
    if request.method != "POST":
        return JsonResponse({"error": "send in POST method"}, status=400)
    text = request.POST.get("text")
    if not text:
        return JsonResponse({"error": "text is required"}, status=400)
    ref_text  = request.POST.get("ref_text")
    ref_audio = request.FILES.get("ref_audio")
    if ref_audio:
        files = {"ref_audio": ("audio.wav", ref_audio, "audio/wav")}
        data  = {"ref_text": ref_text, "text": text}
        print("Sending to TTS service")
        response = requests.post(speech_to_text, files=files, data=data, timeout=100000)
        return HttpResponse(response.content, content_type="audio/wav")
    return JsonResponse({"error": "TTS service failed"}, status=500)


# ─────────────────────────────────────────────────────────────────
#  Emotion TTS  (ChatterboxTurboTTS + Groq + pydub pipeline)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
def emotion_tts(request):
    """
    Proxy view for Emotion TTS running on the IPU (Port 9055).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    TTS_DOCKER_URL = "http://172.16.2.131:9055/generate/"

    try:
        text = request.POST.get("text", "")
        ref_audio = request.FILES.get("ref_audio")

        if not text:
            # Check if JSON was sent instead
            if request.body:
                try:
                    import json
                    body = json.loads(request.body)
                    text = body.get("text", "")
                except:
                    pass

        files = {}
        if ref_audio:
            files["ref_audio"] = (ref_audio.name, ref_audio.read(), ref_audio.content_type)
        
        data = {"text": text}

        print(f"🔊 Proxying TTS request to {TTS_DOCKER_URL} (Text: {text[:30]}...)")
        response = requests.post(TTS_DOCKER_URL, data=data, files=files, timeout=300)

        if response.status_code == 200:
            return HttpResponse(response.content, content_type="audio/wav")
        else:
            print(f"❌ TTS Docker error: {response.status_code} - {response.text}")
            return JsonResponse({"error": f"TTS Service Error: {response.status_code}"}, status=500)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

