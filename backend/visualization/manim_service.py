import ast
import logging
import os
import re
import subprocess
import sys
import tempfile
import uuid
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

logger = logging.getLogger("manim_service")
logger.setLevel(logging.DEBUG)

try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Optional; backend should still start without python-dotenv installed.
    pass


def _has_latex() -> bool:
    """Check whether a LaTeX compiler is available and functional on this system."""
    try:
        # 1. Basic version check
        result = subprocess.run(
            ["latex", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            logger.warning("[INIT] LaTeX command 'latex' not found or failed.")
            return False

        # 2. Functional check (test compilation)
        # We try to compile a tiny snippet to ensure the installation is functional
        # and not blocked by missing packages or dialogs.
        with tempfile.TemporaryDirectory() as tmp_dir:
            tex_content = r"\documentclass{article}\begin{document}X\end{document}"
            tex_file = os.path.join(tmp_dir, "test.tex")
            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(tex_content)
            
            # Run latex in non-interactive mode
            test_res = subprocess.run(
                ["latex", "-interaction=batchmode", "test.tex"],
                cwd=tmp_dir,
                capture_output=True,
                timeout=15,
            )
            if test_res.returncode != 0:
                logger.warning("[INIT] LaTeX found but test compilation failed (exit %d).", test_res.returncode)
                return False
        
        logger.info("[INIT] LaTeX available and functional.")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        logger.warning("[INIT] LaTeX check failed: %s", str(e))
        return False


LATEX_AVAILABLE: bool = _has_latex()

_LATEX_RULE_ALLOWED = (
    "13. You MAY use Tex(...) and MathTex(...) for mathematical expressions — LaTeX is available on this system."
)
_LATEX_RULE_BLOCKED = (
    "13. Do NOT use Tex(...) or MathTex(...); use Text(...) or MarkupText(...) only — LaTeX is NOT installed."
)

SYSTEM_PROMPT = f"""\
You are an expert at writing Manim Community Edition (v0.20.1) Python code.

CRITICAL: Do NOT output any thinking, reasoning, explanations, or text before/after the code.
Output ONLY pure Python code. No markdown, no comments, no anything else.

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
{_LATEX_RULE_ALLOWED if LATEX_AVAILABLE else _LATEX_RULE_BLOCKED}
14. Do NOT pass `z_range` to 2D coordinate systems like `Axes` or `NumberPlane`; use `ThreeDAxes` if 3D is needed.
"""

REVIEW_SYSTEM_PROMPT = """\
You are a strict Manim Community Edition (v0.20.1) code reviewer.

CRITICAL: Do NOT output any thinking, reasoning, explanations, or text before/after the code.
Output ONLY pure Python code. No markdown, no comments, no anything else.

Goals:
1. Validate the code renders without errors in Manim v0.20.1.
2. Fix invalid APIs, missing imports, or invalid point shapes.
3. Keep the structure simple and render-safe.

Rules:
- Output ONLY valid Python code. No markdown, no explanations.
- Keep exactly one Scene class named GeneratedScene.
- Do NOT introduce external imports beyond manim.
"""

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.environ.get("CLOUD_API_KEY", os.environ.get("GROQ_API_KEY", ""))

# --- Provider Config ---
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", os.environ.get("PROVIDER", "GROQ")).upper()
LLM_SERVER_URL = os.environ.get("LLM_SERVER_URL", os.environ.get("LLAMA_URL", ""))

MAX_BASE_CODE_PROMPT_CHARS = 9000
MAX_CONTINUATION_CODE_PROMPT_CHARS = 11000
MAX_REVIEW_CODE_CHARS = 10000
MAX_HISTORY_ITEMS = 6
MAX_HISTORY_ITEM_CHARS = 220
MAX_RENDER_RETRIES = 3

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
    if not raw or not raw.strip():
        raise ValueError("Groq returned empty response")
    
    cleaned = raw
    
    # Strip Qwen reasoning tags (aggressive approach)
    # Handle both <think>...</think> and <think> without closing tag
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*?(?=from\s+manim|```|class\s+GeneratedScene)", "", cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()
    
    # If after stripping think tags we're left with almost nothing, it's likely reasoning-only
    if not cleaned or len(cleaned) < 50:
        raise ValueError(
            f"LLM returned only reasoning text, no code. This suggests the system prompt is not being followed. "
            f"Please verify:\n"
            f"1. GROQ_API_KEY is valid\n"
            f"2. Qwen model is accessible\n"
            f"3. Try disabling Qwen's reasoning mode or use a different model.\n"
            f"Raw response (first 200 chars): {raw[:200]}"
        )
    
    # Try to extract code from markdown fences first
    m = re.search(r"```(?:python)?\s*\n(.*?)```", cleaned, re.DOTALL)
    if m:
        extracted = m.group(1).strip()
        if extracted and re.search(r"(from\s+manim|class\s+\w+\s*\(\s*Scene)", extracted):
            return extracted
    
    # Find code starting from "from manim import *" or "class GeneratedScene"
    code_start_patterns = [
        r"(from\s+manim\s+import\s+\*.*)",
        r"(class\s+GeneratedScene\s*\(.*)",
    ]
    
    for pattern in code_start_patterns:
        m = re.search(pattern, cleaned, flags=re.DOTALL)
        if m:
            extracted = m.group(1).strip()
            if extracted:
                return extracted
    
    # Last resort: if cleaned text looks like Python, return it
    if cleaned and re.match(r"^\s*(from|import|class|def)", cleaned):
        return cleaned
    
    raise ValueError(
        f"Failed to extract code from response. LLM may be outputting reasoning instead of code.\n"
        f"Raw response (first 500 chars): {raw[:500]}"
    )


def _validate_scene_class(code: str) -> str:
    if not code or not code.strip():
        raise ValueError("Generated code is empty")
    
    # Additional check: ensure code doesn't look like reasoning/explanation
    if code.lower().startswith(("okay", "sure", "let me", "i will", "first", "the user wants")) and "class" not in code.lower():
        raise ValueError(f"Generated content appears to be explanation text, not code. Preview: {code[:200]}")
    
    if "class GeneratedScene" not in code:
        m = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", code)
        if m:
            old_name = m.group(1)
            code = code.replace(f"class {old_name}(Scene)", "class GeneratedScene(Scene)")
            code = code.replace(f"class {old_name} (Scene)", "class GeneratedScene(Scene)")
        else:
            code_preview = code[:300] if len(code) > 300 else code
            raise ValueError(f"Generated code does not contain a Scene subclass. Code preview: {code_preview}")
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
    if not LATEX_AVAILABLE and re.search(r"\b(MathTex|Tex)\s*\(", code):
        raise ValueError("Tex/MathTex require LaTeX which is not installed; use Text/MarkupText instead.")
    if re.search(r"\b(Axes|NumberPlane)\s*\([^)]*z_range", code):
        raise ValueError("Invalid Manim API: z_range is not supported for 2D Axes/NumberPlane; use ThreeDAxes instead.")


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
    latex_constraint = (
        "- You MAY use Tex/MathTex for math — LaTeX IS available.\n"
        if LATEX_AVAILABLE
        else "- Do NOT use Tex/MathTex — LaTeX is NOT installed; use Text/MarkupText and unicode symbols.\n"
    )
    return (
        f"Create a Manim animation for the following {domain} concept in Manim Community v0.20.1:\n\n"
        f"{prompt}\n\n"
        "The previous attempt FAILED to render. Fix the error and ensure the code renders correctly.\n"
        f"RENDER ERROR:\n{error_hint}\n\n"
        "Important constraints:\n"
        "- Do NOT use dot.animate.move_along(...) or any .move_along method.\n"
        "- If moving an object along a path, use MoveAlongPath(mobject, path) or an updater/UpdateFromAlphaFunc.\n"
        "- Do NOT repeat keyword arguments in function calls (e.g. rate_func=... twice).\n"
        "- Do NOT use end_angle for Arc/Angle; use start_angle and angle (end - start).\n"
        "- Do NOT call add_points(...); for paths use add_points_as_corners([...]) or set_points_as_corners([...]).\n"
        "- Use 3D points (x, y, 0) when setting points for VMobject/Line/Path; do not pass 2D tuples.\n"
        f"{latex_constraint}"
        "- Do NOT pass `z_range` to 2D coordinate systems like `Axes` or `NumberPlane`; use `ThreeDAxes` if 3D is needed.\n"
        "- Output ONLY valid Python code, one Scene class named GeneratedScene."
    )


def _build_render_error_repair_prompt(code: str, error_hint: str) -> str:
    """Build a prompt that sends the failing code + render error back to the LLM."""
    latex_constraint = (
        "- You MAY use Tex/MathTex for math — LaTeX IS available.\n"
        if LATEX_AVAILABLE
        else "- Do NOT use Tex/MathTex — LaTeX is NOT installed; use Text/MarkupText and unicode symbols.\n"
    )
    clipped_code = _clip_text_middle(code, MAX_REVIEW_CODE_CHARS)
    return (
        "The following Manim v0.20.1 code FAILED to render. Fix the error and return corrected code.\n\n"
        f"RENDER ERROR:\n{error_hint}\n\n"
        f"FAILING CODE:\n{clipped_code}\n\n"
        "Constraints:\n"
        f"{latex_constraint}"
        "- Do NOT use end_angle; use start_angle and angle.\n"
        "- Use 3D points (x, y, 0) for VMobject/Line.\n"
        "- Do NOT pass z_range to Axes/NumberPlane.\n"
        "- Output ONLY the corrected Python code, one Scene class named GeneratedScene."
    )


def _call_llm(user_prompt: str, model: str, system_prompt: str) -> str:
    if LLM_PROVIDER in ["LLAMA", "LLAMA.CPP"]:
        if not LLM_SERVER_URL:
            raise RuntimeError(f"LLM_SERVER_URL is not set in .env while LLM_PROVIDER is set to {LLM_PROVIDER}.")
        # Ensure the URL ends with the completions endpoint
        url = LLM_SERVER_URL.rstrip('/')
        if not url.endswith("/v1/chat/completions"):
            url = f"{url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        # For local Llama.cpp, we often use a dummy model name or the one it's loaded with
        model_name = "local-model" 
    else:
        api_key = GROQ_API_KEY
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set. Please set it before using the Manim generation service.")
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        model_name = model

    if not user_prompt or not user_prompt.strip():
        raise ValueError("User prompt is empty")

    logger.info("[LLM REQUEST] provider=%s model=%s prompt_length=%d chars", LLM_PROVIDER, model_name, len(user_prompt))

    payload = json.dumps(
        {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
            "stream": True,
        }
    ).encode("utf-8")

    request = Request(
        url,
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        response = urlopen(request, timeout=300)
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
        raise RuntimeError(f"{LLM_PROVIDER} request failed (HTTP {e.code}): {details or e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Could not reach {LLM_PROVIDER} API: {e.reason}") from e

    # ── Stream the response and print tokens live ──
    collected_content: list[str] = []
    print(f"\n{'='*60}", flush=True)
    print(f"[LLM STREAM] model={model}", flush=True)
    print(f"{'─'*60}", flush=True)

    try:
        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            if not line.startswith("data: "):
                continue
            data_str = line[len("data: "):]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if "error" in chunk:
                error_msg = chunk.get("error", {}).get("message", "Unknown error")
                raise RuntimeError(f"{LLM_PROVIDER} API error: {error_msg}")

            delta = chunk.get("choices", [{}])[0].get("delta", {})
            token = delta.get("content", "")
            if token:
                collected_content.append(token)
                # Print each token live to stdout
                sys.stdout.write(token)
                sys.stdout.flush()
    finally:
        response.close()

    print(f"\n{'─'*60}", flush=True)

    content = "".join(collected_content)

    if not content or not content.strip():
        raise RuntimeError(f"{LLM_PROVIDER} returned empty streamed content.")

    logger.info("[LLM RESPONSE] total_length=%d chars", len(content))
    print(f"[LLM DONE] received {len(content)} chars", flush=True)
    print(f"{'='*60}\n", flush=True)

    return content.strip()


def _call_llm_review(code: str, error_hint: str | None = None) -> str:
    if len(code) > MAX_REVIEW_CODE_CHARS:
        raise RuntimeError("Review skipped: code too large for safe review payload.")

    compact_error_hint = _clip_text_middle(error_hint or "None", 500)
    review_prompt = (
        "Review and fix this Manim v0.20.1 code.\n"
        "Return the corrected full code only.\n\n"
        f"ERROR_HINT:\n{compact_error_hint}\n\n"
        f"CODE:\n{code}\n"
    )
    logger.info("[REVIEW] Sending code for review (code_len=%d, error_hint=%s)", len(code), compact_error_hint[:120])
    return _call_llm(review_prompt, model=GROQ_MODEL, system_prompt=REVIEW_SYSTEM_PROMPT)


def _review_with_feedback(
    code: str,
    max_rounds: int = 2,
    initial_error_hint: str | None = None,
) -> str:
    error_hint: str | None = initial_error_hint
    current = code

    if len(current) > MAX_REVIEW_CODE_CHARS:
        logger.warning("[REVIEW] Skipping review — code too large (%d chars)", len(current))
        return current

    for round_num in range(1, max_rounds + 1):
        logger.info("[REVIEW ROUND %d/%d] error_hint=%s", round_num, max_rounds, (error_hint or "None")[:120])
        try:
            raw = _call_llm_review(current, error_hint=error_hint)
        except RuntimeError as e:
            msg = str(e)
            if "Request too large" in msg or "rate_limit_exceeded" in msg or "Review skipped" in msg:
                logger.warning("[REVIEW] Skipping remaining rounds — %s", msg[:200])
                return current
            raise
        reviewed = _validate_scene_class(_extract_code(raw))
        safe, reason = _is_code_safe(reviewed)
        if not safe:
            raise RuntimeError(f"{LLM_PROVIDER} review rejected for safety: {reason}")
        try:
            _validate_generated_code_or_raise(reviewed)
            logger.info("[REVIEW ROUND %d/%d] ✓ Passed validation", round_num, max_rounds)
            return reviewed
        except Exception as e:
            error_hint = str(e)[:300]
            logger.warning("[REVIEW ROUND %d/%d] ✗ Validation failed: %s", round_num, max_rounds, error_hint[:200])
            current = reviewed
    raise RuntimeError(f"{LLM_PROVIDER} review failed to validate after {max_rounds} rounds.")


def generate_manim_code(prompt: str, domain: str) -> tuple[str, str]:
    user_prompt = _build_user_prompt(prompt, domain)

    raw = _call_llm(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"{LLM_PROVIDER} → {LLM_PROVIDER} review"


def generate_manim_code_from_base_code(base_code: str, user_request: str, domain: str) -> tuple[str, str]:
    user_prompt = _build_base_code_user_prompt(base_code=base_code, user_request=user_request, domain=domain)

    raw = _call_llm(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"{LLM_PROVIDER} → {LLM_PROVIDER} review (base-code)"


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

    raw = _call_llm(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"{LLM_PROVIDER} → {LLM_PROVIDER} review (continuation)"


def generate_manim_code_from_template(template: dict[str, Any], user_request: str) -> tuple[str, str]:
    user_prompt = _build_template_user_prompt(template, user_request)

    raw = _call_llm(user_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
    code = _validate_scene_class(_extract_code(raw))
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")

    reviewed = _review_with_feedback(code)
    return reviewed, f"{LLM_PROVIDER} → {LLM_PROVIDER} review (template)"


def render_manim_to_mp4(code: str, timeout_s: int = 180) -> str:
    sid = uuid.uuid4().hex[:8]
    # Use a local temporary directory within the project to avoid drive-crossing issues
    # and potential permission problems in the system Temp directory.
    base_tmp = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp_manim")
    os.makedirs(base_tmp, exist_ok=True)
    
    work_dir = os.path.join(base_tmp, f"manim_{sid}")
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


def _render_with_retries(
    code: str,
    provider: str,
    timeout_s: int,
    max_retries: int = MAX_RENDER_RETRIES,
) -> tuple[str, str, str]:
    """Try to render `code`. On failure, send the error back to the LLM and retry."""
    current_code = code
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("[RENDER] Attempt %d/%d", attempt, max_retries)
            video_path = render_manim_to_mp4(current_code, timeout_s=timeout_s)
            suffix = f" -> render-repair x{attempt - 1}" if attempt > 1 else ""
            logger.info("[RENDER] ✓ Success on attempt %d", attempt)
            return video_path, current_code, (provider + suffix)
        except Exception as render_err:
            last_error = render_err
            error_text = str(render_err)[:1500]
            logger.warning(
                "[RENDER] ✗ Attempt %d/%d failed:\n%s",
                attempt, max_retries, error_text[:500],
            )
            print(f"\n{'!'*60}", flush=True)
            print(f"[RENDER FAILED] Attempt {attempt}/{max_retries}", flush=True)
            print(f"ERROR DETAILS:\n{error_text}", flush=True)
            print(f"{'!'*60}\n", flush=True)

            if attempt >= max_retries:
                break

            # ── Send the error + code back to the LLM for repair ──
            logger.info("[RENDER-REPAIR] Querying LLM with render error for attempt %d...", attempt + 1)
            repair_prompt = _build_render_error_repair_prompt(current_code, error_text)
            try:
                raw = _call_llm(repair_prompt, model=GROQ_MODEL, system_prompt=SYSTEM_PROMPT)
                repaired = _validate_scene_class(_extract_code(raw))
                safe, reason = _is_code_safe(repaired)
                if not safe:
                    logger.warning("[RENDER-REPAIR] Repaired code rejected for safety: %s", reason)
                    break
                _validate_generated_code_or_raise(repaired)
                current_code = repaired
                logger.info("[RENDER-REPAIR] LLM returned repaired code (%d chars), retrying render...", len(repaired))
            except Exception as repair_err:
                logger.warning("[RENDER-REPAIR] LLM repair itself failed: %s", str(repair_err)[:300])
                break

    raise RuntimeError(
        f"Manim render failed after {max_retries} attempts. Last error: {last_error}"
    )


def generate_and_render(prompt: str, domain: str, timeout_s: int | None = None) -> tuple[str, str, str]:
    code, provider = generate_manim_code(prompt, domain)
    safe, reason = _is_code_safe(code)
    if not safe:
        raise RuntimeError(f"Generated code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(code)
    return _render_with_retries(code, provider, timeout_s=timeout_s or 180)


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
    return _render_with_retries(code, provider, timeout_s=timeout_s or 180)


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
    return _render_with_retries(code, provider, timeout_s=timeout_s or 180)


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
    return _render_with_retries(code, provider, timeout_s=timeout_s or 180)


def render_base_code_directly(base_code: str, timeout_s: int | None = None) -> tuple[str, str, str]:
    """Render the base code directly without LLM processing."""
    safe, reason = _is_code_safe(base_code)
    if not safe:
        raise RuntimeError(f"Base code was rejected for safety: {reason}")
    _validate_generated_code_or_raise(base_code)

    video_path = render_manim_to_mp4(base_code, timeout_s=timeout_s or 180)
    return video_path, base_code, "Template (Direct Render)"