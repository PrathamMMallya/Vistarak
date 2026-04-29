# manim_microservice

Lightweight FastAPI microservice that renders Manim animations and serves generated media locally.

Purpose
- Provide a dedicated containerized service for generating Manim videos used by the Vistarak project.
- Expose simple JSON endpoints for template info, generation, and an optional chat/assist endpoint.
- Serve generated media under `/media/` from inside the container (container-local storage policy).

Quick Start (Docker Compose - recommended for development)

From the repo root:

```bash
# Build and run via the provided compose file
docker compose -f docker-compose.manim.yml up --build -d

# Tear down and remove container+built resources
docker compose -f docker-compose.manim.yml down
```

Quick Start (docker build + run)

```bash
# Build the image (from repo root)
docker build -f backend/manim_microservice/Dockerfile -t vistarak-manim:latest backend/manim_microservice

# Run (example mapping container port 8000 -> host 8010)
docker run --rm -p 8010:8000 \
  -e GROQ_API_KEY="<your-groq-key>" \
  -e GROQ_MODEL="<model-name>" \
  vistarak-manim:latest
```

Important environment variables
- `GROQ_API_KEY`: (required for template parsing / LLM assist) API key used by the microservice.
- `GROQ_MODEL`: Model name for LLM interactions (if used).
- `MANIM_MEDIA_ROOT`: Path where generated media will be written inside the container (defaults to `/app/media/manim`).
- `MANIM_STATE_DIR`: Path for persistent state inside container (defaults to `/app/state`).
- `MANIM_CORS_ORIGINS`: Optional CORS origins; may be set if serving directly to remote frontends.

Django / Frontend integration notes
- Django proxy: set the Django env `MANIM_API_BASE_URL` to point to the microservice (e.g. `http://127.0.0.1:8010`) so Django can forward requests.
- Frontend: use `NEXT_PUBLIC_MANIM_API_BASE_URL` to point the frontend directly to the microservice, or set `NEXT_PUBLIC_MANIM_API_USE_DJANGO=true` to route via Django.

API Endpoints (implemented)
- `GET /health` — health check (200 OK).
- `GET /manim/template-info/?id=<template_id>` — returns template metadata and editable inputs for a template.
- `POST /manim/generate/` — request a render; returns JSON with `media` path (e.g. `/media/manim/xyz.mp4`) and metadata.
- `POST /manim/chat/` — optional conversational/assist endpoint used by the UI.
- `GET /media/...` — static serving of generated media (video files).

Media lifecycle policy
- Generated media is stored inside the container under `MANIM_MEDIA_ROOT` by default.
- This storage is container-local: stopping the container preserves files while container exists; removing the container (e.g., `docker compose down` without volumes, or `docker rm`) will delete files.
- If you need persistence beyond container removal, mount a host directory or use external object storage (S3) by adapting the Docker Compose file.

Verifying the service
- Health check:
```bash
curl http://127.0.0.1:8010/health
```
- Template info example:
```bash
curl "http://127.0.0.1:8010/manim/template-info/?id=math.gradient_descent"
```
- Trigger a generation (example JSON payload depends on templates used):
```bash
curl -X POST http://127.0.0.1:8010/manim/generate/ -H "Content-Type: application/json" -d '{"template_id":"...","params":{}}'
```

Common troubleshooting
- Docker build COPY errors: ensure you run `docker build` from the repo root or use the compose file. COPY paths in the Dockerfile are relative to the image build `context`.
- `ModuleNotFoundError: No module named 'visualization'`: the Dockerfile expects shared app folders to be copied into the image; use the provided compose file which uses the correct context.
- `uvicorn: executable file not found`: ensure `uvicorn` is installed in the image via `requirements.txt`; use the compose/build flow to pick up the correct image layers.
- Browser video players show `206 Partial Content` in logs: this is expected (Range requests for streaming) and not an error.
- Docker engine http2 preface/pipe errors during builds: restart Docker Desktop and retry, or try `DOCKER_BUILDKIT=0 docker compose build` if BuildKit causes issues.

Logs & Debugging
- Container logs show FastAPI access logs. Template-info and generate calls should return 200 when functioning.
- If Django is proxying requests, the Django server logs will show the proxied calls and any rewriting of media URLs.

Security and production notes
- This microservice currently exposes media and generation endpoints without auth. For production, add authentication, rate-limiting, and place the service behind an API gateway.
- Consider moving media to durable storage and only serve signed URLs for production.

Planned / Upcoming improvements
- Add request timeouts and more robust error handling.
- Add optional persistent storage (volume + retention policy) or S3-backed media storage.
- Add authentication for generation endpoints.
- Add CI checks and a minimal integration test suite.

Files of interest
- Dockerfile: `backend/manim_microservice/Dockerfile`
- Service code: `backend/manim_microservice/main.py`
- Templates: `backend/templates_manim/` (copied into the image at build-time)

