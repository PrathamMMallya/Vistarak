import os
from django.http import FileResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def serve_default_story(request):
    """
    Serves a default video for the story generator preview.
    """
    potential_paths = [
        os.path.join(settings.BASE_DIR, "media", "sample_story.mp4"),
    ]
    
    for path in potential_paths:
        if os.path.exists(path):
            response = FileResponse(open(path, 'rb'), content_type='video/mp4')
            response["Accept-Ranges"] = "bytes"
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            return response
            
    return JsonResponse({"error": "No default video found on server"}, status=404)

@csrf_exempt
def story_config(request):
    """
    Returns the Story Server configuration from .env
    """
    server_url = os.environ.get("STORY_SERVER_URL", "http://127.0.0.1:8001").rstrip('/')
    ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
    
    return JsonResponse({
        "server_url": server_url,
        "ws_url": f"{ws_url}/ws/progress"
    })

@csrf_exempt
def generate_story(request):
    """
    Returns the configuration for the frontend to initiate a WS connection.
    """
    return story_config(request)
