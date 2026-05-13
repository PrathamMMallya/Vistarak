from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def tts_enabled() -> bool:
    return bool((os.environ.get("VOICEFRAME_TTS_BASE_URL") or "").strip())


def synthesize_dialogues_http(out_dir: Path, dialogues: list[dict]) -> None:
    base = (os.environ.get("VOICEFRAME_TTS_BASE_URL") or "").strip().rstrip("/")
    if not base:
        return

    endpoint = (os.environ.get("VOICEFRAME_TTS_ENDPOINT") or "/tts").strip()
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint

    url = f"{base}{endpoint}"
    out_dir.mkdir(parents=True, exist_ok=True)

    idx = 1
    for d in dialogues:
        if d.get("type") == "gap":
            continue

        line = (d.get("line") or "").strip()
        if not line:
            continue

        payload = json.dumps(
            {
                "dialogue": line,
                "emotion": (d.get("emotion") or "neutral"),
                "gender": (d.get("gender") or "female"),
                "language": (os.environ.get("VOICEFRAME_TTS_LANGUAGE") or "English"),
            }
        ).encode("utf-8")

        req = Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "VoiceFrame"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=300) as resp:
                content_type = (resp.headers.get("Content-Type") or "").lower()
                body = resp.read()
        except HTTPError as e:
            details = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
            raise RuntimeError(f"TTS request failed (HTTP {e.code}): {details or e.reason}") from e
        except URLError as e:
            raise RuntimeError(f"Could not reach TTS API at {url}: {e.reason}") from e

        if "application/json" in content_type:
            try:
                data = json.loads(body.decode("utf-8", errors="replace"))
            except Exception:
                data = {}
            err = (data.get("error") or data.get("detail") or "").strip()
            if err:
                raise RuntimeError(f"TTS error: {err}")

        wav_path = out_dir / f"{idx}.wav"
        wav_path.write_bytes(body)
        idx += 1
