import os
import numpy as np
import soundfile as sf
import torch
from transformers import AutoModel
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import tempfile

# -------------------------
# Environment & Device
# -------------------------
os.environ["HUGGING_FACE_HUB_TOKEN"] = os.getenv("HF_TOKEN")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# -------------------------
# Load model ONCE at startup
# -------------------------
repo_id = "ai4bharat/IndicF5"
model = AutoModel.from_pretrained(repo_id, trust_remote_code=True).to(device)
model.eval()
print("Model loaded successfully.")

# -------------------------
# FastAPI App
# -------------------------
app = FastAPI()


@app.post("/generate/")
async def generate_audio(
    text: str = Form(...),
    ref_text: str = Form(""),
    ref_audio: UploadFile = File(None)
):
    ref_audio_path = None
    if ref_audio is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            ref_audio_path = tmp.name
            tmp.write(await ref_audio.read())

    # Run inference
    audio = model(text, ref_audio_path=ref_audio_path, ref_text=ref_text)

    # Convert int16 → float32 if needed
    if isinstance(audio, np.ndarray) and audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0

    output_path = "output.wav"
    sf.write(output_path, np.array(audio, dtype=np.float32), samplerate=24000)

    return FileResponse(output_path, media_type="audio/wav", filename="output.wav")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8005)
