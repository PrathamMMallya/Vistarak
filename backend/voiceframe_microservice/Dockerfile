FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    ; apt-get install -y --no-install-recommends ffmpeg curl fonts-dejavu-core \
    ; rm -rf /var/lib/apt/lists/*

COPY voiceframe_microservice/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY voiceframe_microservice /app/voiceframe_microservice

EXPOSE 8020

ENV VOICEFRAME_MEDIA_ROOT=/shared_media
ENV VOICEFRAME_STATE_DIR=/app/state
ENV VOICEFRAME_WORK_DIR=/app/work

CMD ["uvicorn", "voiceframe_microservice.main:app", "--host", "0.0.0.0", "--port", "8020"]
