FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libpangocairo-1.0-0 \
    libcairo2 \
    libglib2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements into the image. With the build context set to
# `backend`, the microservice requirements are under `manim_microservice/`.
COPY manim_microservice/requirements.txt /app/manim_microservice/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/manim_microservice/requirements.txt

# Include the shared backend code and templates the microservice imports.
COPY visualization /app/visualization
COPY templates_manim /app/templates_manim
COPY manim_microservice /app/manim_microservice

RUN mkdir -p /app/media/manim /app/state

EXPOSE 8000

# The image keeps the microservice as a Python package under /app, so the
# ASGI entrypoint is manim_microservice.main:app.
CMD ["uvicorn", "manim_microservice.main:app", "--host", "0.0.0.0", "--port", "8000"]
