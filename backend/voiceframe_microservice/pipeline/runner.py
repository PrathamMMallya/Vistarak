from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .images_comfyui import generate_assets_comfyui
from .images_placeholder import generate_placeholder_assets
from .md_parser import parse_story_md
from .story_llm import generate_story_markdown
from .tts_http import synthesize_dialogues_http, tts_enabled
from .video_gen import VoiceFrameVideoGenerator, generate_video_from_scene_data


def run_pipeline(
    *,
    prompt: str,
    work_dir: Path,
    progress_cb: Callable[[int, str], None],
) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)

    progress_cb(10, "Generating story")
    md = generate_story_markdown(prompt)
    (work_dir / "story.md").write_text(md, encoding="utf-8")

    progress_cb(20, "Parsing story")
    scenes = parse_story_md(md)
    if not scenes:
        raise RuntimeError("Failed to parse story markdown")

    progress_cb(35, "Generating images")
    image_provider = (os.environ.get("VOICEFRAME_IMAGE_PROVIDER") or "placeholder").strip().lower()
    if image_provider == "comfyui":
        generate_assets_comfyui(work_dir, scenes)
    else:
        generate_placeholder_assets(work_dir, scenes)

    all_dialogues: list[dict] = []
    for scene_obj in scenes:
        all_dialogues.extend((scene_obj.get("scene") or {}).get("dialogues", []) or [])

    voices_dir = work_dir / "voices"
    if tts_enabled() and all_dialogues:
        progress_cb(55, "Synthesizing voices")
        synthesize_dialogues_http(voices_dir, all_dialogues)

        progress_cb(65, "Aligning timings")
        gen = VoiceFrameVideoGenerator(str(work_dir))
        scenes = gen.recalculate_timestamps(scenes, str(voices_dir))

    progress_cb(80, "Compositing video")

    unique_characters = {}
    for scene_obj in scenes:
        for ch in (scene_obj.get("scene") or {}).get("characters", []) or []:
            if ch.get("name") and ch.get("name") not in unique_characters:
                unique_characters[ch.get("name")] = ch

    character_positions = {}
    sides = ["left", "right"]
    for i, name in enumerate(unique_characters.keys()):
        side = sides[i % len(sides)]
        character_positions[name] = {"side": side, "max_width": 450, "tail_side": side}

    ok = generate_video_from_scene_data(str(work_dir), scenes, character_positions)
    if not ok:
        raise RuntimeError("Video generation failed")

    out = work_dir / "video.mp4"
    if not out.exists():
        raise RuntimeError("Video file not found after generation")

    progress_cb(95, "Finalizing")
    return out
