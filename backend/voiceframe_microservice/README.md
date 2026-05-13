# VoiceFrame Microservice (Animated Story)

This service generates an animated story video (MP4) from a text prompt.

It is designed to run as a microservice and write the final MP4 into the shared Vistarak media volume under:

- `backend/media/voiceframe/<job_id>.mp4`

The Vistarak Django backend proxies this service under `/voiceframe/*` and the frontend previews the final MP4 from `/media/voiceframe/<job_id>.mp4`.

## Quick Start (Docker Compose)

From the Vistarak repo root:

1. Build + run the service:

   - `docker compose -f docker-compose.voiceframe.yml up --build`

2. Verify health:

   - `curl http://127.0.0.1:8020/health`

3. Create a job:

   - `curl -X POST http://127.0.0.1:8020/generate -H "Content-Type: application/json" -d "{\"prompt\":\"A short moral story about honesty\"}"`

4. Poll status until `status=complete`:

   - `curl http://127.0.0.1:8020/status/<job_id>`

5. The video will be written to:

   - `backend/media/voiceframe/<job_id>.mp4`

## Endpoints

- `GET /health` -> service status
- `POST /generate` -> starts a job
  - Body: `{ "prompt": "..." }`
  - Response: `{ "status": "success", "job_id": "..." }`
- `GET /status/{job_id}` -> job state
  - Response fields:
    - `status`: `queued | running | complete | failed`
    - `progress`: 0-100
    - `stage`: optional human-readable stage
    - `video_url`: `/media/voiceframe/<job_id>.mp4` when complete
    - `error`: string when failed
- `GET /result/{job_id}` -> returns `video_url` if complete, otherwise 409

## Pipeline Overview

Each job runs:

1. Story generation -> LLM (Ollama/Groq) or a built-in fallback story
2. Markdown parsing -> converts story markdown into scene data
3. Image generation
   - Placeholder images (default)
   - OR ComfyUI (if enabled)
4. Optional TTS -> generates WAV files for dialogues and re-aligns timestamps
5. Video compositing -> MoviePy builds `video.mp4`

## Environment Variables

### Core paths (already set in docker-compose.voiceframe.yml)

- `VOICEFRAME_MEDIA_ROOT` (default: `/shared_media`)
- `VOICEFRAME_STATE_DIR` (default: `/app/state`)
- `VOICEFRAME_WORK_DIR` (default: `/app/work`)

### Story generation (LLM)

If no LLM is configured, the service uses a simple built-in fallback story by default.

- `VOICEFRAME_LLM_PROVIDER`
  - `ollama` or `groq`
- `VOICEFRAME_ALLOW_FALLBACK_STORY`
  - `1` (default) to allow fallback story when no LLM is configured
  - `0` to hard-fail if no LLM provider is configured

**Ollama**

- `OLLAMA_API_BASE` (or `OLLAMA_HOST`)
  - Example (Ollama on host): `http://host.docker.internal:11434`
- `VOICEFRAME_OLLAMA_MODEL` (or `OLLAMA_MODEL`)
  - Default: `llama3.1:8b`

**Groq**

- `GROQ_API_KEY`
- `VOICEFRAME_GROQ_MODEL` (or `GROQ_MODEL`)
  - Default: `llama-3.1-8b-instant`

### Image generation

- `VOICEFRAME_IMAGE_PROVIDER`
  - `placeholder` (default)
  - `comfyui` (requires ComfyUI + workflows)

**ComfyUI settings** (only used if `VOICEFRAME_IMAGE_PROVIDER=comfyui`)

- `COMFYUI_URL` (default: `http://127.0.0.1:8188`)
- `WORKFLOW_DIR` (default: `/workflows`)
- `CHAR_WORKFLOW` (default: `char_workflow.json`)
- `BG_WORKFLOW` (default: `background_workflow.json`)
- `VOICEFRAME_CHAR_PROMPT_NODE_ID` (default: `1005`) -> node id whose `inputs.value` is the character prompt
- `VOICEFRAME_BG_PROMPT_NODE_ID` (default: `102`) -> node id whose `inputs.value` is the background prompt

### Optional TTS

If unset, TTS is disabled.

- `VOICEFRAME_TTS_BASE_URL`
  - Example: `http://host.docker.internal:5005`
- `VOICEFRAME_TTS_ENDPOINT` (default: `/tts`)
- `VOICEFRAME_TTS_LANGUAGE` (default: `English`)

## Django proxy integration (Vistarak backend)

The Django app proxies to this service using:

- `VOICEFRAME_API_BASE_URL` (default: `http://127.0.0.1:8020`)
- `VOICEFRAME_PROXY_TIMEOUT` (default: `30` seconds)

So from Vistarak you can call:

- `POST /voiceframe/generate`
- `GET /voiceframe/status/<job_id>`
- `GET /voiceframe/result/<job_id>`

## Notes / Troubleshooting

- This service requires `ffmpeg` inside the container (installed via the Dockerfile).
- If you enable ComfyUI mode and the workflow JSON files or node ids do not match, image generation will fail.
- For Ollama/Groq, the prompt must be non-empty; the LLM is instructed to output a strict markdown format expected by the parser.
