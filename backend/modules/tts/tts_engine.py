"""
tts_engine.py — Generates audio chunks from emotion-tagged segments.

Uses ChatterboxTurboTTS (already cached locally at HuggingFace cache dir).

Emotion is driven by three mechanisms the Turbo model ACTUALLY supports:
  1. Paralinguistic tags in text  [chuckle] [sigh] [gasp] [sniff] etc.
  2. Sampling parameters          temperature, top_k, top_p, repetition_penalty
  3. Audio post-processing        speed & volume shifts (audio_utils.py)

NOTE: Turbo does NOT support exaggeration / cfg_weight — those params
are silently ignored. We use the above mechanisms instead.
"""

import os
import sys
import torch
import torchaudio as ta
from django.conf import settings

from .prosody_engine import apply_prosody, get_generation_params

# ── Make sure the chatterbox package is importable ───────────────
# Add the chatterbox-emotion-tts directory to sys.path so we can
# import ChatterboxTurboTTS (it lives there, not in site-packages).
CHATTERBOX_DIR = getattr(
    settings,
    "CHATTERBOX_PACKAGE_DIR",
    r"C:\Users\prath\Downloads\chatterbox-emotion-tts",
)
if CHATTERBOX_DIR not in sys.path:
    sys.path.insert(0, CHATTERBOX_DIR)

from chatterbox.tts_turbo import ChatterboxTurboTTS   # noqa: E402

# ── Model singleton ──────────────────────────────────────────────
# Loaded ONCE at Django startup (AppConfig.ready → import this module).
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[EmotionTTS] Loading ChatterboxTurboTTS on {DEVICE}...")
model = ChatterboxTurboTTS.from_pretrained(device=DEVICE)
print("[EmotionTTS] Model ready.")

# ── Default voice reference ──────────────────────────────────────
# Must be ≥ 5 s of clean speech.  Configurable via settings.py.
DEFAULT_VOICE_PATH = getattr(
    settings,
    "TTS_DEFAULT_VOICE_PATH",
    os.path.join(settings.BASE_DIR, "voices", "baabu.wav"),
)

# ── Output dir ──────────────────────────────────────────────────
TTS_OUTPUT_DIR = getattr(
    settings,
    "TTS_OUTPUT_DIR",
    os.path.join(settings.BASE_DIR, "tts_output"),
)
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def generate_audio_chunks(
    segments: list,
    voice_path: str | None = None,
    session_id: str = "default",
) -> list:
    """
    For each segment dict {"text": ..., "emotion": ...}:
      1. Inject paralinguistic tags into the text
      2. Fetch emotion-specific sampling parameters
      3. Call model.generate() with those parameters
      4. Save the chunk wav and return the list of file paths.

    Args:
        segments  : list of {"text": str, "emotion": str}
        voice_path: path to reference voice WAV (overrides default)
        session_id: unique id to namespace chunk files per request

    Returns:
        list of absolute paths to per-chunk WAV files
    """
    ref = voice_path if (voice_path and os.path.exists(voice_path)) else DEFAULT_VOICE_PATH
    files = []

    for i, seg in enumerate(segments):
        text    = seg["text"]
        emotion = seg.get("emotion", "neutral")

        # 1. Inject paralinguistic tags
        styled_text = apply_prosody(text, emotion)

        # 2. Emotion-calibrated sampling params
        gen_params = get_generation_params(emotion)

        print(f"\n[EmotionTTS Segment {i}] emotion={emotion!r}")
        print(f"  params : {gen_params}")
        print(f"  text   : {styled_text!r}")

        # 3. Generate
        wav = model.generate(
            styled_text,
            audio_prompt_path=ref,
            temperature=gen_params["temperature"],
            top_k=int(gen_params["top_k"]),
            top_p=gen_params["top_p"],
            repetition_penalty=gen_params["repetition_penalty"],
        )

        # 4. Save chunk
        filename = os.path.join(TTS_OUTPUT_DIR, f"chunk_{session_id}_{i}.wav")
        ta.save(filename, wav, model.sr)
        files.append(filename)

    return files
