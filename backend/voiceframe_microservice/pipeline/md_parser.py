from __future__ import annotations

import re


def parse_story_md(md_content: str) -> list:
    md_content = md_content.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    md_content = md_content.replace('–', '-').replace('—', '-').replace('…', '...')
    md_content = md_content.encode('ascii', 'ignore').decode('ascii')

    scenes: list[dict] = []

    scene_blocks = re.split(r"# Scene \d+", md_content)

    for block in scene_blocks:
        if not block.strip():
            continue

        scene_data = {"background": {}, "characters": [], "dialogues": []}

        bg_match = re.search(
            r"## Background\n+(.+?)\s*\(?\s*[\[(](?:Start\s+)?(\d{2}:\d{2}:\d{2})[\])]\s*(?:to|-|-)\s*[\[(](?:End\s+)?(\d{2}:\d{2}:\d{2})[\])]\s*\)?",
            block,
            re.DOTALL,
        )
        if bg_match:
            scene_data["background"] = {
                "description": bg_match.group(1).strip(),
                "start": bg_match.group(2).strip(),
                "end": bg_match.group(3).strip(),
            }

        char_gender_map: dict[str, str] = {}
        char_section_match = re.search(r"## Characters\n+(.+?)(?=## Dialogues|$)", block, re.DOTALL)
        if char_section_match:
            char_lines = char_section_match.group(1).strip().split("\n")
            for line in char_lines:
                char_match = re.match(r"\*\s+(.+?):\s+(.+?)\((Male|Female)\)", line.strip(), re.IGNORECASE)
                if char_match:
                    name = char_match.group(1).strip()
                    gender = char_match.group(3).strip().lower()
                    scene_data["characters"].append(
                        {
                            "name": name,
                            "appearance": char_match.group(2).strip(),
                            "gender": gender,
                        }
                    )
                    char_gender_map[name.lower()] = gender

        dialogue_section_match = re.search(r"## Dialogues\n+(.+)$", block, re.DOTALL)
        if dialogue_section_match:
            dialogue_lines = dialogue_section_match.group(1).strip().split("\n")
            for line in dialogue_lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("*GAP*"):
                    gap_match = re.search(r"\*GAP\*\s*\((\d+)\)", line)
                    if gap_match:
                        scene_data["dialogues"].append({"type": "gap", "duration": int(gap_match.group(1))})
                    continue

                diag_match = re.match(r"(.+?)\s*(?:\((.+?)\))?:\s+(.+)", line)
                if not diag_match:
                    continue

                char_name = diag_match.group(1).strip()
                emotion = diag_match.group(2).strip().lower() if diag_match.group(2) else "neutral"
                line_text = diag_match.group(3).strip()

                inner_emotion_match = re.match(r"\((.+?)\)\s*(.+)", line_text)
                if inner_emotion_match:
                    emotion = inner_emotion_match.group(1).strip().lower()
                    line_text = inner_emotion_match.group(2).strip()

                gender = char_gender_map.get(char_name.lower(), "male")

                scene_data["dialogues"].append(
                    {
                        "type": "dialogue",
                        "character": char_name,
                        "emotion": emotion,
                        "gender": gender,
                        "line": line_text,
                        "start": "00:00:00",
                        "end": "00:00:00",
                    }
                )

        if scene_data["background"].get("start"):
            bg_start_sec = parse_time_to_seconds(scene_data["background"]["start"])
            current_time = bg_start_sec

            calculated_dialogues = []
            for d in scene_data["dialogues"]:
                if d.get("type") == "gap":
                    current_time += float(d.get("duration") or 0)
                    continue

                words = len((d.get("line") or "").split())
                duration = max(3.0, words / 2.5)
                d["start"] = seconds_to_time(current_time)
                current_time += duration
                d["end"] = seconds_to_time(current_time)
                calculated_dialogues.append(d)

            scene_data["dialogues"] = calculated_dialogues

        scenes.append({"scene": scene_data})

    return scenes


def parse_time_to_seconds(time_str: str) -> float:
    parts = time_str.strip().split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0


def seconds_to_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
