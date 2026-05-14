import os
import uuid
import json
import requests
import pdfplumber
from docx import Document
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from modules.models import Transcript

FASTAPI_TRANSLATE_URL = "http://172.16.2.131:8903/translate"
UPLOAD_DIR = "temp_translate_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ONLY ALLOWED LANGUAGES
ALLOWED_LANGS = {"en", "hi", "kn", "te", "ta", "ml", "bn"}


# ======================================================
# COMMON TEXT EXTRACTION
# ======================================================
def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".pdf":
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    pages.append(txt)
        return "\n".join(pages)

    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    raise ValueError("Unsupported file format")


# ======================================================
# TRANSCRIPT → NLLB
# ======================================================
@csrf_exempt
def nllb(request):
    """
    Translate latest transcript using NLLB
    Works even if target_lan is NOT sent (defaults applied)
    """

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # -----------------------------
    # ALLOWED LANGUAGES
    # -----------------------------
    ALLOWED_LANGS = {"en", "hi", "kn", "te", "ta", "ml", "bn"}

    # -----------------------------
    # READ TARGET LANGUAGE
    # -----------------------------
    target_lan = request.POST.get("target_lan")

    # If frontend sends JSON
    if not target_lan and request.body:
        try:
            import json
            body = json.loads(request.body.decode("utf-8"))
            target_lan = body.get("target_lan")
        except Exception:
            pass

    # 🔑 DEFAULT (CRITICAL FIX)
    if not target_lan:
        target_lan = "hi"   # default for transcript translation

    if target_lan not in ALLOWED_LANGS:
        return JsonResponse(
            {"error": f"Unsupported target language: {target_lan}"},
            status=400
        )

    # -----------------------------
    # FETCH LATEST TRANSCRIPT
    # -----------------------------
    try:
        latest = Transcript.objects.latest("created_at")
    except Transcript.DoesNotExist:
        return JsonResponse({"error": "No transcript found"}, status=404)

    if not latest.transcript_text or not latest.transcript_text.strip():
        return JsonResponse({"error": "Transcript text is empty"}, status=400)

    source_lan = latest.source_lan or "en"
    if source_lan not in ALLOWED_LANGS:
        source_lan = "en"

    # -----------------------------
    # CALL NLLB SERVICE
    # -----------------------------
    payload = {
        "text": latest.transcript_text,
        "source_lan": source_lan,
        "target_lan": target_lan,
    }

    try:
        response = requests.post(
            FASTAPI_TRANSLATE_URL,
            json=payload,
            timeout=300
        )
    except requests.RequestException as e:
        return JsonResponse(
            {"error": "NLLB service unreachable", "details": str(e)},
            status=500
        )

    if response.status_code != 200:
        return JsonResponse(
            {"error": "Translation failed", "details": response.text},
            status=500
        )

    return JsonResponse({
        "status": "success",
        "original_text": latest.transcript_text,
        "translated_text": response.json().get("translated_text", ""),
        "source_language": source_lan,
        "target_language": target_lan,
    })



# ======================================================
# DOCUMENT → NLLB
# ======================================================
@csrf_exempt
def document_translate(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    uploaded_file = request.FILES.get("file")
    source_lan = request.POST.get("source_language", "en")
    target_lan = request.POST.get("target_language", "hi")

    if not uploaded_file:
        return JsonResponse({"error": "file is required"}, status=400)

    if source_lan not in ALLOWED_LANGS:
        source_lan = "en"

    if target_lan not in ALLOWED_LANGS:
        return JsonResponse({"error": "Invalid target language"}, status=400)

    temp_path = None

    try:
        temp_name = f"{uuid.uuid4()}_{uploaded_file.name}"
        temp_path = os.path.join(UPLOAD_DIR, temp_name)

        with open(temp_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        extracted_text = extract_text(temp_path)

        payload = {
            "text": extracted_text,
            "source_lan": source_lan,
            "target_lan": target_lan,
        }

        response = requests.post(
            FASTAPI_TRANSLATE_URL,
            json=payload,
            timeout=600
        )

        if response.status_code != 200:
            return JsonResponse(
                {"error": "Translation service failed", "details": response.text},
                status=500
            )

        return JsonResponse({
            "status": "success",
            "original_text": extracted_text,
            "translated_text": response.json().get("translated_text", ""),
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
