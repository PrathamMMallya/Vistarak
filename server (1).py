import os
import uuid
import tempfile

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from groq_client import get_expressive_segments
from tts_engine import generate_audio_chunks
from audio_utils import merge_audio

# =========================================================
# FastAPI App
# =========================================================

app = FastAPI(
    title="Emotion TTS API",
    description="Emotion-aware Chatterbox TTS Service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# Output Directory
# =========================================================

BASE_DIR = os.path.dirname(__file__)

OUTPUT_DIR = os.path.join(BASE_DIR, "tts_output")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================================================
# Health Endpoint
# =========================================================

@app.get("/health")
def health():
    return {"status": "ok"}


# =========================================================
# TTS Endpoint
# =========================================================

@app.post("/generate/")
async def generate_audio(
    text: str = Form(...),
    ref_audio: UploadFile = File(None),
):

    session_id = str(uuid.uuid4())

    # -----------------------------------------------------
    # Save uploaded reference audio temporarily
    # -----------------------------------------------------

    ref_audio_path = None

    if ref_audio is not None:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as tmp:

            ref_audio_path = tmp.name

            tmp.write(await ref_audio.read())

    # -----------------------------------------------------
    # Step 1: Emotion segmentation
    # -----------------------------------------------------

    segments = get_expressive_segments(text)

    # -----------------------------------------------------
    # Step 2: Generate chunk audios
    # -----------------------------------------------------

    chunk_files = generate_audio_chunks(
        segments=segments,
        voice_path=ref_audio_path,
        session_id=session_id,
    )

    # -----------------------------------------------------
    # Step 3: Merge chunks
    # -----------------------------------------------------

    final_output = os.path.join(
        OUTPUT_DIR,
        f"final_{session_id}.wav"
    )

    merge_audio(
        files=chunk_files,
        segments=segments,
        output=final_output,
    )

    # -----------------------------------------------------
    # Return generated wav
    # -----------------------------------------------------

    return FileResponse(
        final_output,
        media_type="audio/wav",
        filename="output.wav"
    )


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=9055,
        reload=False
    )