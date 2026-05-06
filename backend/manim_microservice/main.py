from __future__ import annotations

import json
import os
import re
import shutil
import threading
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from visualization.manim_service import (
    GROQ_MODEL,
    OLLAMA_MODEL,
    _call_llm,
    generate_and_render,
    generate_and_render_continuation,
    generate_and_render_from_base_code,
    render_base_code_directly,
)

APP_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = APP_DIR / "templates_manim"
MEDIA_ROOT = Path(os.environ.get("MANIM_MEDIA_ROOT", str(APP_DIR / "media")))
MEDIA_DIR = MEDIA_ROOT / "manim"
STATE_DIR = Path(os.environ.get("MANIM_STATE_DIR", str(APP_DIR / "state")))
STATE_FILE = STATE_DIR / "manim_threads.json"

SLUG_TO_JSON: dict[str, str] = {
    "math.gradient_descent": "gradient_descent.json",
    "math.eigenvalues": "eigenvalues.json",
    "math.fourier_series": "fourier_series.json",
    "physics.projectile_motion": "projectile.json",
    "physics.electric_field": "electric_field.json",
    "physics.wave_interference": "wave_interference.json",
}

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
    re.compile(r"=\s*\d", re.I),
]

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

THREAD_LOCK = threading.Lock()
MANIM_THREADS: dict[str, dict[str, Any]] = {}

app = FastAPI(title="Manim Microservice", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.environ.get("MANIM_CORS_ORIGINS", "*").split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")


class GenerateRequest(BaseModel):
    prompt: str = ""
    domain: str = "Mathematics"
    base_code_id: str = ""
    template_id: str = ""
    thread_id: str = ""
    new_animation: bool = False
    render_only: bool = False
    timeout_s: Optional[int] = Field(default=None, ge=30, le=900)


class ChatRequest(BaseModel):
    prompt: str
    domain: str = "Mathematics"
    base_code_id: str = ""
    template_id: str = ""
    thread_id: str = ""


def _ensure_storage() -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _load_state() -> None:
    if not STATE_FILE.exists():
        return
    try:
        with STATE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            MANIM_THREADS.clear()
            for key, value in data.items():
                if isinstance(key, str) and isinstance(value, dict):
                    MANIM_THREADS[key] = value
    except Exception:
        MANIM_THREADS.clear()


def _save_state() -> None:
    tmp_file = STATE_FILE.with_suffix(".tmp")
    with tmp_file.open("w", encoding="utf-8") as handle:
        json.dump(MANIM_THREADS, handle, ensure_ascii=False, indent=2)
    tmp_file.replace(STATE_FILE)


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

    path = TEMPLATE_DIR / fname
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _load_template_info(template_id: str) -> dict[str, Any]:
    fname = SLUG_TO_JSON.get(template_id)
    if not fname:
        raise ValueError(f"Unknown template_id: {template_id}")

    path = TEMPLATE_DIR / fname
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _auto_detect_base_code_id(prompt: str) -> Optional[str]:
    p = (prompt or "").lower()
    if "projectile" in p:
        return "projectile"
    if "gradient" in p and "descent" in p:
        return "math.gradient_descent"
    if "eigen" in p:
        return "math.eigenvalues"
    if "fourier" in p:
        return "math.fourier_series"
    if "electric" in p and "field" in p:
        return "physics.electric_field"
    if "wave" in p and "interference" in p:
        return "physics.wave_interference"
    return None


def _classify_intent(prompt: str) -> str:
    p = (prompt or "").strip()
    if not p:
        return "animation"

    explanation_score = sum(1 for pat in _EXPLANATION_PATTERNS if pat.search(p))
    animation_score = sum(1 for pat in _ANIMATION_PATTERNS if pat.search(p))

    if p.rstrip().endswith("?"):
        explanation_score += 1

    if explanation_score > animation_score:
        return "explanation"
    return "animation"


def _extract_thread_user_requests(thread: dict[str, Any]) -> list[str]:
    messages = thread.get("messages", []) if isinstance(thread, dict) else []
    requests: list[str] = []
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = (msg.get("content") or "").strip()
            if content:
                requests.append(content)
    return requests


def _copy_video_to_media(video_path: str) -> str:
    out_name = f"{uuid.uuid4().hex}.mp4"
    out_path = MEDIA_DIR / out_name
    shutil.copyfile(video_path, out_path)
    return f"/media/manim/{out_name}"


def _get_thread(thread_id: str) -> dict[str, Any] | None:
    thread_id = (thread_id or "").strip()
    if not thread_id:
        return None
    return MANIM_THREADS.get(thread_id)


def _resolve_base_code_id(prompt: str, request: GenerateRequest) -> str:
    return (request.base_code_id or request.template_id or "").strip() or _auto_detect_base_code_id(prompt) or ""


@app.on_event("startup")
def _startup() -> None:
    _ensure_storage()
    _load_state()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "threads": len(MANIM_THREADS),
        "media_dir": str(MEDIA_DIR),
    }


@app.get("/manim/template-info/")
def template_info(id: str = "") -> JSONResponse:
    template_id = (id or "").strip()
    if not template_id:
        raise HTTPException(status_code=400, detail="id query parameter is required")

    fname = SLUG_TO_JSON.get(template_id)
    if not fname:
        raise HTTPException(status_code=400, detail=f"Unknown template_id: {template_id}")

    try:
        info = _load_template_info(template_id)
        return JSONResponse({"status": "success", **info})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/manim/generate/")
def manim_generate(request: GenerateRequest) -> JSONResponse:
    prompt = (request.prompt or "").strip()
    domain = (request.domain or "Mathematics").strip() or "Mathematics"
    base_code_id = _resolve_base_code_id(prompt, request)
    thread_id = (request.thread_id or "").strip()
    new_animation = bool(request.new_animation)
    render_only = bool(request.render_only)

    if not prompt and not render_only:
        raise HTTPException(status_code=400, detail="prompt is required")

    if thread_id and not new_animation and thread_id not in MANIM_THREADS:
        raise HTTPException(status_code=400, detail="Invalid or expired thread_id. Start a new animation.")

    used_thread_id = thread_id or uuid.uuid4().hex
    resolved_base_code_id = ""
    base_code: Optional[str] = None

    try:
        if thread_id and not new_animation and thread_id in MANIM_THREADS:
            thread = MANIM_THREADS[thread_id]
            prior_user_requests = _extract_thread_user_requests(thread)
            previous_code = (thread.get("current_code") or "").strip()
            if not previous_code:
                raise HTTPException(status_code=400, detail="No previous code available in this thread.")

            resolved_base_code_id = (thread.get("base_code_id") or "").strip()
            video_tmp_path, code, provider = generate_and_render_continuation(
                previous_code=previous_code,
                user_request=prompt,
                domain=domain,
                prior_user_requests=prior_user_requests,
                base_code=thread.get("base_code"),
                timeout_s=request.timeout_s,
            )
        else:
            resolved_base_code_id = base_code_id
            if render_only and resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = render_base_code_directly(base_code=base_code, timeout_s=request.timeout_s)
            elif resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = generate_and_render_from_base_code(
                    base_code=base_code,
                    user_request=prompt,
                    domain=domain,
                    timeout_s=request.timeout_s,
                )
            else:
                video_tmp_path, code, provider = generate_and_render(prompt=prompt, domain=domain, timeout_s=request.timeout_s)

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
        _save_state()

        video_url = _copy_video_to_media(video_tmp_path)
        return JSONResponse(
            {
                "status": "success",
                "provider": provider,
                "thread_id": used_thread_id,
                "continuation": bool(thread_id and not new_animation and thread_id in MANIM_THREADS),
                "base_code_id": resolved_base_code_id or None,
                "code": code,
                "video_url": video_url,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse({"status": "error", "error": str(exc)}, status_code=500)


@app.post("/manim/chat/")
def manim_chat(request: ChatRequest) -> JSONResponse:
    prompt = (request.prompt or "").strip()
    domain = (request.domain or "Mathematics").strip() or "Mathematics"
    thread_id = (request.thread_id or "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    thread = _get_thread(thread_id)

    try:
        intent = _classify_intent(prompt)

        if intent == "explanation":
            context_hint = ""
            if thread:
                code_snippet = (thread.get("current_code") or "")[:1500]
                base_id = thread.get("base_code_id") or ""
                context_hint = (
                    f"\n\nCurrent animation context:\n"
                    f"- Template: {base_id or 'custom'}\n"
                    f"- Domain: {thread.get('domain', domain)}\n"
                    f"- Current code excerpt:\n{code_snippet}\n"
                )

            user_prompt = f"{prompt}{context_hint}"
            answer = _call_llm(user_prompt, system_prompt=CHAT_SYSTEM_PROMPT)

            if thread:
                thread["messages"].append({"role": "user", "content": prompt})
                thread["messages"].append({"role": "assistant", "content": answer})
                thread["messages"] = thread["messages"][-20:]
                _save_state()

            return JSONResponse(
                {
                    "status": "success",
                    "type": "explanation",
                    "message": answer,
                    "thread_id": thread_id,
                }
            )

        base_code_id = (request.base_code_id or request.template_id or "").strip()
        use_continuation = bool(thread_id and thread_id in MANIM_THREADS)
        if thread_id and thread_id not in MANIM_THREADS:
            raise HTTPException(status_code=400, detail="Invalid or expired thread_id. Start a new animation.")

        used_thread_id = thread_id or uuid.uuid4().hex
        resolved_base_code_id = ""
        base_code: Optional[str] = None

        if use_continuation:
            thread = MANIM_THREADS[thread_id]
            prior_user_requests = _extract_thread_user_requests(thread)
            previous_code = (thread.get("current_code") or "").strip()
            if not previous_code:
                raise HTTPException(status_code=400, detail="No previous code available in this thread.")

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
            if resolved_base_code_id:
                base_code = _load_base_code_by_id(resolved_base_code_id)
                video_tmp_path, code, provider = generate_and_render_from_base_code(base_code=base_code, user_request=prompt, domain=domain)
            else:
                video_tmp_path, code, provider = generate_and_render(prompt=prompt, domain=domain)

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
        _save_state()

        video_url = _copy_video_to_media(video_tmp_path)
        return JSONResponse(
            {
                "status": "success",
                "type": "animation",
                "provider": provider,
                "thread_id": used_thread_id,
                "continuation": use_continuation,
                "base_code_id": resolved_base_code_id or None,
                "code": code,
                "video_url": video_url,
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse({"status": "error", "type": "error", "error": str(exc)}, status_code=500)
