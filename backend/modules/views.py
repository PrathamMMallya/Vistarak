# from django.shortcuts import render                                  # not needed
# from .services.grpc_client import extract_audio_via_grpc, is_grpc_alive  # gRPC — commented out
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# from modules.models import Transcript                                 # DB model — commented out
# import requests                                                       # not needed for TTS
import traceback
import uuid
import os
import json
import tempfile

# audio_to_trans = "http://127.0.0.1:8003/process_audio/"             # gRPC service — commented out
# speech_to_text = "http://127.0.0.1:8005/generate/"                  # old IndicF5 service — commented out

def index(request):
    return JsonResponse({"message": "Emotion TTS active"})


# ─────────────────────────────────────────────────────────────────
# OLD views — commented out (require gRPC / IndicF5 / Transcript)
# Uncomment when those services are available again.
# ─────────────────────────────────────────────────────────────────

# @csrf_exempt
# def video_transcribe(request):
#     print("reached here")
#     if request.method != "POST":
#         return JsonResponse({"error": "send in POST method"}, status=400)
#     video = request.FILES.get("video_file")
#     source_lan = request.POST.get("source_lan", "auto")
#     if not video:
#         return JsonResponse({"error": "video not received"}, status=400)
#     try:
#         if not is_grpc_alive():
#             print("gRPC server is NOT alive")
#             return JsonResponse({"error": "gRPC server is not available"}, status=503)
#         print("gRPC server is alive")
#         print("Extract audio")
#         audio = extract_audio_via_grpc(video)
#         if not audio:
#             return JsonResponse({"error": "Failed to extract audio"}, status=500)
#         print(f"Audio extracted: {len(audio)} bytes")
#         files = {"file": ("audio.wav", audio, "audio/wav")}
#         data  = {"source_lan": source_lan}
#         print("Sending to STT service")
#         response = requests.post(audio_to_trans, files=files, data=data, timeout=3000)
#         if response.status_code != 200:
#             return JsonResponse({"error": f"STT service error: {response.status_code}"}, status=500)
#         result = response.json()
#         transcript_content = result.get("only_transcript")
#         transcript_id = str(uuid.uuid4())
#         Transcript.objects.create(
#             transcript_id=transcript_id,
#             transcript_text=transcript_content,
#             source_lan=result.get("source_lan")
#         )
#         return JsonResponse({
#             "status": "success",
#             "transcript": result.get("srt_content", ""),
#             "json_data": result.get("json_content", {}),
#             "message": result.get("message", "Processing complete"),
#             "only_transcript": result.get("only_transcript", ""),
#         })
#     except requests.exceptions.ConnectionError as e:
#         return JsonResponse({"error": "Cannot connect to STT service", "details": str(e)}, status=503)
#     except requests.exceptions.Timeout as e:
#         return JsonResponse({"error": "STT processing timeout", "details": str(e)}, status=504)
#     except Exception as e:
#         traceback.print_exc()
#         return JsonResponse({"error": "Internal server error", "details": str(e)}, status=500)


# @csrf_exempt
# def stt(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "send in POST method"}, status=400)
#     text = request.POST.get("text")
#     if not text:
#         return JsonResponse({"error": "text is required"}, status=400)
#     ref_text  = request.POST.get("ref_text")
#     ref_audio = request.FILES.get("ref_audio")
#     if ref_audio:
#         files = {"ref_audio": ("audio.wav", ref_audio, "audio/wav")}
#         data  = {"ref_text": ref_text, "text": text}
#         print("Sending to TTS service")
#         response = requests.post(speech_to_text, files=files, data=data, timeout=100000)
#         return HttpResponse(response.content, content_type="audio/wav")
#     return JsonResponse({"error": "TTS service failed"}, status=500)


# ─────────────────────────────────────────────────────────────────
#  Emotion TTS  (ChatterboxTurboTTS + Groq + pydub pipeline)
# ─────────────────────────────────────────────────────────────────

@csrf_exempt
def emotion_tts(request):
    """
    POST /modules/tts/generate/

    Body (multipart/form-data or application/json):
      text       : str  — the text to synthesise
      ref_audio  : file — (optional) WAV voice reference for cloning
                           if omitted, server uses DEFAULT_VOICE_PATH

    Response (JSON):
      {
        "audio_url"  : "/modules/tts/audio/<filename>.wav",
        "segments"   : [{"text": "...", "emotion": "..."}, ...]
      }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    # ── Parse input text ────────────────────────────────────────
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            body = json.loads(request.body)
            text = body.get("text", "").strip()
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON body"}, status=400)
    else:
        text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({"error": "text field is required"}, status=400)

    # ── Optional voice reference upload ─────────────────────────
    voice_path = None
    ref_audio_file = request.FILES.get("ref_audio")
    if ref_audio_file:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".wav",
            dir=getattr(settings, "TTS_OUTPUT_DIR",
                        os.path.join(settings.BASE_DIR, "tts_output"))
        )
        for chunk in ref_audio_file.chunks():
            tmp.write(chunk)
        tmp.close()
        voice_path = tmp.name

    # ── Lazy import TTS engine (model already loaded at startup) ─
    try:
        from .tts import groq_client, tts_engine, audio_utils
    except Exception as exc:
        traceback.print_exc()
        return JsonResponse({"error": f"TTS engine import failed: {exc}"}, status=500)

    session_id = str(uuid.uuid4())[:8]

    try:
        # Step 1 — Emotion labelling via Groq
        segments = groq_client.get_expressive_segments(text)

        # Step 2 — Generate per-segment audio chunks
        chunk_files = tts_engine.generate_audio_chunks(
            segments,
            voice_path=voice_path,
            session_id=session_id,
        )

        # Step 3 — Merge with emotion-aware pacing
        output_dir = getattr(
            settings, "TTS_OUTPUT_DIR",
            os.path.join(settings.BASE_DIR, "tts_output")
        )
        os.makedirs(output_dir, exist_ok=True)
        final_filename = f"final_{session_id}.wav"
        final_path = os.path.join(output_dir, final_filename)

        audio_utils.merge_audio(chunk_files, segments, output=final_path)

        # Clean up per-chunk temp files
        for f in chunk_files:
            try:
                os.remove(f)
            except OSError:
                pass

        return JsonResponse({
            "audio_url": f"/modules/tts/audio/{final_filename}",
            "segments": segments,
        })

    except Exception as exc:
        traceback.print_exc()
        return JsonResponse({"error": str(exc)}, status=500)

    finally:
        # Clean up uploaded voice temp file
        if voice_path and os.path.exists(voice_path):
            try:
                os.remove(voice_path)
            except OSError:
                pass


@csrf_exempt
def serve_tts_audio(request, filename):
    """
    GET /modules/tts/audio/<filename>

    Streams the final merged WAV file back to the client.
    Automatically deletes the file after streaming to save disk space.
    """
    output_dir = getattr(
        settings, "TTS_OUTPUT_DIR",
        os.path.join(settings.BASE_DIR, "tts_output")
    )
    file_path = os.path.join(output_dir, filename)

    if not os.path.exists(file_path):
        return JsonResponse({"error": "Audio file not found"}, status=404)

    # Security: only allow .wav files and no directory traversal
    if not filename.endswith(".wav") or ".." in filename or "/" in filename:
        return JsonResponse({"error": "Invalid filename"}, status=400)

    response = FileResponse(
        open(file_path, "rb"),
        content_type="audio/wav",
        as_attachment=False,
        filename=filename,
    )
    return response

