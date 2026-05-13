from __future__ import annotations

import json
import os
import time
import urllib.parse
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen, urlretrieve


class ComfyClient:
    def __init__(self) -> None:
        self.server_address = (os.getenv("COMFYUI_URL") or "http://127.0.0.1:8188").rstrip("/")
        self.workflow_dir = Path(os.getenv("WORKFLOW_DIR") or "/workflows").resolve()
        self.char_workflow = os.getenv("CHAR_WORKFLOW") or "char_workflow.json"
        self.bg_workflow = os.getenv("BG_WORKFLOW") or "background_workflow.json"
        self.char_prompt_node_id = os.getenv("VOICEFRAME_CHAR_PROMPT_NODE_ID") or "1005"
        self.bg_prompt_node_id = os.getenv("VOICEFRAME_BG_PROMPT_NODE_ID") or "102"

    def load_workflow(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def queue_prompt(self, workflow: dict) -> str:
        payload = json.dumps({"prompt": workflow}).encode("utf-8")
        req = Request(
            f"{self.server_address}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=60) as res:
                data = json.loads(res.read().decode("utf-8", errors="replace"))
        except HTTPError as err:
            details = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ComfyUI rejected the prompt (HTTP {err.code}): {details}") from err

        prompt_id = (data.get("prompt_id") or "").strip()
        if not prompt_id:
            raise RuntimeError("ComfyUI did not return prompt_id")
        return prompt_id

    def wait_for_completion(self, prompt_id: str) -> dict:
        while True:
            with urlopen(f"{self.server_address}/history/{prompt_id}", timeout=60) as res:
                history = json.loads(res.read().decode("utf-8", errors="replace"))
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(1.0)

    def download_images(self, outputs: dict, save_dir: Path, file_prefix: str) -> None:
        save_dir.mkdir(parents=True, exist_ok=True)

        image_count = 0
        for node_output in outputs.values():
            if not isinstance(node_output, dict) or "images" not in node_output:
                continue
            for image in node_output.get("images") or []:
                filename = image.get("filename")
                if not filename:
                    continue

                subfolder = image.get("subfolder", "")
                folder_type = image.get("type", "output")

                params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
                url = f"{self.server_address}/view?{params}"

                ext = os.path.splitext(filename)[1] or ".png"
                new_filename = f"{file_prefix}_{image_count}{ext}" if image_count > 0 else f"{file_prefix}{ext}"
                out_path = save_dir / new_filename

                urlretrieve(url, out_path)
                image_count += 1

        if image_count == 0:
            raise RuntimeError("ComfyUI returned no images")

    def generate_character(self, prompt_text: str, save_dir: Path, file_prefix: str) -> None:
        workflow_path = self.workflow_dir / self.char_workflow
        if not workflow_path.exists():
            raise RuntimeError(f"Character workflow not found: {workflow_path}")

        workflow = self.load_workflow(workflow_path)
        node_id = self.char_prompt_node_id
        if node_id not in workflow:
            raise RuntimeError(f"Character prompt node id not in workflow: {node_id}")

        workflow[node_id]["inputs"]["value"] = (
            prompt_text
            + "\nStyle: high-detail comic illustration, bold ink outlines, rich colors, slight cel-shading, solid background"
        )

        prompt_id = self.queue_prompt(workflow)
        history_entry = self.wait_for_completion(prompt_id)
        outputs = history_entry.get("outputs", {})
        self.download_images(outputs, save_dir=save_dir, file_prefix=file_prefix)

    def generate_background(self, prompt_text: str, save_dir: Path, file_prefix: str) -> None:
        workflow_path = self.workflow_dir / self.bg_workflow
        if not workflow_path.exists():
            raise RuntimeError(f"Background workflow not found: {workflow_path}")

        workflow = self.load_workflow(workflow_path)
        node_id = self.bg_prompt_node_id
        if node_id not in workflow:
            raise RuntimeError(f"Background prompt node id not in workflow: {node_id}")

        workflow[node_id]["inputs"]["value"] = (
            prompt_text
            + "\nStyle: high-detail comic illustration, bold ink outlines, rich colors, slight cel-shading, dramatic atmosphere"
        )

        prompt_id = self.queue_prompt(workflow)
        history_entry = self.wait_for_completion(prompt_id)
        outputs = history_entry.get("outputs", {})
        self.download_images(outputs, save_dir=save_dir, file_prefix=file_prefix)


def generate_assets_comfyui(base_dir: Path, scenes: list[dict]) -> None:
    chars_dir = base_dir / "outputs" / "character"
    bgs_dir = base_dir / "outputs" / "background"
    chars_dir.mkdir(parents=True, exist_ok=True)
    bgs_dir.mkdir(parents=True, exist_ok=True)

    _clear_dir(chars_dir)
    _clear_dir(bgs_dir)

    client = ComfyClient()

    generated_characters: set[str] = set()
    for scene_idx, scene_obj in enumerate(scenes):
        scene = scene_obj.get("scene") or {}

        bg_desc = ((scene.get("background") or {}).get("description") or "").strip()
        if bg_desc:
            client.generate_background(bg_desc, save_dir=bgs_dir, file_prefix=f"scene_{scene_idx + 1}_bg")

        for ch in (scene.get("characters") or []) or []:
            name = (ch.get("name") or "").strip()
            appearance = (ch.get("appearance") or "").strip()
            gender = (ch.get("gender") or "unknown").strip()

            key = f"{name}::{appearance}"
            if not name or not appearance or key in generated_characters:
                continue

            prompt_text = f"one {name}, {appearance} ({gender})"
            safe_name = "".join([c if c.isalnum() else "_" for c in name]).strip("_") or "char"
            client.generate_character(prompt_text, save_dir=chars_dir, file_prefix=f"char_{safe_name}")
            generated_characters.add(key)


def _clear_dir(p: Path) -> None:
    for child in p.iterdir():
        if child.is_file():
            try:
                child.unlink()
            except Exception:
                pass
