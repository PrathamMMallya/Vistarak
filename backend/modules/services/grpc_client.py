import grpc
from . import media_pb2 as pb2
from . import media_pb2_grpc as pb2_grpc

# Safe chunk size (4 MB)
CHUNK_SIZE = 4 * 1024 * 1024


def video_stream(video_bytes):
    """
    Generator that yields VideoChunk messages (streaming)
    Breaks large video into 4MB pieces
    """
    total_size = len(video_bytes)
    sent = 0
    
    for i in range(0, total_size, CHUNK_SIZE):
        chunk_data = video_bytes[i:i + CHUNK_SIZE]
        sent += len(chunk_data)
        print(f"📤 Sending chunk: {len(chunk_data)} bytes ({sent}/{total_size})")
        
        # ✅ Yield VideoChunk (not VideoRequest!)
        yield pb2.VideoChunk(data=chunk_data)
    
    print(f"✅ All chunks sent: {sent} bytes")


def extract_audio_via_grpc(video_bytes):
    """
    Extract audio from video via gRPC streaming
    
    Args:
        video_bytes: bytes or file-like object (Django UploadedFile)
    
    Returns:
        bytes: Extracted audio data (WAV format)
    """
    # Read file if file-like object (Django UploadedFile)
    if hasattr(video_bytes, "read"):
        print("📖 Reading from file-like object...")
        video_bytes = video_bytes.read()
    
    print(f"📹 Video size: {len(video_bytes)} bytes ({len(video_bytes) / (1024**3):.2f} GB)")

    channel = grpc.insecure_channel(
        "172.16.2.131:9004",
        options=[
            ("grpc.max_send_message_length", -1),
            ("grpc.max_receive_message_length", -1),
        ]
    )

    stub = pb2_grpc.MediaServiceStub(channel)

    try:
        print("🚀 Starting streaming upload...")
        # ✅ STREAMING CALL: Pass generator to ExtractAudio
        response = stub.ExtractAudio(video_stream(video_bytes))
        
        print(f"✅ Received audio: {len(response.audio_data)} bytes")
        return response.audio_data
        
    except grpc.RpcError as e:
        print(f"❌ gRPC Error: {e.code()} - {e.details()}")
        raise
    finally:
        channel.close()


def is_grpc_alive():
    """
    Check if gRPC server is alive
    """
    channel = None
    try:
        channel = grpc.insecure_channel(
            "172.16.2.131:9004",
            options=[
                ('grpc.enable_http_proxy', 0),
            ]
        )
        stub = pb2_grpc.MediaServiceStub(channel)
        resp = stub.HealthCheck(pb2.Empty(), timeout=5)
        return resp.status == "OK"
    except Exception as e:
        print(f"❌ gRPC health check failed: {e}")
        return False
    finally:
        if channel:
            channel.close()