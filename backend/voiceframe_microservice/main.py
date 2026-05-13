from __future__ import annotations

import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

JobState = Literal["queued", "running", "complete", "failed"]


class GenerateRequest(BaseModel):
    prompt: str = Field(default="", min_length=1)


MEDIA_ROOT = Path(os.environ.get("VOICEFRAME_MEDIA_ROOT", "/shared_media")).resolve()
STATE_DIR = Path(os.environ.get("VOICEFRAME_STATE_DIR", "/app/state")).resolve()
WORK_DIR = Path(os.environ.get("VOICEFRAME_WORK_DIR", "/app/work")).resolve()
STATE_FILE = STATE_DIR / "voiceframe_jobs.json"

_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}

app = FastAPI(title="VoiceFrame Microservice", version="0.1.0")


def _copy_to_media(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    tmp.write_bytes(src.read_bytes())
    tmp.replace(dst)


def _ensure_dirs() -> None:
    (MEDIA_ROOT / "voiceframe").mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)


def _load_state() -> None:
    if not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            _JOBS.clear()
            for key, value in data.items():
                if isinstance(key, str) and isinstance(value, dict):
                    _JOBS[key] = value
    except Exception:
        _JOBS.clear()


def _save_state() -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_JOBS, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


def _job_dir(job_id: str) -> Path:
    return WORK_DIR / "jobs" / job_id


def _media_video_path(job_id: str) -> Path:
    return MEDIA_ROOT / "voiceframe" / f"{job_id}.mp4"


def _set_job(job_id: str, **updates: Any) -> None:
    with _LOCK:
        job = _JOBS.get(job_id) or {}
        job.update(updates)
        _JOBS[job_id] = job
        _save_state()


def _get_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        job = _JOBS.get(job_id)
        return dict(job) if isinstance(job, dict) else None


def _run_job(job_id: str, prompt: str) -> None:
    started = time.time()
    job_work = _job_dir(job_id)
    job_work.mkdir(parents=True, exist_ok=True)

    try:
        _set_job(job_id, status="running", progress=1, stage="starting", started_at=started)

        from voiceframe_microservice.pipeline.runner import run_pipeline

        def progress_cb(pct: int, stage: str) -> None:
            safe_pct = max(0, min(99, int(pct)))
            _set_job(job_id, progress=safe_pct, stage=stage)

        out_tmp = run_pipeline(prompt=prompt, work_dir=job_work, progress_cb=progress_cb)
        out_path = _media_video_path(job_id)
        _copy_to_media(out_tmp, out_path)

        _set_job(
            job_id,
            status="complete",
            progress=100,
            stage="complete",
            finished_at=time.time(),
            video_url=f"/media/voiceframe/{job_id}.mp4",
        )
    except Exception as exc:
        _set_job(
            job_id,
            status="failed",
            progress=100,
            stage="failed",
            finished_at=time.time(),
            error=str(exc),
        )


@app.on_event("startup")
def _startup() -> None:
    _ensure_dirs()
    _load_state()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "jobs": len(_JOBS),
        "media_root": str(MEDIA_ROOT),
    }


@app.post("/generate")
def generate(req: GenerateRequest) -> JSONResponse:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    job_id = uuid.uuid4().hex
    _set_job(job_id, status="queued", progress=0, prompt=prompt, created_at=time.time())

    t = threading.Thread(target=_run_job, args=(job_id, prompt), daemon=True)
    t.start()

    return JSONResponse({"status": "success", "job_id": job_id})


@app.get("/status/{job_id}")
def status(job_id: str) -> JSONResponse:
    job = _get_job(job_id)
    if not job:
        return JSONResponse({"status": "failed", "error": "job not found"}, status_code=404)

    # keep response stable for Django/frontend
    return JSONResponse(
        {
            "status": job.get("status"),
            "progress": job.get("progress", 0),
            "stage": job.get("stage"),
            "error": job.get("error"),
            "video_url": job.get("video_url"),
        }
    )


@app.get("/result/{job_id}")
def result(job_id: str) -> JSONResponse:
    job = _get_job(job_id)
    if not job:
        return JSONResponse({"status": "failed", "error": "job not found"}, status_code=404)

    if job.get("status") != "complete":
        return JSONResponse({"status": job.get("status"), "error": job.get("error")}, status_code=409)

    return JSONResponse({"status": "success", "video_url": job.get("video_url")})
