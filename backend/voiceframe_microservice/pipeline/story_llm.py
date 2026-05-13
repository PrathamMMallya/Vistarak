from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """
You are an expert children's story creator specializing in cartoon-style narratives.

GOAL:
Generate a structured, multi-scene story suitable for video generation and downstream image synthesis.

STORY REQUIREMENTS:
- Target audience: children aged 4-10
- STRICTLY follow the provided story topic or fable. Do not invent a different story.
- Tone: positive, engaging, emotionally expressive (or fitting the moral of the fable)
- Structure: clear beginning, middle, and end
- Maximum 3 characters total
- Characters must interact meaningfully and learn something
- Avoid repetition in dialogue

CHARACTER DESCRIPTION RULES (STRICT):
- MUST remain IDENTICAL across all scenes
- ONLY include: species, colors, eyes, clothing
- NO actions, emotions, poses, sizes, or states
- NO stylistic or descriptive words (e.g., cute, big, small, happy, detailed)
- NO animation or rendering terms (e.g., 3D, cinematic, realistic, stylized)
- Keep descriptions minimal and structured for downstream processing
- Format EXACTLY:
  "one [color] [species], [color] [body parts], [clothing] (Gender)"

BACKGROUND DESCRIPTION RULES:
- Use vivid, colorful, cartoon-style descriptions
- Can include motion, lighting, environment details
- Backgrounds should be standalone and verbose for every scene

SCENE RULES:
- Generate 2 to 4 scenes ONLY
- Each scene must progress the story
- Each scene must have a unique setting
- Scene duration must be between 30 and 90 seconds
- Scenes must be sequential and non-overlapping

DIALOGUE RULES:
- Use natural conversational tone
- Each dialogue line short (1-2 sentences)
- Alternate speakers where possible
- ALWAYS include emotion in parentheses after the character name

GAP RULES (STRICT):
- Use *GAP* (N) ONLY when a pause is narratively meaningful
- N must be GREATER THAN 5
- Maximum 1 GAP per scene

TIMESTAMP RULES:
- Each scene MUST include: (Start HH:MM:SS to End HH:MM:SS)

OUTPUT FORMAT (STRICT - NO EXTRA TEXT):

# Scene [Number]

## Background

[Description] ([Start HH:MM:SS] to [End HH:MM:SS])

## Characters

* [Name]: one [color] [species], [features], [clothing] (Gender)

## Dialogues

[Character Name] (Emotion): Dialogue

*GAP* (6)
[Character Name] (Emotion): Dialogue

---

STRICT OUTPUT RULES:
- Do not add explanations, notes, or extra formatting.
""".strip()


def _ollama_api_base() -> str:
    return (os.environ.get("OLLAMA_API_BASE") or os.environ.get("OLLAMA_HOST") or "").rstrip("/")


def _ollama_model() -> str:
    return (os.environ.get("VOICEFRAME_OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL") or "llama3.1:8b").strip()


def generate_story_markdown(prompt: str) -> str:
    provider = (os.environ.get("VOICEFRAME_LLM_PROVIDER") or "").strip().lower()
    if not provider:
        provider = "ollama" if _ollama_api_base() else ""

    if provider == "ollama":
        return _generate_via_ollama(prompt)
    if provider == "groq":
        return _generate_via_groq(prompt)

    allow_fallback = (os.environ.get("VOICEFRAME_ALLOW_FALLBACK_STORY") or "1").strip().lower() in ("1", "true", "yes")
    if allow_fallback:
        return _fallback_story(prompt)

    raise RuntimeError(
        "No LLM provider configured. Set VOICEFRAME_LLM_PROVIDER=ollama and OLLAMA_API_BASE (or OLLAMA_HOST), "
        "or set VOICEFRAME_LLM_PROVIDER=groq and GROQ_API_KEY."
    )


def _fallback_story(prompt: str) -> str:
    topic = (prompt or "a short moral story").strip()
    return (
        "# Scene 1\n\n"
        "## Background\n\n"
        f"A bright cartoon meadow where the story topic is introduced: {topic}. ([Start 00:00:00] to [End 00:00:35])\n\n"
        "## Characters\n\n"
        "* Alex: one blue rabbit, white paws, red scarf (Male)\n"
        "* Mia: one green turtle, brown shell, yellow hat (Female)\n\n"
        "## Dialogues\n\n"
        "Alex (excited): Let's start our adventure!\n"
        "Mia (neutral): We should be careful and kind.\n"
        "---\n\n"
        "# Scene 2\n\n"
        "## Background\n\n"
        "A colorful riverbank with a small bridge and warm sunlight, where the moral is learned. ([Start 00:00:35] to [End 00:01:10])\n\n"
        "## Characters\n\n"
        "* Alex: one blue rabbit, white paws, red scarf (Male)\n"
        "* Mia: one green turtle, brown shell, yellow hat (Female)\n\n"
        "## Dialogues\n\n"
        "Alex (surprised): I understand now. Being patient helps everyone.\n"
        "Mia (happy): Exactly! Let's remember that lesson.\n"
        "---\n"
    )


def _generate_via_ollama(prompt: str) -> str:
    api_base = _ollama_api_base()
    if not api_base:
        raise RuntimeError("OLLAMA_API_BASE (or OLLAMA_HOST) is not set.")

    api_url = f"{api_base}/chat/completions"
    payload = json.dumps(
        {
            "model": _ollama_model(),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a detailed cartoon story about: {prompt}"},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }
    ).encode("utf-8")

    request = Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "VoiceFrame"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
        raise RuntimeError(f"Ollama request failed (HTTP {e.code}): {details or e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Could not reach Ollama API at {api_url}: {e.reason}") from e

    data = _parse_json(body)
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Ollama returned empty message content.")

    return content


def _generate_via_groq(prompt: str) -> str:
    api_key = (os.environ.get("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    model = (os.environ.get("VOICEFRAME_GROQ_MODEL") or os.environ.get("GROQ_MODEL") or "llama-3.1-8b-instant").strip()
    api_url = "https://api.groq.com/openai/v1/chat/completions"

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Create a detailed cartoon story about: {prompt}"},
            ],
            "temperature": 0.3,
            "max_tokens": 2048,
        }
    ).encode("utf-8")

    request = Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "VoiceFrame",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        details = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
        raise RuntimeError(f"Groq request failed (HTTP {e.code}): {details or e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"Could not reach Groq API: {e.reason}") from e

    data = _parse_json(body)
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("Groq returned empty message content.")

    return content


def _parse_json(body: str) -> dict[str, Any]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {body[:500]}") from e

    if not isinstance(data, dict):
        raise RuntimeError("Invalid API response shape.")

    return data
