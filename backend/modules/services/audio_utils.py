import subprocess
import os
import tempfile
from django.conf import settings

def extract_audio_local(video_file):
    """
    Extracts audio from a video file using local FFmpeg.
    Returns the audio bytes.
    """
    ffmpeg_exe = os.path.join(getattr(settings, "FFMPEG_DIR", ""), "ffmpeg.exe")
    if not os.path.exists(ffmpeg_exe):
        # Fallback to system ffmpeg
        ffmpeg_exe = "ffmpeg"

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_tmp:
        for chunk in video_file.chunks():
            video_tmp.write(chunk)
        video_tmp_path = video_tmp.name

    audio_tmp_path = video_tmp_path + ".wav"

    try:
        command = [
            ffmpeg_exe, "-y",
            "-i", video_tmp_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_tmp_path
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        
        with open(audio_tmp_path, "rb") as f:
            audio_bytes = f.read()
            
        return audio_bytes
    finally:
        # Cleanup
        if os.path.exists(video_tmp_path):
            os.remove(video_tmp_path)
        if os.path.exists(audio_tmp_path):
            os.remove(audio_tmp_path)
