"""
prosody_engine.py — Wraps original text with paralinguistic sound tags
and provides per-emotion sampling parameters for ChatterboxTurboTTS.

ChatterboxTurboTTS natively understands these non-verbal event tags:
  [clear throat]  [sigh]    [shush]   [cough]
  [groan]         [sniff]   [gasp]    [chuckle]   [laugh]

These tags produce SOUNDS, not words, so the spoken text is unchanged.

Emotion is controlled via:
  1. Paralinguistic tags     — non-verbal sounds, primary expressive signal
  2. Sampling parameters     — temperature, top_k, top_p, repetition_penalty
  3. Audio post-processing   — speed & volume (handled in audio_utils.py)
"""

# -----------------------------------------------------------------
# Per-emotion sampling profiles for ChatterboxTurboTTS.generate()
#   temperature       : 0.05–2.0  — energy / spontaneity of speech
#   top_k             : 1–1000    — lower = more focused / controlled
#   top_p             : 0.0–1.0   — nucleus sampling cutoff
#   repetition_penalty: 1.0–2.0   — rhythm variation penalty
# -----------------------------------------------------------------
EMOTION_PROFILES = {
    "happy":      {"temperature": 0.95, "top_k": 800, "top_p": 0.97, "repetition_penalty": 1.15},
    "excited":    {"temperature": 1.10, "top_k": 900, "top_p": 0.98, "repetition_penalty": 1.10},
    "sad":        {"temperature": 0.55, "top_k": 400, "top_p": 0.88, "repetition_penalty": 1.30},
    "tense":      {"temperature": 0.90, "top_k": 600, "top_p": 0.93, "repetition_penalty": 1.25},
    "angry":      {"temperature": 1.10, "top_k": 700, "top_p": 0.95, "repetition_penalty": 1.10},
    "calm":       {"temperature": 0.60, "top_k": 300, "top_p": 0.85, "repetition_penalty": 1.35},
    "reflective": {"temperature": 0.65, "top_k": 350, "top_p": 0.87, "repetition_penalty": 1.30},
    "surprised":  {"temperature": 1.00, "top_k": 750, "top_p": 0.96, "repetition_penalty": 1.15},
    "fearful":    {"temperature": 0.85, "top_k": 500, "top_p": 0.92, "repetition_penalty": 1.20},
    "neutral":    {"temperature": 0.80, "top_k": 600, "top_p": 0.95, "repetition_penalty": 1.20},
}

# Paralinguistic tags — NON-VERBAL sounds, placed where they feel most natural.
# prefix = sound BEFORE the sentence, suffix = sound AFTER the sentence.
EMOTION_TAGS = {
    "happy":      {"prefix": "[chuckle] ", "suffix": ""},
    "excited":    {"prefix": "[laugh] ",   "suffix": ""},
    "sad":        {"prefix": "[sniff] ",   "suffix": ""},
    "tense":      {"prefix": "",           "suffix": " [gasp]"},
    "angry":      {"prefix": "[groan] ",   "suffix": ""},
    "calm":       {"prefix": "",           "suffix": ""},
    "reflective": {"prefix": "[sigh] ",    "suffix": ""},
    "surprised":  {"prefix": "[gasp] ",    "suffix": ""},
    "fearful":    {"prefix": "[gasp] ",    "suffix": ""},
    "neutral":    {"prefix": "",           "suffix": ""},
}


def apply_prosody(text: str, emotion: str) -> str:
    """
    Wraps the ORIGINAL text with paralinguistic sound tags ONLY.

    The spoken words are NEVER modified — text content is preserved exactly.
    Tags like [sniff], [chuckle], [gasp] produce non-verbal vocal sounds
    that change the emotional DELIVERY without altering any words.

    IMPORTANT: Do NOT use '...' — punc_norm() inside ChatterboxTurboTTS
    converts '...' to ', ' which sounds wrong. Use commas for natural pauses.
    """
    emotion = emotion.lower().strip()
    tags    = EMOTION_TAGS.get(emotion, EMOTION_TAGS["neutral"])
    styled  = tags["prefix"] + text + tags["suffix"]
    return styled.strip()


def get_generation_params(emotion: str) -> dict:
    """
    Returns the TTS generation kwargs for ChatterboxTurboTTS.generate()
    corresponding to the requested emotion.
    """
    emotion = emotion.lower().strip()
    return dict(EMOTION_PROFILES.get(emotion, EMOTION_PROFILES["neutral"]))
