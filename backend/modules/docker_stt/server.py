import os
os.environ['TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD'] = '1'

from fastapi import FastAPI, UploadFile, File, Form
import uvicorn
import torch
import shutil
import sys
import warnings
import gc
import json
import time
import subprocess
import tempfile
from datetime import datetime
import whisperx
from nemo.collections.asr.models import SortformerEncLabelModel
import numpy as np

warnings.filterwarnings('ignore', category=UserWarning)

# Setup cuDNN paths
cudnn_paths = [
    '/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib',
    '/opt/conda/lib/python3.11/site-packages/ctranslate2.libs',
    '/opt/conda/lib/python3.11/site-packages/torch/lib'
]
current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
os.environ['LD_LIBRARY_PATH'] = ':'.join(cudnn_paths) + ':' + current_ld_path

# Preload cuDNN libraries
import ctypes
try:
    cudnn_lib_path = '/opt/conda/lib/python3.11/site-packages/nvidia/cudnn/lib'
    for lib in ['libcudnn_ops.so.9', 'libcudnn_cnn.so.9', 'libcudnn_adv.so.9']:
        lib_path = os.path.join(cudnn_lib_path, lib)
        if os.path.exists(lib_path):
            ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
    print("✓ cuDNN library preloaded successfully")
except Exception as e:
    print(f"⚠ Warning: Could not preload cuDNN: {e}")

app = FastAPI()

# Chunking configuration
CHUNK_LENGTH = 30.0  # 30 seconds per chunk (Whisper's optimal size)
STRIDE = CHUNK_LENGTH / 6  # 5 seconds overlap to prevent word splitting


def convert_to_mono_16k(input_file):
    """Convert audio to mono 16kHz WAV using FFmpeg (memory efficient)."""
    output_file = os.path.splitext(input_file)[0] + "_mono16k.wav"
    cmd = [
        'ffmpeg', '-i', input_file,
        '-ac', '1',  # mono
        '-ar', '16000',  # 16kHz
        '-y',  # overwrite
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_file


def get_audio_duration(audio_file):
    """Get audio duration using FFprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def create_audio_chunks(audio_array, sample_rate, chunk_length, stride):
    """
    Split audio into overlapping chunks.
    
    Args:
        audio_array: numpy array of audio samples
        sample_rate: audio sample rate (16000)
        chunk_length: length of each chunk in seconds (30.0)
        stride: overlap between chunks in seconds (5.0)
    
    Returns:
        List of (chunk_audio, start_time, end_time) tuples
    """
    chunk_samples = int(chunk_length * sample_rate)
    stride_samples = int(stride * sample_rate)
    
    chunks = []
    total_samples = len(audio_array)
    
    start_sample = 0
    while start_sample < total_samples:
        end_sample = min(start_sample + chunk_samples, total_samples)
        
        chunk_audio = audio_array[start_sample:end_sample]
        start_time = start_sample / sample_rate
        end_time = end_sample / sample_rate
        
        chunks.append((chunk_audio, start_time, end_time))
        
        # Move to next chunk with stride overlap
        start_sample += chunk_samples - stride_samples
        
        # If we've reached the end, break
        if end_sample >= total_samples:
            break
    
    return chunks


def merge_segments_from_chunks(chunk_results):
    """
    Merge segments from overlapping chunks, removing duplicates.
    
    Args:
        chunk_results: List of (segments, chunk_start_time) tuples
    
    Returns:
        Merged list of segments
    """
    all_segments = []
    
    for segments, chunk_offset in chunk_results:
        for seg in segments:
            # Adjust segment times to global timeline
            adjusted_seg = seg.copy()
            adjusted_seg['start'] += chunk_offset
            adjusted_seg['end'] += chunk_offset
            
            # Adjust word timings if present
            if 'words' in adjusted_seg:
                adjusted_words = []
                for word in adjusted_seg['words']:
                    adjusted_word = word.copy()
                    if 'start' in adjusted_word and adjusted_word['start'] is not None:
                        adjusted_word['start'] += chunk_offset
                    if 'end' in adjusted_word and adjusted_word['end'] is not None:
                        adjusted_word['end'] += chunk_offset
                    adjusted_words.append(adjusted_word)
                adjusted_seg['words'] = adjusted_words
            
            all_segments.append(adjusted_seg)
    
    # Remove overlapping duplicates (keep segments from later chunks in overlap regions)
    merged_segments = []
    for seg in all_segments:
        # Check if this segment overlaps significantly with any existing segment
        is_duplicate = False
        for existing in merged_segments:
            overlap_start = max(seg['start'], existing['start'])
            overlap_end = min(seg['end'], existing['end'])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            seg_duration = seg['end'] - seg['start']
            
            # If more than 80% of segment overlaps, consider it duplicate
            if overlap_duration > 0.8 * seg_duration:
                is_duplicate = True
                break
        
        if not is_duplicate:
            merged_segments.append(seg)
    
    # Sort by start time
    merged_segments.sort(key=lambda x: x['start'])
    
    return merged_segments


def transcribe_with_chunking(audio_file, model, device, chunk_length=30.0, stride=5.0, language=None):
    print(f"📊 Loading audio for chunked processing...")
    
    audio_array = whisperx.load_audio(audio_file)
    sample_rate = 16000
    duration = len(audio_array) / sample_rate
    
    print(f"📊 Audio duration: {duration:.2f}s")
    
    # ✅ Detect language ONCE using only the first 30s, before chunking
    if language is None:
        print("🌐 Detecting language from first 30s...")
        first_30s = audio_array[:30 * sample_rate]
        detect_result = model.transcribe(first_30s, batch_size=16, language=None)
        language = detect_result.get("language", "en")
        print(f"🌐 Detected language: {language} — will use for all chunks")
    
    chunks = create_audio_chunks(audio_array, sample_rate, chunk_length, stride)
    print(f"📊 Created {len(chunks)} chunks (chunk_length={chunk_length}s, stride={stride}s)")
    
    chunk_results = []
    
    for i, (chunk_audio, start_time, end_time) in enumerate(chunks, 1):
        print(f"🔄 Processing chunk {i}/{len(chunks)} ({start_time:.1f}s - {end_time:.1f}s)...")
        
        # ✅ Always pass the detected language — no re-detection
        result = model.transcribe(chunk_audio, batch_size=16, language=language)
        chunk_results.append((result['segments'], start_time))
        
        if i % 5 == 0:
            gc.collect()
    
    print(f"🔗 Merging {len(chunk_results)} chunks...")
    merged_segments = merge_segments_from_chunks(chunk_results)
    print(f"✅ Merged into {len(merged_segments)} segments")
    
    return {
        'segments': merged_segments,
        'language': language
    }


def format_time(seconds):
    """Convert seconds to SRT time format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def get_segment_speaker(segment):
    """Determine primary speaker from word-level assignments."""
    if "words" not in segment or not segment["words"]:
        return "Unknown"
    
    speaker_counts = {}
    for word in segment["words"]:
        speaker = word.get("speaker", "Unknown")
        speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
    
    return max(speaker_counts, key=speaker_counts.get) if speaker_counts else "Unknown"


def save_as_srt(segments, output_path):
    """Save segments as SRT file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            start = format_time(seg["start"])
            end = format_time(seg["end"])
            speaker = get_segment_speaker(seg)
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n[{speaker}] {text}\n\n")


def assign_word_speakers(words, diar_segments):
    """Assign speakers to words based on time overlap."""
    result = []
    for word in words:
        w_start, w_end = word.get("start"), word.get("end")
        if w_start is None or w_end is None:
            continue
        
        speaker = "Unknown"
        for seg in diar_segments:
            if w_start >= seg["start_time"] and w_end <= seg["end_time"]:
                speaker = seg["speaker"]
                break
        
        result.append({
            "word": word["word"],
            "start": w_start,
            "end": w_end,
            "score": word.get("score"),
            "speaker": speaker
        })
    return result


def parse_sortformer_output(sort_segments):
    """Parse Sortformer output to standard format."""
    diar_segments = []
    for seg_list in sort_segments:
        if isinstance(seg_list, list):
            for seg in seg_list:
                if isinstance(seg, str):
                    parts = seg.split()
                    if len(parts) == 3:
                        diar_segments.append({
                            "start_time": float(parts[0]),
                            "end_time": float(parts[1]),
                            "speaker": parts[2]
                        })
    return diar_segments


def run(audio_file, output_srt, output_json, device="cuda", compute_type="int8", lang_code=None):
    """Main processing pipeline with chunking."""
    start_time = time.time()
    timings = {}
    
    def step(name, func, *args, **kwargs):
        t0 = time.time()
        result = func(*args, **kwargs)
        timings[name] = time.time() - t0
        return result
    
    print(f"🚀 Starting at {datetime.now().strftime('%H:%M:%S')}")
    
    # Convert audio first (memory efficient)
    processed_audio = step("Audio Conversion", convert_to_mono_16k, audio_file)
    
    # Load WhisperX model
    model = step("WhisperX Model Load", whisperx.load_model, "small", device, compute_type=compute_type)
    
    # Transcribe with chunking
    result = step("Chunked Transcription", transcribe_with_chunking, 
                  processed_audio, model, device, 
                  chunk_length=CHUNK_LENGTH, stride=STRIDE, language=lang_code)
    segments, lang_code = result["segments"], result["language"]
    
    del model
    gc.collect()
    
    # Generate transcript
    transcript = " ".join([s["text"] for s in segments])
    
    # Align words (load full audio for alignment - this is necessary for WhisperX)
    try:
        audio = step("Audio Load for Alignment", whisperx.load_audio, processed_audio)
        align_model, metadata = step("Align Model Load", whisperx.load_align_model, lang_code, device)
        result = step("Alignment", whisperx.align, segments, align_model, metadata, audio, device)
        segments = result["segments"]
        del align_model, audio
        gc.collect()
    except Exception as e:
        print(f"⚠ Alignment failed: {e}, continuing without alignment")
    
    # Diarization with Sortformer
    sort_model = step("Sortformer Load", SortformerEncLabelModel.from_pretrained, 
                      "nvidia/diar_streaming_sortformer_4spk-v2")
    sort_model.eval().to(device)
    sort_segments, _ = step("Sortformer Diarization", sort_model.diarize, 
                           processed_audio, batch_size=1, include_tensor_outputs=True)
    del sort_model
    gc.collect()
    
    # Parse diarization output
    diar_segments = parse_sortformer_output(sort_segments)
    
    # Assign speakers to words
    for seg in segments:
        if "words" in seg:
            seg["words"] = assign_word_speakers(seg["words"], diar_segments)
    
    # Save outputs
    save_as_srt(segments, output_srt)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
    
    # Cleanup
    if os.path.exists(processed_audio):
        os.remove(processed_audio)
    
    # Summary
    total_time = time.time() - start_time
    print(f"\n📊 SUMMARY: Language={lang_code}, Segments={len(segments)}, Time={total_time:.2f}s")
    print(f"📊 Timing breakdown:")
    for name, duration in timings.items():
        print(f"   {name}: {duration:.2f}s")
    
    return lang_code, transcript


@app.post("/process_audio/")
async def process_audio(file: UploadFile = File(...), source_lan: str = Form(None)):
    """Process audio file with transcription and diarization."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save uploaded file
            input_path = os.path.join(tmpdir, file.filename)
            with open(input_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Set output paths
            output_srt = os.path.join(tmpdir, "output.srt")
            output_json = os.path.join(tmpdir, "output.json")
            
            # Auto-detect language if needed
            if source_lan == 'auto':
                source_lan = None
            
            # Process
            detect_lan, transcript = run(
                audio_file=input_path,
                output_srt=output_srt,
                output_json=output_json,
                device="cuda" if torch.cuda.is_available() else "cpu",
                compute_type="int8",
                lang_code=source_lan
            )
            
            # Read results
            with open(output_srt, "r", encoding="utf-8") as f:
                srt_data = f.read()
            with open(output_json, "r", encoding="utf-8") as f:
                json_data = json.load(f)
        
        return {
            "status": "success",
            "message": "Processing complete",
            "srt_content": srt_data,
            "json_content": json_data,
            "only_transcript": transcript,
            "source_lan": detect_lan
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/clear_memory/")
async def clear_memory():
    """Clear CUDA memory cache."""
    try:
        print("🧹 Clearing CUDA memory...")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            torch.cuda.reset_accumulated_memory_stats()
        print("✅ CUDA memory cleared.")
        return {"status": "success", "message": "CUDA memory cleared successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8003)