from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
import re
import shutil
import uuid
from typing import Any, Optional

# In-memory store for demo purposes
EQUATIONS_STORE = []
MANIM_THREADS: dict[str, dict[str, Any]] = {}


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
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body or b"{}")
        prompt = (data.get("prompt") or "").strip()
        domain = (data.get("domain") or "Mathematics").strip() or "Mathematics"
        base_code_id = (data.get("base_code_id") or data.get("template_id") or "").strip()
        thread_id = (data.get("thread_id") or "").strip()
        new_animation = bool(data.get("new_animation", False))
        render_only = bool(data.get("render_only", False))
        timeout_s_raw = data.get("timeout_s")
        if not prompt and not render_only:
            return JsonResponse({"error": "prompt is required"}, status=400)

        timeout_s = None
        if timeout_s_raw is not None:
            try:
                timeout_s = int(timeout_s_raw)
            except (TypeError, ValueError):
                return JsonResponse({"error": "timeout_s must be an integer (seconds)"}, status=400)
            if timeout_s < 30 or timeout_s > 900:
                return JsonResponse({"error": "timeout_s must be between 30 and 900 seconds"}, status=400)

        from .manim_service import generate_and_render, generate_and_render_continuation, generate_and_render_from_base_code, render_base_code_directly

        use_continuation = bool(thread_id and not new_animation and thread_id in MANIM_THREADS)
        if thread_id and not new_animation and thread_id not in MANIM_THREADS:
            return JsonResponse({"error": "Invalid or expired thread_id. Start a new animation."}, status=400)

        resolved_base_code_id = ""
        used_thread_id = thread_id or uuid.uuid4().hex

        if use_continuation:
            thread = MANIM_THREADS[thread_id]
            prior_user_requests = _extract_thread_user_requests(thread)
            previous_code = (thread.get("current_code") or "").strip()
            if not previous_code:
                return JsonResponse({"error": "No previous code available in this thread."}, status=400)

            resolved_base_code_id = (thread.get("base_code_id") or "").strip()
            video_tmp_path, code, provider = generate_and_render_continuation(
                previous_code=previous_code,
                user_request=prompt,
                domain=domain,
                prior_user_requests=prior_user_requests,
                base_code=thread.get("base_code"),
                timeout_s=timeout_s,
            )
        else:
            resolved_base_code_id = base_code_id or _auto_detect_base_code_id(prompt) or ""
            base_code: Optional[str] = None
            if render_only and resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = render_base_code_directly(
                    base_code=base_code,
                    timeout_s=timeout_s,
                )
            elif resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = generate_and_render_from_base_code(
                    base_code=base_code,
                    user_request=prompt,
                    domain=domain,
                    timeout_s=timeout_s,
                )
            else:
                video_tmp_path, code, provider = generate_and_render(
                    prompt=prompt,
                    domain=domain,
                    timeout_s=timeout_s,
                )

            MANIM_THREADS[used_thread_id] = {
                "domain": domain,
                "base_code_id": resolved_base_code_id or None,
                "base_code": base_code,
                "messages": [],
                "current_code": "",
            }

        thread_ref = MANIM_THREADS.get(used_thread_id)
        if thread_ref is None:
            thread_ref = {
                "domain": domain,
                "base_code_id": resolved_base_code_id or None,
                "base_code": None,
                "messages": [],
                "current_code": "",
            }
            MANIM_THREADS[used_thread_id] = thread_ref

        thread_ref["domain"] = domain
        thread_ref["messages"].append({"role": "user", "content": prompt})
        thread_ref["messages"] = thread_ref["messages"][-20:]
        thread_ref["current_code"] = code

        out_dir = os.path.join(settings.MEDIA_ROOT, "manim")
        os.makedirs(out_dir, exist_ok=True)
        out_name = f"{uuid.uuid4().hex}.mp4"
        out_path = os.path.join(out_dir, out_name)
        shutil.copyfile(video_tmp_path, out_path)

        return JsonResponse(
            {
                "status": "success",
                "provider": provider,
                "thread_id": used_thread_id,
                "continuation": use_continuation,
                "base_code_id": resolved_base_code_id or None,
                "code": code,
                "video_url": f"{settings.MEDIA_URL}manim/{out_name}",
            }
        )
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=500)


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

    try:
        info = _load_template_info(template_id)
        return JsonResponse({"status": "success", **info})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)


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

    try:
        data = json.loads(request.body or b"{}")
        prompt = (data.get("prompt") or "").strip()
        domain = (data.get("domain") or "Mathematics").strip() or "Mathematics"
        thread_id = (data.get("thread_id") or "").strip()

        if not prompt:
            return JsonResponse({"error": "prompt is required"}, status=400)

        intent = _classify_intent(prompt)

        # ── Explanation path ────────────────────────────────────────────────
        if intent == "explanation":
            from .manim_service import _call_llm, GROQ_MODEL

            # Build context from thread if available
            context_hint = ""
            if thread_id and thread_id in MANIM_THREADS:
                thread = MANIM_THREADS[thread_id]
                code_snippet = (thread.get("current_code") or "")[:1500]
                base_id = thread.get("base_code_id") or ""
                context_hint = (
                    f"\n\nCurrent animation context:\n"
                    f"- Template: {base_id or 'custom'}\n"
                    f"- Domain: {thread.get('domain', domain)}\n"
                    f"- Current code excerpt:\n{code_snippet}\n"
                )

            user_prompt = f"{prompt}{context_hint}"

            try:
                answer = _call_llm(user_prompt, model=GROQ_MODEL, system_prompt=CHAT_SYSTEM_PROMPT)
            except RuntimeError as e:
                answer = f"Sorry, I couldn't generate an explanation right now: {e}"

            # Store in thread messages if thread exists
            if thread_id and thread_id in MANIM_THREADS:
                t = MANIM_THREADS[thread_id]
                t["messages"].append({"role": "user", "content": prompt})
                t["messages"].append({"role": "assistant", "content": answer})
                t["messages"] = t["messages"][-20:]

            return JsonResponse({
                "status": "success",
                "type": "explanation",
                "message": answer,
                "thread_id": thread_id,
            })

        # ── Animation path ─ delegate to manim_generate logic ──────────────
        from .manim_service import (
            generate_and_render,
            generate_and_render_continuation,
            generate_and_render_from_base_code,
        )

        base_code_id = (data.get("base_code_id") or data.get("template_id") or "").strip()

        use_continuation = bool(thread_id and thread_id in MANIM_THREADS)
        if thread_id and thread_id not in MANIM_THREADS:
            return JsonResponse({"error": "Invalid or expired thread_id. Start a new animation."}, status=400)

        resolved_base_code_id = ""
        used_thread_id = thread_id or uuid.uuid4().hex

        if use_continuation:
            thread = MANIM_THREADS[thread_id]
            prior_user_requests = _extract_thread_user_requests(thread)
            previous_code = (thread.get("current_code") or "").strip()
            if not previous_code:
                return JsonResponse({"error": "No previous code available in this thread."}, status=400)

            resolved_base_code_id = (thread.get("base_code_id") or "").strip()
            video_tmp_path, code, provider = generate_and_render_continuation(
                previous_code=previous_code,
                user_request=prompt,
                domain=domain,
                prior_user_requests=prior_user_requests,
                base_code=thread.get("base_code"),
            )
        else:
            resolved_base_code_id = base_code_id or _auto_detect_base_code_id(prompt) or ""
            base_code: Optional[str] = None
            if resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = generate_and_render_from_base_code(
                    base_code=base_code,
                    user_request=prompt,
                    domain=domain,
                )
            else:
                video_tmp_path, code, provider = generate_and_render(
                    prompt=prompt,
                    domain=domain,
                )

            MANIM_THREADS[used_thread_id] = {
                "domain": domain,
                "base_code_id": resolved_base_code_id or None,
                "base_code": base_code,
                "messages": [],
                "current_code": "",
            }

        thread_ref = MANIM_THREADS.get(used_thread_id)
        if thread_ref is None:
            thread_ref = {
                "domain": domain,
                "base_code_id": resolved_base_code_id or None,
                "base_code": None,
                "messages": [],
                "current_code": "",
            }
            MANIM_THREADS[used_thread_id] = thread_ref

        thread_ref["domain"] = domain
        thread_ref["messages"].append({"role": "user", "content": prompt})
        thread_ref["messages"] = thread_ref["messages"][-20:]
        thread_ref["current_code"] = code

        out_dir = os.path.join(settings.MEDIA_ROOT, "manim")
        os.makedirs(out_dir, exist_ok=True)
        out_name = f"{uuid.uuid4().hex}.mp4"
        out_path = os.path.join(out_dir, out_name)
        shutil.copyfile(video_tmp_path, out_path)

        return JsonResponse({
            "status": "success",
            "type": "animation",
            "provider": provider,
            "thread_id": used_thread_id,
            "continuation": use_continuation,
            "base_code_id": resolved_base_code_id or None,
            "code": code,
            "video_url": f"{settings.MEDIA_URL}manim/{out_name}",
        })
    except Exception as e:
        return JsonResponse({"status": "error", "type": "error", "error": str(e)}, status=500)
