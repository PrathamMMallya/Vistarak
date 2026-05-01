"""
groq_client.py — Splits original text into sentence segments and asks
Groq LLM to assign an emotion label to each one.

The LLM is NEVER allowed to rewrite, rephrase, or modify the text.
It only returns an emotion label per sentence.
"""

import os
import re
import json
import requests
from django.conf import settings

GROQ_API_KEY = getattr(settings, "GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
GROQ_MODEL   = "llama-3.1-8b-instant"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

VALID_EMOTIONS = {
    "happy", "excited", "sad", "tense", "angry",
    "calm", "reflective", "surprised", "fearful", "neutral"
}


def split_sentences(text: str) -> list:
    """
    Splits text into sentence-level chunks.
    Handles '.', '!', '?' as sentence boundaries.
    Filters out empty results.
    """
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


def label_emotions(sentences: list) -> dict:
    """
    Sends the original sentences to Groq and asks it to assign
    one emotion label per sentence — NO rewriting allowed.
    Returns a dict {sentence_index (1-based): emotion_str}.
    """
    numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))

    system_prompt = (
        "You are an emotion classifier for text-to-speech.\n"
        "You will receive a numbered list of sentences.\n"
        "For each sentence, assign exactly ONE emotion from this list:\n"
        "happy, excited, sad, tense, angry, calm, reflective, surprised, fearful, neutral\n\n"
        "Rules:\n"
        "- Return ONLY a valid JSON array. No markdown, no explanation.\n"
        "- Each element must have exactly two keys:\n"
        '  "index"   : the sentence number (integer, 1-based)\n'
        '  "emotion" : one emotion from the list above (string)\n'
        "- Do NOT include the sentence text in your response.\n"
        "- Do NOT rewrite or modify any sentence.\n\n"
        "Example output for 3 sentences:\n"
        '[{"index":1,"emotion":"sad"},{"index":2,"emotion":"reflective"},{"index":3,"emotion":"calm"}]'
    )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":    GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Label these sentences:\n{numbered}"},
        ],
        "temperature": 0.3,
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        res_json = response.json()

        if "choices" not in res_json:
            print("Groq API error:", res_json)
            return None

        content = res_json["choices"][0]["message"]["content"].strip()

        # Strip accidental markdown fences
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        labels = json.loads(content)

        emotion_map = {}
        for item in labels:
            idx     = int(item.get("index", 0))
            emotion = str(item.get("emotion", "neutral")).lower().strip()
            if emotion not in VALID_EMOTIONS:
                emotion = "neutral"
            emotion_map[idx] = emotion

        return emotion_map

    except Exception as e:
        print(f"Groq labelling error: {e}")
        return None


def get_expressive_segments(user_input: str) -> list:
    """
    Returns a list of {"text": <original sentence>, "emotion": <label>}.

    The original text is NEVER modified — words, punctuation, and order
    are preserved exactly. Only the emotion label is added.
    """
    sentences = split_sentences(user_input)

    if not sentences:
        return [{"text": user_input, "emotion": "neutral"}]

    emotion_map = label_emotions(sentences)

    segments = []
    for i, sentence in enumerate(sentences):
        emotion = "neutral"
        if emotion_map:
            emotion = emotion_map.get(i + 1, "neutral")
        segments.append({"text": sentence, "emotion": emotion})

    print("\n[Groq Segments]")
    for seg in segments:
        print(f"  [{seg['emotion']:>10}]  {seg['text']}")

    return segments
