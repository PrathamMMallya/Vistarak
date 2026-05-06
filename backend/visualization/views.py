from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
import re
import shutil
import uuid
import requests
from urllib.parse import quote_plus
from typing import Any, Optional

# In-memory store for demo purposes
EQUATIONS_STORE = []
MANIM_THREADS: dict[str, dict[str, Any]] = {}


def _manim_proxy_timeout() -> int:
    raw_timeout = os.environ.get("MANIM_PROXY_TIMEOUT", "900")
    try:
        return max(30, int(raw_timeout))
    except (TypeError, ValueError):
        return 900


def _load_base_code_by_id(base_code_id: str) -> str:
    base_code_id = (base_code_id or "").strip()
    if not base_code_id:
        raise ValueError("base_code_id is empty")

    slug_map = {
        "math.gradient_descent": "gradient_descent.py",
        "math.eigenvalues": "eigenvalues.py",
        "math.fourier_series": "fourier_series.py",
        "physics.projectile_motion": "projectile.py",
        "physics.electric_field": "electric_field.py",
        "physics.wave_interference": "wave_interference.py",
        "physics.projectile_motion_vector_decomposition": "projectile.py",
        "projectile": "projectile.py",
    }
    fname = slug_map.get(base_code_id)
    if not fname:
        raise ValueError(f"Unknown base_code_id: {base_code_id}")

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates_manim"))
    path = os.path.join(base_dir, fname)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _auto_detect_base_code_id(prompt: str) -> Optional[str]:
    p = (prompt or "").lower()
    if "projectile" in p:
        return "projectile"
    return None


def _extract_thread_user_requests(thread: dict[str, Any]) -> list[str]:
    messages = thread.get("messages", []) if isinstance(thread, dict) else []
    requests: list[str] = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = (msg.get("content") or "").strip()
            if content:
                requests.append(content)
    return requests


def _rewrite_media_urls(obj: Any, base_url: str) -> Any:
    """Recursively rewrite media paths like '/media/...' to absolute URLs
    pointing at `base_url` (e.g. http://127.0.0.1:8010).
    """
    if isinstance(obj, str):
        if obj.startswith("/media/") or obj.startswith("media/"):
            return f"{base_url.rstrip('/')}/{obj.lstrip('/')}"
        return obj
    if isinstance(obj, dict):
        return {k: _rewrite_media_urls(v, base_url) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_rewrite_media_urls(v, base_url) for v in obj]
    return obj


@csrf_exempt
def add_equation(request):
    """
    POST { "latex": "y = x^2" } -> adds equation
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        latex = data.get("latex")
        if not latex:
            return JsonResponse({"error": "LaTeX required"}, status=400)
        EQUATIONS_STORE.append(latex)
        return JsonResponse({"status": "success", "equations": EQUATIONS_STORE})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def list_equations(request):
    """
    GET -> returns all stored equations
    """
    return JsonResponse({"equations": EQUATIONS_STORE})


@csrf_exempt
def manim_generate(request):
    MANIM_API_BASE = os.environ.get("MANIM_API_BASE_URL", "http://127.0.0.1:8010")
    target = f"{MANIM_API_BASE.rstrip('/')}/manim/generate/"

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        resp = requests.post(
            target,
            data=request.body,
            headers={"Content-Type": request.META.get("CONTENT_TYPE", "application/json")},
            timeout=_manim_proxy_timeout(),
        )
        try:
            payload = resp.json()
        except ValueError:
            return JsonResponse({"status": "error", "error": "Invalid JSON from manim service"}, status=502)
        # Rewrite any /media/... paths so clients fetch media from the Manim service
        payload = _rewrite_media_urls(payload, MANIM_API_BASE)
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=502)


# ── Template slug → JSON filename mapping ──────────────────────────────────────
_SLUG_TO_JSON: dict[str, str] = {
    "math.gradient_descent": "gradient_descent.json",
    "math.eigenvalues": "eigenvalues.json",
    "math.fourier_series": "fourier_series.json",
    "physics.projectile_motion": "projectile.json",
    "physics.electric_field": "electric_field.json",
    "physics.wave_interference": "wave_interference.json",
}


def _load_template_info(template_id: str) -> dict[str, Any]:
    """Load the JSON metadata file for a given template_id."""
    fname = _SLUG_TO_JSON.get(template_id)
    if not fname:
        raise ValueError(f"Unknown template_id: {template_id}")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates_manim"))
    path = os.path.join(base_dir, fname)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def manim_template_info(request):
    """GET /visualization/manim/template-info/?id=<template_id>"""
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    template_id = (request.GET.get("id") or "").strip()
    if not template_id:
        return JsonResponse({"error": "id query parameter is required"}, status=400)

    MANIM_API_BASE = os.environ.get("MANIM_API_BASE_URL", "http://127.0.0.1:8010")
    target = f"{MANIM_API_BASE.rstrip('/')}/manim/template-info/?id={quote_plus(template_id)}"
    try:
        resp = requests.get(target, timeout=30)
        try:
            payload = resp.json()
        except ValueError:
            return JsonResponse({"status": "error", "error": "Invalid JSON from manim service"}, status=502)
        payload = _rewrite_media_urls(payload, MANIM_API_BASE)
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=502)


# ── Intent classification ───────────────────────────────────────────────────────

_EXPLANATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(explain|what\s+is|what\s+are|why\s+(does|is|do|did|are))\b", re.I),
    re.compile(r"\b(how\s+does|how\s+do|how\s+is|how\s+are)\b", re.I),
    re.compile(r"\b(tell\s+me|describe|definition|define|meaning)\b", re.I),
    re.compile(r"\b(difference\s+between|compare)\b", re.I),
    re.compile(r"\b(can\s+you\s+explain|could\s+you\s+explain)\b", re.I),
    re.compile(r"\b(what\s+happens|what\s+would\s+happen)\b", re.I),
    re.compile(r"\b(is\s+it\s+true|is\s+this\s+correct)\b", re.I),
    re.compile(r"^(why|what|who|when)\b", re.I),
]

_ANIMATION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(animate|render|show\s+me|visuali[sz]e|generate|draw|plot)\b", re.I),
    re.compile(r"\b(change|modify|update|set|replace|swap|switch)\b", re.I),
    re.compile(r"\b(add|remove|delete|insert|include)\b", re.I),
    re.compile(r"\b(make\s+it|turn\s+it|increase|decrease|scale)\b", re.I),
    re.compile(r"\b(colo[u]?r|speed|slow|fast|bigger|smaller|thicker|thinner)\b", re.I),
    re.compile(r"\b(move|rotate|shift|flip|mirror)\b", re.I),
    re.compile(r"\b(label|title|text|font|arrow|dot|line|axis)\b", re.I),
    re.compile(r"=\s*\d", re.I),  # e.g. "set gravity = 5"
]


def _classify_intent(prompt: str) -> str:
    """Classify user prompt as 'explanation' or 'animation'.

    Scores each category by matching patterns. If the prompt ends with '?'
    and has no strong animation signals, prefer explanation.
    """
    p = (prompt or "").strip()
    if not p:
        return "animation"

    explanation_score = sum(1 for pat in _EXPLANATION_PATTERNS if pat.search(p))
    animation_score = sum(1 for pat in _ANIMATION_PATTERNS if pat.search(p))

    # Question-mark bonus for explanation
    if p.rstrip().endswith("?"):
        explanation_score += 1

    if explanation_score > animation_score:
        return "explanation"
    return "animation"


# System prompt for conversational (non-animation) responses
CHAT_SYSTEM_PROMPT = """\
You are a helpful educational assistant embedded in a Manim animation tool.
The user is currently viewing a Manim animation and may ask conceptual questions.

Rules:
1. Answer clearly, concisely, and accurately about the math/physics concept.
2. Reference the current animation context (variables, objects) when relevant.
3. Use plain text. Do NOT output code, markdown fences, or formatting.
4. Keep answers under 200 words unless a detailed explanation is needed.
5. If the user seems to actually want an animation change, tell them to phrase it as a request (e.g. "change the learning rate to 0.5").
"""


@csrf_exempt
def manim_chat(request):
    """POST /visualization/manim/chat/
    Dual-mode endpoint: routes to explanation or animation based on intent.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    # Proxy the chat endpoint to the Manim microservice. The microservice
    # already handles intent classification and returns the appropriate JSON.
    MANIM_API_BASE = os.environ.get("MANIM_API_BASE_URL", "http://127.0.0.1:8010")
    target = f"{MANIM_API_BASE.rstrip('/')}/manim/chat/"

    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        resp = requests.post(
            target,
            data=request.body,
            headers={"Content-Type": request.META.get("CONTENT_TYPE", "application/json")},
            timeout=_manim_proxy_timeout(),
        )
        try:
            payload = resp.json()
        except ValueError:
            return JsonResponse({"status": "error", "error": "Invalid JSON from manim service"}, status=502)
        payload = _rewrite_media_urls(payload, MANIM_API_BASE)
        return JsonResponse(payload, status=resp.status_code)
    except requests.RequestException as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=502)
