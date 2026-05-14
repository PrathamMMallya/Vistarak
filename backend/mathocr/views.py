from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import re

DOCKER_URL = "http://172.16.2.131:9006"

def clean_latex(text):
    if not text:
        return ""
    # Clean up model special tokens like <|im_end|> or <|endoftext|>
    text = re.sub(r'<\|.*?\|>', '', text)
    text = re.sub(r'<\|im_end\|>', '', text)
    text = text.strip()

    if text.startswith('$') and text.endswith('$'):
        text = text[1:-1].strip()
    
    # If it's a TikZ picture, try to extract the nodes/text
    if "\\draw" in text or "\\begin{tikzpicture}" in text:
        # Extract content inside node{...}
        nodes = re.findall(r'node(?:\[.*?\])?\s*{([^}]+)}', text)
        if nodes:
            # Join multiple nodes with a newline for clarity
            return " ".join([n.strip().replace('$', '') for n in nodes if n.strip()])
    
    return text.strip()

@csrf_exempt
def img_to_latex(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method allowed'}, status=405)
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        
        try:
            files = {'file': (file.name, file.read(), file.content_type or 'image/png')}
            print(f"📹 Sending OCR request to {DOCKER_URL}/convert ...")
            response = requests.post(f"{DOCKER_URL}/convert", files=files, timeout=240)
            
            if response.status_code == 200:
                raw_latex = response.json().get('latex', '')
                print(f"✅ OCR Received: {raw_latex[:100]}...")
                
                cleaned_latex = clean_latex(raw_latex)
                print(f"✨ Cleaned LaTeX: {cleaned_latex}")
                
                return JsonResponse({'success': True, 'latex': cleaned_latex})
            else:
                print(f"❌ OCR Service Error {response.status_code}: {response.text}")
                return JsonResponse({
                    'error': 'Conversion failed',
                    'details': response.text
                }, status=response.status_code)
        except requests.exceptions.Timeout:
            print("❌ OCR Request Timeout")
            return JsonResponse({'error': 'Request timeout'}, status=504)
        except requests.exceptions.RequestException as e:
            print(f"❌ OCR Request failed: {str(e)}")
            return JsonResponse({'error': f'Request failed: {str(e)}'}, status=503)
    except Exception as e:
        print(f"❌ OCR Server error: {str(e)}")
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)