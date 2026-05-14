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
def generate_story(request):
    """
    Dummy endpoint for story generation.
    """
    return JsonResponse({
        "status": "success", 
        "message": "Story generation triggered",
        "video_url": "http://localhost:8000/story/preview/"
    })
