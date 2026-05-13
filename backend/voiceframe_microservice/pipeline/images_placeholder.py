from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _safe_slug(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "item"


def generate_placeholder_assets(base_dir: Path, scenes: list[dict]) -> None:
    chars_dir = base_dir / "outputs" / "character"
    bgs_dir = base_dir / "outputs" / "background"
    chars_dir.mkdir(parents=True, exist_ok=True)
    bgs_dir.mkdir(parents=True, exist_ok=True)

    _clear_dir(chars_dir)
    _clear_dir(bgs_dir)

    font = _load_font(28)
    small = _load_font(18)

    unique_chars: dict[str, dict] = {}
    for scene_obj in scenes:
        for ch in (scene_obj.get("scene") or {}).get("characters", []) or []:
            name = (ch.get("name") or "Unknown").strip()
            if name and name not in unique_chars:
                unique_chars[name] = ch

    for name, ch in unique_chars.items():
        img = Image.new("RGBA", (512, 512), (40, 40, 40, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([16, 16, 496, 496], outline=(255, 215, 0, 255), width=4)
        d.text((24, 24), name, font=font, fill=(255, 255, 255, 255))
        appearance = (ch.get("appearance") or "").strip()[:260]
        if appearance:
            d.text((24, 80), appearance, font=small, fill=(210, 210, 210, 255))
        out = chars_dir / f"char_{_safe_slug(name)}.png"
        img.save(out)

    for idx, scene_obj in enumerate(scenes):
        scene = scene_obj.get("scene") or {}
        bg = (scene.get("background") or {}).get("description") or ""
        img = Image.new("RGBA", (1280, 720), (15, 15, 25, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([20, 20, 1260, 700], outline=(0, 200, 255, 255), width=4)
        d.text((40, 40), f"Scene {idx + 1}", font=font, fill=(255, 255, 255, 255))
        if bg:
            d.text((40, 100), bg[:800], font=small, fill=(200, 200, 200, 255))
        out = bgs_dir / f"scene_{idx + 1}_bg.png"
        img.save(out)


def _clear_dir(p: Path) -> None:
    for child in p.iterdir():
        if child.is_file():
            try:
                child.unlink()
            except Exception:
                pass


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()
