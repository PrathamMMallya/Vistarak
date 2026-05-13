"""Video generator adapted from VoiceFrame."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from moviepy import AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip
from moviepy import vfx


class ImprovedTextRenderer:
    def __init__(self, font_size: int = 20, font_color: str = "gold"):
        self.font_size = font_size
        self.font_color = font_color
        self.font_path = self._get_font_path()

    def _get_font_path(self) -> Optional[str]:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None

    def _get_text_dimensions(self, text: str, font) -> Tuple[int, int]:
        try:
            bbox = font.getbbox(text)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return width, height
        except AttributeError:
            width, height = font.getsize(text)
            return width, height

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        full_text_width, _ = self._get_text_dimensions(text, font)
        if full_text_width <= max_width:
            return [text]

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = (current_line + " " + word) if current_line else word
            text_width, _ = self._get_text_dimensions(test_line, font)
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def create_speech_bubble(
        self,
        text: str,
        max_width: int,
        bg_color: tuple = (0, 0, 0, 220),
        border_color: tuple = (218, 165, 32, 255),
        padding: int = 15,
        corner_radius: int = 15,
        add_tail: bool = True,
        tail_side: str = "left",
    ) -> Image.Image:
        try:
            if self.font_path:
                font = ImageFont.truetype(self.font_path, self.font_size)
            else:
                font = ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        content_width = max_width - (2 * padding)
        lines = self._wrap_text(text, font, content_width)

        line_height = self.font_size + 4
        text_height = len(lines) * line_height

        actual_text_width = 0
        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            actual_text_width = max(actual_text_width, line_width)

        min_bubble_width = 150
        bubble_width = max(actual_text_width + (2 * padding), min_bubble_width)
        bubble_height = text_height + (2 * padding)

        tail_height = 20
        tail_width = 15

        if add_tail:
            img_width = bubble_width + tail_width
            img_height = bubble_height + tail_height
        else:
            img_width = bubble_width
            img_height = bubble_height

        img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if add_tail and tail_side == "right":
            bubble_x = 0
        else:
            bubble_x = tail_width if add_tail else 0
        bubble_y = 0

        self._draw_rounded_rectangle(
            draw,
            [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height],
            corner_radius,
            fill=bg_color,
            outline=border_color,
            width=2,
        )

        if add_tail:
            self._draw_speech_tail(draw, bubble_x, bubble_y, bubble_width, bubble_height, tail_side, bg_color, border_color)

        text_color = self._parse_color(self.font_color)
        y_offset = bubble_y + padding

        for line in lines:
            line_width, _ = self._get_text_dimensions(line, font)
            x_offset = bubble_x + padding + (actual_text_width - line_width) // 2
            draw.text((x_offset, y_offset), line, font=font, fill=text_color)
            y_offset += line_height

        return img

    def _draw_rounded_rectangle(self, draw, coords, radius, fill=None, outline=None, width=1):
        x1, y1, x2, y2 = coords
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        draw.pieslice([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=fill)
        draw.pieslice([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=fill)

        if outline:
            draw.rectangle([x1 + radius, y1, x2 - radius, y1 + width], fill=outline)
            draw.rectangle([x1 + radius, y2 - width, x2 - radius, y2], fill=outline)
            draw.rectangle([x1, y1 + radius, x1 + width, y2 - radius], fill=outline)
            draw.rectangle([x2 - width, y1 + radius, x2, y2 - radius], fill=outline)

            draw.arc([x1, y1, x1 + 2 * radius, y1 + 2 * radius], 180, 270, fill=outline, width=width)
            draw.arc([x2 - 2 * radius, y1, x2, y1 + 2 * radius], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2 - 2 * radius, x1 + 2 * radius, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2 - 2 * radius, y2 - 2 * radius, x2, y2], 0, 90, fill=outline, width=width)

    def _draw_speech_tail(self, draw, bubble_x, bubble_y, bubble_width, bubble_height, tail_side, bg_color, border_color):
        tail_height = 20
        tail_width = 15

        if tail_side == "left":
            tail_points = [
                (bubble_x, bubble_y + bubble_height - 30),
                (bubble_x - tail_width, bubble_y + bubble_height - 10),
                (bubble_x, bubble_y + bubble_height - 10),
            ]
        else:
            tail_points = [
                (bubble_x + bubble_width, bubble_y + bubble_height - 30),
                (bubble_x + bubble_width + tail_width, bubble_y + bubble_height - 10),
                (bubble_x + bubble_width, bubble_y + bubble_height - 10),
            ]

        draw.polygon(tail_points, fill=bg_color)
        for i in range(len(tail_points)):
            start = tail_points[i]
            end = tail_points[(i + 1) % len(tail_points)]
            draw.line([start, end], fill=border_color, width=2)

    def _parse_color(self, color_str: str) -> tuple:
        color_map = {
            "gold": (255, 215, 0, 255),
            "white": (255, 255, 255, 255),
            "black": (0, 0, 0, 255),
        }
        return color_map.get((color_str or "").lower(), (255, 215, 0, 255))


SPEECH_BUBBLE_CONFIGS = {
    "modern_bubbles": {
        "font_size": 20,
        "font_color": "gold",
        "character_positions": {},
    }
}


class VoiceFrameVideoGenerator:
    def __init__(self, base_dir: str):
        res_str = os.getenv("VIDEO_RESOLUTION", "1280x720")
        try:
            self.target_width, self.target_height = map(int, res_str.split("x"))
        except Exception:
            self.target_width, self.target_height = 1280, 720

        self.video_codec = os.getenv("VIDEO_CODEC", "libx264")
        self.video_threads = int(os.getenv("VIDEO_THREADS", "4"))
        self.video_preset = os.getenv("VIDEO_PRESET", "medium")

        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "images"
        self.audio_dir = self.base_dir / "voices"
        self.output_path = self.base_dir / "video.mp4"

    @staticmethod
    def convert_time_to_seconds(time_str: str) -> float:
        parts = [p.strip() for p in (time_str or "").strip().split(":")]
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
            return h * 3600 + m * 60 + s
        if len(parts) == 2:
            m, s = int(parts[0]), float(parts[1])
            return m * 60 + s
        if len(parts) == 1 and parts[0]:
            return float(parts[0])
        return 0.0

    def seconds_to_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 100)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:02d}"

    def recalculate_timestamps(self, scenes: List[Dict], audio_dir: str) -> List[Dict]:
        current_time = 0.0
        dialogue_idx = 1
        padding = 0.2

        for scene_obj in scenes:
            scene_info = scene_obj.get("scene", {})
            background_info = scene_info.get("background", {})
            dialogues = scene_info.get("dialogues", [])

            scene_start_time = current_time

            for dialogue in dialogues:
                audio_file = os.path.join(audio_dir, f"{dialogue_idx}.wav")

                if os.path.exists(audio_file):
                    audio_clip = AudioFileClip(audio_file)
                    duration = audio_clip.duration
                    audio_clip.close()

                    dialogue["start"] = self.seconds_to_time(current_time)
                    current_time += duration
                    dialogue["end"] = self.seconds_to_time(current_time)
                    current_time += padding
                else:
                    dialogue["start"] = self.seconds_to_time(current_time)
                    current_time += 2.0
                    dialogue["end"] = self.seconds_to_time(current_time)
                    current_time += padding

                dialogue_idx += 1

            background_info["start"] = self.seconds_to_time(scene_start_time)
            background_info["end"] = self.seconds_to_time(current_time)

        return scenes

    def get_character_image_by_name(self, name: str, index: int = 0) -> Optional[str]:
        chars_dir = self.base_dir / "outputs" / "character"
        if not chars_dir.exists():
            return None

        name_lower = (name or "").lower()
        image_files = sorted([f for f in os.listdir(chars_dir) if f.endswith((".png", ".jpeg", ".jpg"))])

        named_files = [f for f in image_files if name_lower and name_lower in f.lower()]
        if named_files:
            named_files.sort(key=len)
            return str(chars_dir / named_files[0])

        if len(image_files) > index:
            return str(chars_dir / image_files[index])
        if image_files:
            return str(chars_dir / image_files[0])

        return None

    def get_background_image(self, scene_index: int = 0) -> Optional[str]:
        bg_dir = self.base_dir / "outputs" / "background"
        search_dir = bg_dir if bg_dir.exists() else self.images_dir

        if not search_dir.exists():
            return None

        prefix = f"scene_{scene_index + 1}_bg"
        image_files = sorted([f for f in os.listdir(search_dir) if f.startswith(prefix) and f.endswith((".jpeg", ".jpg", ".png"))])
        if image_files:
            return str(search_dir / image_files[0])

        all_images = sorted([f for f in os.listdir(search_dir) if f.endswith((".jpeg", ".jpg", ".png"))])
        if len(all_images) > scene_index:
            return str(search_dir / all_images[scene_index])
        if all_images:
            return str(search_dir / all_images[0])

        return None

    def get_audio_files(self) -> List[str]:
        if not self.audio_dir.exists():
            return []

        audio_files = sorted(
            [f for f in os.listdir(self.audio_dir) if f.endswith((".wav", ".mp3", ".m4a"))],
            key=lambda x: int(x.split(".")[0]) if x.split(".")[0].isdigit() else 0,
        )
        return [str(self.audio_dir / f) for f in audio_files]

    def generate_video_with_dialogues(
        self,
        scenes: List[Dict],
        character_positions: Optional[Dict] = None,
        font_size: int = 32,
        font_color: str = "gold",
    ) -> bool:
        try:
            if not scenes:
                return False

            all_video_clips = []

            first_bg = self.get_background_image(0)
            if not first_bg:
                return False

            W, H = self.target_width, self.target_height

            total_duration = 0.0
            for scene_obj in scenes:
                bg_info = (scene_obj.get("scene", {}) or {}).get("background", {}) or {}
                scene_end = self.convert_time_to_seconds(bg_info.get("end", "00:00:00"))
                total_duration = max(total_duration, scene_end)

            temp_text_files = []

            for scene_idx, scene_obj in enumerate(scenes):
                scene_info = scene_obj.get("scene", {})
                bg_info = scene_info.get("background", {})
                scene_start = self.convert_time_to_seconds(bg_info.get("start", "00:00:00"))
                scene_end = self.convert_time_to_seconds(bg_info.get("end", "00:00:10"))
                scene_duration = scene_end - scene_start
                if scene_duration <= 0:
                    continue

                bg_path = self.get_background_image(scene_idx) or first_bg
                bg_clip = ImageClip(bg_path).with_start(scene_start).with_duration(scene_duration).resized((W, H))
                all_video_clips.append(bg_clip)

                scene_characters = scene_info.get("characters", [])
                num_chars = len(scene_characters)

                for i, char_data in enumerate(scene_characters):
                    char_name = char_data.get("name", "")
                    char_file = self.get_character_image_by_name(char_name, index=i)
                    if not char_file:
                        continue

                    char_clip = ImageClip(char_file).with_start(scene_start).with_duration(scene_duration)
                    if num_chars == 1:
                        pos = ("center", "bottom")
                    elif num_chars == 2:
                        pos = ("left", "bottom") if i == 0 else ("right", "bottom")
                    else:
                        if i == 0:
                            pos = ("left", "bottom")
                        elif i == 1:
                            pos = ("right", "bottom")
                        else:
                            pos = ("center", "bottom")

                    if char_clip.h > H * 0.8:
                        char_clip = char_clip.resized(height=int(H * 0.8))
                    char_clip = char_clip.with_position(pos)
                    all_video_clips.append(char_clip)

                dialogues = scene_info.get("dialogues", [])
                for i, dialogue in enumerate(dialogues):
                    d_start = self.convert_time_to_seconds(dialogue.get("start", "00:00:00"))
                    d_end = self.convert_time_to_seconds(dialogue.get("end", "00:00:00"))
                    d_duration = d_end - d_start
                    if d_duration <= 0:
                        continue

                    char_name = dialogue.get("character", "Unknown")
                    line_text = dialogue.get("line", "")
                    text_content = f"{char_name}: {line_text}"

                    char_config = (character_positions or {}).get(char_name, {"side": "left", "max_width": 450, "tail_side": "left"})
                    side = char_config.get("side", "left")
                    max_width = int(char_config.get("max_width", 450))
                    tail_side = char_config.get("tail_side", "left")

                    text_renderer = ImprovedTextRenderer(font_size, font_color)
                    text_img = text_renderer.create_speech_bubble(text=text_content, max_width=max_width, add_tail=True, tail_side=tail_side)

                    temp_name = f"temp_text_s{scene_idx}_d{i}.png"
                    temp_path = self.base_dir / temp_name
                    text_img.save(temp_path)
                    temp_text_files.append(temp_path)

                    margin = 40
                    bottom_margin = 120

                    if side == "left":
                        text_x = margin
                    elif side == "right":
                        text_x = W - margin - text_img.width
                    else:
                        text_x = (W - text_img.width) // 2

                    text_y = H - bottom_margin - text_img.height

                    fade_duration = min(0.2, d_duration / 6.0)
                    text_clip = ImageClip(str(temp_path)).with_start(d_start).with_duration(d_duration).with_position((text_x, text_y))
                    if fade_duration > 0:
                        text_clip = text_clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])
                    all_video_clips.append(text_clip)

            audio_files = self.get_audio_files()
            all_dialogues = []
            for scene_obj in scenes:
                all_dialogues.extend((scene_obj.get("scene", {}) or {}).get("dialogues", []) or [])

            if audio_files and len(audio_files) >= len(all_dialogues):
                synchronized_audio_clips = []
                for i, dialogue in enumerate(all_dialogues):
                    start_sec = self.convert_time_to_seconds(dialogue.get("start", "00:00:00"))
                    audio_file = audio_files[i]
                    audio_clip = AudioFileClip(audio_file).with_start(start_sec)
                    synchronized_audio_clips.append(audio_clip)

                combined_audio = CompositeAudioClip(synchronized_audio_clips)
                final_clip = CompositeVideoClip(all_video_clips, size=(W, H)).with_audio(combined_audio).with_duration(total_duration)
            else:
                final_clip = CompositeVideoClip(all_video_clips, size=(W, H)).with_duration(total_duration)

            final_clip.write_videofile(
                str(self.output_path),
                fps=24,
                codec=self.video_codec,
                threads=self.video_threads,
                preset=self.video_preset,
                audio_codec="aac" if audio_files else None,
            )

            final_clip.close()
            for clip in all_video_clips:
                try:
                    clip.close()
                except Exception:
                    pass

            for temp_file in temp_text_files:
                try:
                    temp_file.unlink()
                except Exception:
                    pass

            return True

        except Exception:
            return False


def generate_video_from_scene_data(
    base_dir: str,
    scenes: List[Dict],
    character_positions: Optional[Dict] = None,
) -> bool:
    generator = VoiceFrameVideoGenerator(base_dir)
    return generator.generate_video_with_dialogues(scenes, character_positions)
