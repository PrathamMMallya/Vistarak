from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import re

DOCKER_URL = "http://172.16.2.131:9006"

def clean_latex(text):
    if not text:
        return ""
    text = re.sub(r'<\|.*?\|>', '', text).strip()
    if text.startswith('$') and text.endswith('$'):
        text = text[1:-1].strip()
    tikz_pattern = r'\\begin{tikzpicture}.*?\\end{tikzpicture}'
    tikz_matches = re.findall(tikz_pattern, text, re.DOTALL)
    if tikz_matches:
        math_content = []
        for tikz in tikz_matches:
            nodes = re.findall(r'node(?:\[.*?\])?\s*{([^}]+)}', tikz)
            for content in nodes:
                content = content.strip()
                if content.startswith('$') and content.endswith('$'):
                    content = content[1:-1]
                if content:
                    math_content.append(content)
        if math_content:
            text = ' '.join(math_content)
    text = re.sub(tikz_pattern, '', text, flags=re.DOTALL)
    text = re.sub(r'\s+', ' ', text).strip()
    return f"${text}$" if text and not text.startswith('$') else text

@csrf_exempt
def img_to_latex(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method allowed'}, status=405)
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        
        try:
            check = requests.get(DOCKER_URL, timeout=10)
            if check.status_code != 200:
                return JsonResponse({'error': 'Docker service not running'}, status=503)
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Docker unavailable: {str(e)}'}, status=503)
        
        try:
            files = {'file': (file.name, file.read(), file.content_type or 'image/png')}
            response = requests.post(f"{DOCKER_URL}/convert", files=files, timeout=240)
            
            if response.status_code == 200:
                print(response.json())
                # latex_text = clean_latex(response.json().get('latex', ''))
                
                return JsonResponse({'success': True, 'latex': response.json().get('latex', '')})
            else:
                return JsonResponse({
                    'error': 'Conversion failed',
                    'details': response.text
                }, status=response.status_code)
        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'Request timeout'}, status=504)
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Request failed: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)