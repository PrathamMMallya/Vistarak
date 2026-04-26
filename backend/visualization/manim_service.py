import ast
import os
import re
import subprocess
import tempfile
import uuid
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Optional; backend should still start without python-dotenv installed.
    pass


SYSTEM_PROMPT = """\
You are an expert at writing Manim Community Edition (v0.20.1) Python code.

RULES — follow every single one:
1. Output ONLY valid Python code. No markdown fences, no explanation, no comments outside the code.
2. Always start with: from manim import *
3. Define exactly ONE class that inherits from Scene.
4. The class MUST be named `GeneratedScene`.
5. Implement the `construct` method with the animation.
6. Keep it simple and guaranteed to render — avoid complex external assets.
7. Use self.play(), self.wait(), Create, Transform, FadeIn, FadeOut, Write, Text, MarkupText, Axes, etc.
8. Do NOT import os, subprocess, sys, shutil, pathlib, or any module beyond manim.
9. Do NOT use eval(), exec(), open(), __import__(), or compile().
10. Ensure all objects are properly added to the scene before animating them.
11. Do NOT use end_angle for Arc/Angle; use start_angle and angle instead.
12. Use 3D points (x, y, 0) for VMobject/Line points; do not use 2D tuples.
13. Do NOT use Tex(...) or MathTex(...); use Text(...) or MarkupText(...) only.
"""

REVIEW_SYSTEM_PROMPT = """\
You are a strict Manim Community Edition (v0.20.1) code reviewer.

Goals:
1. Validate the code renders without errors in Manim v0.20.1.
2. Fix invalid APIs, missing imports, or invalid point shapes.
3. Keep the structure simple and render-safe.

Rules:
- Output ONLY valid Python code. No markdown, no explanations.
- Keep exactly one Scene class named GeneratedScene.
- Do NOT introduce external imports beyond manim.
"""

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MAX_BASE_CODE_PROMPT_CHARS = 9000
MAX_CONTINUATION_CODE_PROMPT_CHARS = 11000
MAX_REVIEW_CODE_CHARS = 10000
MAX_HISTORY_ITEMS = 6
MAX_HISTORY_ITEM_CHARS = 220

BLOCKED_MODULES = {
    "os",
    "subprocess",
    "sys",
    "shutil",
    "pathlib",
    "socket",
    "http",
    "urllib",
    "requests",
    "ctypes",
    "multiprocessing",
    "threading",
    "signal",
    "importlib",
}
BLOCKED_BUILTINS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "breakpoint",
}


def _clip_text_middle(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars < 80:
        return text[:max_chars]
    head_len = int(max_chars * 0.65)
    tail_len = max_chars - head_len - len("\n# ... trimmed ...\n")
    if tail_len < 0:
        tail_len = 0
    return text[:head_len] + "\n# ... trimmed ...\n" + (text[-tail_len:] if tail_len else "")


def _prepare_history(prior_user_requests: list[str]) -> list[str]:
    if not prior_user_requests:
        return []
    recent = prior_user_requests[-MAX_HISTORY_ITEMS:]
    return [_clip_text_middle((req or "").strip(), MAX_HISTORY_ITEM_CHARS) for req in recent if (req or "").strip()]


def _normalize_ollama_host(host: str | None) -> str:
    # Not used anymore for Groq
    return "https://api.groq.com/openai/v1/chat/completions"


def _extract_code(raw: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", raw, re.DOTALL)
    return m.group(1).strip() if m else raw.strip()


def _validate_scene_class(code: str) -> str:
    if "class GeneratedScene" not in code:
        m = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", code)
        if m:
            old_name = m.group(1)
            code = code.replace(f"class {old_name}(Scene)", "class GeneratedScene(Scene)")
            code = code.replace(f"class {old_name} (Scene)", "class GeneratedScene(Scene)")
        else:
            raise ValueError("Generated code does not contain a Scene subclass.")
    return code


def _is_code_safe(code: str) -> tuple[bool, str]:
    for mod in BLOCKED_MODULES:
        if re.search(rf"\bimport\s+{mod}\b", code) or re.search(rf"\bfrom\s+{mod}\b", code):
            return False, f"Blocked import: {mod}"

    for fn in BLOCKED_BUILTINS:
        if re.search(rf"\b{fn}\s*\(", code):
            return False, f"Blocked function call: {fn}"

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} (line {e.lineno})"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BLOCKED_MODULES:
                    return False, f"Blocked import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in BLOCKED_MODULES:
                    return False, f"Blocked import: {node.module}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_BUILTINS:
                return False, f"Blocked call: {node.func.id}()"
            if isinstance(node.func, ast.Attribute) and node.func.attr in BLOCKED_BUILTINS:
                return False, f"Blocked call: .{node.func.attr}()"

    return True, "OK"


def _validate_generated_code_or_raise(code: str) -> None:
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"SyntaxError: {e.msg} (line {e.lineno})") from e

    if re.search(r"\.animate\.move_along\s*\(", code):
        raise ValueError("Invalid Manim API: .animate.move_along(...) not supported.")
    if re.search(r"\bmove_along\s*\(", code):
        raise ValueError("Invalid Manim API: move_along(...) is not valid; use MoveAlongPath.")
    if re.search(r"\bend_angle\s*=", code):
        raise ValueError(
            "Invalid Manim API: end_angle is not supported; use start_angle and angle (end - start)."
        )
    if re.search(r"\badd_points\s*\(", code):
        raise ValueError(
            "Invalid Manim API: VMobject.add_points(...) does not exist; use add_points_as_corners or set_points_as_corners."
        )
    if re.search(r"\b(MathTex|Tex)\s*\(", code):
        raise ValueError("Invalid pipeline rule: Tex/MathTex are not allowed; use Text/MarkupText.")


def _build_user_prompt(prompt: str, domain: str) -> str:
    return (
        f"Create a Manim animation for the following {domain} concept in Manim Community v0.20.1:\n\n"
        f"{prompt}\n\n"
        "Remember: output ONLY valid Python code, one Scene class named GeneratedScene."
    )


def _build_base_code_user_prompt(base_code: str, user_request: str, domain: str) -> str:
    clipped_base_code = _clip_text_middle(base_code, MAX_BASE_CODE_PROMPT_CHARS)
    return (
        f"Create a Manim animation for the following {domain} concept in Manim Community v0.20.1.\n\n"
        "You are given BASE_CODE. Keep the structure and animation flow similar, and only apply the minimum changes needed for USER_REQUEST.\n"
        "Do not invent unrelated elements or large structural rewrites unless required.\n\n"
        f"BASE_CODE:\n{clipped_base_code}\n\n"
        f"USER_REQUEST:\n{user_request}\n\n"
        "Return ONLY valid Python code, starting with `from manim import *`, one Scene class named GeneratedScene."
    )


def _build_continuation_user_prompt(
    previous_code: str,
    user_request: str,
    domain: str,
    prior_user_requests: list[str],
    base_code: str | None = None,
) -> str:
    prepared_history = _prepare_history(prior_user_requests)
    history_text = "\n".join([f"- {req}" for req in prepared_history]) if prepared_history else "- (none)"
    clipped_previous_code = _clip_text_middle(previous_code, MAX_CONTINUATION_CODE_PROMPT_CHARS)
    base_block = ""
    if base_code:
        clipped_base = _clip_text_middle(base_code, int(MAX_BASE_CODE_PROMPT_CHARS * 0.45))
        base_block = f"BASE_CODE (reference excerpt):\n{clipped_base}\n\n"
    return (
        f"Continue an existing Manim animation conversation for a {domain} concept in Manim Community v0.20.1.\n\n"
        "This is NOT a fresh generation. You MUST preserve the current scene logic and make targeted edits based on the new user request.\n"
        "Prefer minimal diffs to the previous code unless the user asks for major change.\n\n"
        f"{base_block}"
        f"PREVIOUS_USER_REQUESTS:\n{history_text}\n\n"
        f"PREVIOUS_CODE:\n{clipped_previous_code}\n\n"
        f"NEW_USER_REQUEST:\n{user_request}\n\n"
        "Return ONLY valid Python code, starting with `from manim import *`, one Scene class named GeneratedScene."
    )


def _build_template_user_prompt(template: dict[str, Any], user_request: str) -> str:
    meta = template.get("meta", {}) if isinstance(template, dict) else {}
    title = meta.get("title") or meta.get("template_id") or "Template animation"
    domain = meta.get("domain") or "Mathematics"
    template_json = json.dumps(template, ensure_ascii=False, indent=2)

    return (
        "You MUST generate a Manim animation strictly from the TEMPLATE JSON below.\n"
        f"Template title: {title}\n"
        f"Domain: {domain}\n\n"
        "Manim version: v0.20.1\n\n"
        f"TEMPLATE_JSON:\n{template_json}\n\n"
        f"USER_REQUEST:\n{user_request}\n\n"
        "Rules:\n"
        "- The template JSON is the single source of truth. Do not invent new scene objects unless explicitly requested.\n"
        "- Follow the template's step/timeline semantics and render a clean educational animation.\n"
        "- If USER_REQUEST asks for parameter changes, apply them by adjusting values while keeping the same structure.\n"
        "- Output ONLY valid Python code, starting with `from manim import *`, one Scene class named GeneratedScene.\n"
    )


def _build_retry_user_prompt(prompt: str, domain: str, error_hint: str) -> str:
    return (
        f"Create a Manim animation for the following {domain} concept in Manim Community v0.20.1:\n\n"
        f"{prompt}\n\n"
        "Fix the previous error and ensure the code renders in Manim Community v0.20.1.\n"
        f"Error hint: {error_hint}\n\n"
        "Important constraints:\n"
        "- Do NOT use dot.animate.move_along(...) or any .move_along method.\n"
        "- If moving an object along a path, use MoveAlongPath(mobject, path) or an updater/UpdateFromAlphaFunc.\n"
        "- Do NOT repeat keyword arguments in function calls (e.g. rate_func=... twice).\n"
        "- Do NOT use end_angle for Arc/Angle; use start_angle and angle (end - start).\n"
        "- Do NOT call add_points(...); for paths use add_points_as_corners([...]) or set_points_as_corners([...]).\n"
        "- Use 3D points (x, y, 0) when setting points for VMobject/Line/Path; do not pass 2D tuples.\n"
        "- Do NOT use Tex/MathTex; render formulas with Text/MarkupText and unicode symbols.\n"
        "- Output ONLY valid Python code, one Scene class named GeneratedScene."
    )


def _call_groq(user_prompt: str, model: str, system_prompt: str) -> str:
    api_key = GROQ_API_KEY
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4096,
        }
    ).encode("utf-8")

    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            body = response.read().decode("utf-8")
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
        raise RuntimeError(f"Groq request failed (HTTP {e.code}): {details or e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Could not reach Groq API: {e.reason}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response from Groq: {body[:500]}") from e

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Groq returned an empty response.")
    
    content = choices[0].get("message", {}).get("content", "")
    if not content.strip():
        raise RuntimeError("Groq returned empty message content.")

    return content.strip()


def _call_groq_review(code: str, error_hint: str | None = None) -> str:
    if len(code) > MAX_REVIEW_CODE_CHARS:
        raise RuntimeError("Review skipped: code too large for safe review payload.")

    compact_error_hint = _clip_text_middle(error_hint or "None", 500)
    review_prompt = (
        "Review and fix this Manim v0.20.1 code.\n"
        "Return the corrected full code only.\n\n"
        f"ERROR_HINT:\n{compact_error_hint}\n\n"
        f"CODE:\n{code}\n"
    )
    return _call_groq(review_prompt, model=GROQ_MODEL, system_prompt=REVIEW_SYSTEM_PROMPT)


def _review_with_feedback(
    code: str,
    max_rounds: int = 2,
    initial_error_hint: str | None = None,
) -> str:
    error_hint: str | None = initial_error_hint
    current = code

    if len(current) > MAX_REVIEW_CODE_CHARS:
        return current

    for _ in range(max_rounds):
        try:
            raw = _call_groq_review(current, error_hint=error_hint)
        except RuntimeError as e:
            msg = str(e)
            if "Request too large" in msg or "rate_limit_exceeded" in msg or "Review skipped" in msg:
                return current
            raise
        reviewed = _validate_scene_class(_extract_code(raw))
        safe, reason = _is_code_safe(reviewed)
        if not safe:
            raise RuntimeError(f"Groq review rejected for safety: {reason}")
        try:
            _validate_generated_code_or_raise(reviewed)
            return reviewed
        except Exception as e:
            error_hint = str(e)[:300]
            current = reviewed
    raise RuntimeError(f"Groq review failed to validate after {max_rounds} rounds.")


def generate_manim_code(prompt: str, domain: str) -> tuple[str, str]:
    user_prompt = _build_user_prompt(prompt, domain)

    raw = _call_groq(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"Groq ({GROQ_MODEL}) → Groq review ({GROQ_MODEL})"


def generate_manim_code_from_base_code(base_code: str, user_request: str, domain: str) -> tuple[str, str]:
    user_prompt = _build_base_code_user_prompt(base_code=base_code, user_request=user_request, domain=domain)

    raw = _call_groq(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"Groq ({GROQ_MODEL}) → Groq review ({GROQ_MODEL}, base-code)"


def generate_manim_code_continuation(
    previous_code: str,
    user_request: str,
    domain: str,
    prior_user_requests: list[str],
    base_code: str | None = None,
) -> tuple[str, str]:
    user_prompt = _build_continuation_user_prompt(
        previous_code=previous_code,
        user_request=user_request,
        domain=domain,
        prior_user_requests=prior_user_requests,
        base_code=base_code,
    )

    raw = _call_groq(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"Groq ({GROQ_MODEL}) → Groq review ({GROQ_MODEL}, continuation)"


def generate_manim_code_from_template(template: dict[str, Any], user_request: str) -> tuple[str, str]:
    user_prompt = _build_template_user_prompt(template, user_request)

    raw = _call_groq(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"Groq ({GROQ_MODEL}) → Groq review ({GROQ_MODEL}, template)"


def render_manim_to_mp4(code: str, timeout_s: int = 180) -> str:
    sid = uuid.uuid4().hex[:8]
    work_dir = os.path.join(tempfile.gettempdir(), f"manim_{sid}")
    os.makedirs(work_dir, exist_ok=True)

    script_path = os.path.join(work_dir, "scene.py")
    media_dir = os.path.join(work_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    cmd = [
        "manim",
        "render",
        "-ql",
        "--media_dir",
        media_dir,
        script_path,
        "GeneratedScene",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=work_dir,
    )
    if result.returncode != 0:
        stderr_tail = (result.stderr or "")[-3000:]
        stdout_tail = (result.stdout or "")[-1000:]
        raise RuntimeError(f"Manim render failed (exit {result.returncode}):\n{stderr_tail}\n{stdout_tail}")

    for root, _, files in os.walk(media_dir):
        for fname in files:
            if fname.endswith(".mp4"):
                return os.path.join(root, fname)

    raise FileNotFoundError("Manim did not produce an .mp4 file.")


def generate_and_render(prompt: str, domain: str, timeout_s: int | None = None) -> tuple[str, str, str]:
    code, provider = generate_manim_code(prompt, domain)
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(code)

    try:
        video_path = render_manim_to_mp4(code, timeout_s=timeout_s or 180)
        return video_path, code, provider
    except Exception as render_err:
        repaired_code = _review_with_feedback(
            code,
            max_rounds=3,
            initial_error_hint=str(render_err)[:1200],
        )
        safe2, reason2 = _is_code_safe(repaired_code)
        if not safe2:
            raise RuntimeError(f"Render-repair code was rejected for safety: {reason2}")
        _validate_generated_code_or_raise(repaired_code)

        video_path = render_manim_to_mp4(repaired_code, timeout_s=timeout_s or 180)
        return video_path, repaired_code, (provider + " -> render-repair")


def generate_and_render_from_base_code(
    base_code: str,
    user_request: str,
    domain: str,
    timeout_s: int | None = None,
) -> tuple[str, str, str]:
    code, provider = generate_manim_code_from_base_code(base_code=base_code, user_request=user_request, domain=domain)
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(code)

    try:
        video_path = render_manim_to_mp4(code, timeout_s=timeout_s or 180)
        return video_path, code, provider
    except Exception as render_err:
        repaired_code = _review_with_feedback(
            code,
            max_rounds=3,
            initial_error_hint=str(render_err)[:1200],
        )
        safe2, reason2 = _is_code_safe(repaired_code)
        if not safe2:
            raise RuntimeError(f"Render-repair code was rejected for safety: {reason2}")
        _validate_generated_code_or_raise(repaired_code)

        video_path = render_manim_to_mp4(repaired_code, timeout_s=timeout_s or 180)
        return video_path, repaired_code, (provider + " -> render-repair")


def generate_and_render_continuation(
    previous_code: str,
    user_request: str,
    domain: str,
    prior_user_requests: list[str],
    base_code: str | None = None,
    timeout_s: int | None = None,
) -> tuple[str, str, str]:
    code, provider = generate_manim_code_continuation(
        previous_code=previous_code,
        user_request=user_request,
        domain=domain,
        prior_user_requests=prior_user_requests,
        base_code=base_code,
    )
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(code)

    try:
        video_path = render_manim_to_mp4(code, timeout_s=timeout_s or 180)
        return video_path, code, provider
    except Exception as render_err:
        repaired_code = _review_with_feedback(
            code,
            max_rounds=3,
            initial_error_hint=str(render_err)[:1200],
        )
        safe2, reason2 = _is_code_safe(repaired_code)
        if not safe2:
            raise RuntimeError(f"Render-repair code was rejected for safety: {reason2}")
        _validate_generated_code_or_raise(repaired_code)

        video_path = render_manim_to_mp4(repaired_code, timeout_s=timeout_s or 180)
        return video_path, repaired_code, (provider + " -> render-repair")


def generate_and_render_from_template(
    template: dict[str, Any],
    user_request: str,
    timeout_s: int | None = None,
) -> tuple[str, str, str]:
    code, provider = generate_manim_code_from_template(template, user_request)
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    _validate_generated_code_or_raise(code)

    try:
        video_path = render_manim_to_mp4(code, timeout_s=timeout_s or 180)
        return video_path, code, provider
    except Exception as render_err:
        repaired_code = _review_with_feedback(
            code,
            max_rounds=3,
            initial_error_hint=str(render_err)[:1200],
        )
        safe2, reason2 = _is_code_safe(repaired_code)
        if not safe2:
            raise RuntimeError(f"Render-repair code was rejected for safety: {reason2}")
        _validate_generated_code_or_raise(repaired_code)

        video_path = render_manim_to_mp4(repaired_code, timeout_s=timeout_s or 180)
        return video_path, repaired_code, (provider + " -> render-repair")


def render_base_code_directly(base_code: str, timeout_s: int | None = None) -> tuple[str, str, str]:
    """Render the base code directly without LLM processing."""
    safe, reason = _is_code_safe(base_code)
    if not safe:
        raise RuntimeError(f"Base code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(base_code)

    video_path = render_manim_to_mp4(base_code, timeout_s=timeout_s or 180)
    return video_path, base_code, "Template (Direct Render)"