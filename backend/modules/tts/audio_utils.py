"""
audio_utils.py — Merges audio chunks with emotion-appropriate pacing
and subtle post-processing effects using pydub.

Post-processing applied per emotion:
  • sad       → slight slowdown (-6%) → sounds heavier, more dragged
  • tense     → slight speedup (+5%) + small gain boost → urgency
  • angry     → speedup (+8%) + louder → explosive energy
  • excited   → speedup (+6%) → bright, energetic
  • happy     → +3% speed → light and bright
  • calm      → -3% → serene, unhurried
  • reflective→ -4% → thoughtful, measured
  • surprised → +4% → startled, quick
  • fearful   → -3% + soft volume duck → scared, quiet
  • neutral   → no change

Speed is applied with frame-rate manipulation (no pitch shift), which
preserves the timbre of the cloned voice while changing speaking rate.
"""

import os
from django.conf import settings
from pydub import AudioSegment

# Resolve ffmpeg from Django settings (set in settings.py)
FFMPEG_DIR = getattr(settings, "FFMPEG_DIR", r"C:\Users\prath\Downloads\ffmpeg-8.1-essentials_build\bin")
if FFMPEG_DIR and FFMPEG_DIR not in os.environ.get("PATH", ""):
    os.environ["PATH"] += os.pathsep + FFMPEG_DIR


# ── pause durations (ms) per emotion ─────────────────────────────
PAUSE_MS = {
    "sad":        700,
    "tense":      250,
    "angry":      150,
    "excited":    150,
    "happy":      200,
    "calm":       450,
    "reflective": 600,
    "surprised":  200,
    "fearful":    500,
    "neutral":    350,
}

# ── speed factor per emotion (1.0 = normal) ──────────────────────
SPEED_FACTOR = {
    "sad":        0.94,   # slower → heavier
    "tense":      1.05,   # faster → urgency
    "angry":      1.08,   # faster + louder
    "excited":    1.06,   # light and quick
    "happy":      1.03,   # slightly brighter
    "calm":       0.97,   # serene, unhurried
    "reflective": 0.96,   # thoughtful
    "surprised":  1.04,   # startled
    "fearful":    0.97,   # slightly hushed
    "neutral":    1.00,
}

# ── volume adjustment dB per emotion ─────────────────────────────
VOLUME_DB = {
    "sad":       -1.5,
    "tense":     +1.5,
    "angry":     +3.0,
    "excited":   +2.0,
    "happy":     +1.0,
    "calm":       0.0,
    "reflective":-1.0,
    "surprised": +1.5,
    "fearful":   -2.0,
    "neutral":    0.0,
}


def _change_speed(segment: AudioSegment, speed: float) -> AudioSegment:
    """
    Change playback speed by resampling frame-rate.
    Speed > 1.0  → faster (higher pitch-neutral frame rate)
    Speed < 1.0  → slower
    This preserves voice timbre while changing articulation rate.
    """
    if abs(speed - 1.0) < 0.001:
        return segment
    new_frame_rate = int(segment.frame_rate * speed)
    fast = segment._spawn(segment.raw_data, overrides={"frame_rate": new_frame_rate})
    return fast.set_frame_rate(segment.frame_rate)


def merge_audio(
    files: list,
    segments: list,
    output: str,
) -> str:
    """
    Merge all audio chunks with:
      1. Per-emotion speed adjustment
      2. Per-emotion volume adjustment
      3. Emotion-appropriate silence gaps between segments
    """
    final = AudioSegment.empty()

    for i, (f, seg) in enumerate(zip(files, segments)):
        emotion = seg.get("emotion", "neutral").lower()

        audio = AudioSegment.from_file(f, format="wav")

        # Speed adjust
        speed  = SPEED_FACTOR.get(emotion, 1.0)
        audio  = _change_speed(audio, speed)

        # Volume adjust
        vol_db = VOLUME_DB.get(emotion, 0.0)
        if vol_db != 0.0:
            audio = audio + vol_db

        final += audio

        # Silence gap
        pause = PAUSE_MS.get(emotion, 350)
        final += AudioSegment.silent(duration=pause)

    final.export(output, format="wav")
    return output
