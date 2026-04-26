from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
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
