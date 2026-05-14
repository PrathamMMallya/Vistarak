from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add modules directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import our custom modules
from mathcompute.modules.statistics import process_statistics
from mathcompute.modules.calculus import process_calculus
from mathcompute.modules.algebra import process_algebra
from mathcompute.modules.geometry import process_geometry
from mathcompute.modules.vectors import process_vectors

# Import AI parser
from mathcompute.modules.ai_parser import parse_with_ai, fallback_parser, validate_geometry_format

# Configuration
USE_AI_PARSER = True  # Set to False to use only fallback parser


@csrf_exempt
def home(request):
    return JsonResponse({
        'message': 'Math Visualizer Backend is Running! 🚀'
    })


@csrf_exempt
@require_http_methods(["POST"])
def visualize(request):
    """
    Main endpoint that receives LaTeX input and module type
    Returns visualization data
    
    NEW: Now supports AI-powered parsing of natural language inputs
    """
    try:
        # Get data from frontend
        data = json.loads(request.body)
        original_input = data.get('latex', '')
        module_type = data.get('module', '')
        use_ai = data.get('use_ai', USE_AI_PARSER)  # Allow frontend to override
        
        print(f"Received: Module={module_type}, Original Input={original_input}")
        
        # Parse input using AI or fallback
        parsed_input = original_input
        parsing_method = "original"
        
        if use_ai:
            try:
                parsed_input = parse_with_ai(original_input, module_type)
                parsing_method = "ai"
                print(f"AI Parsed: {parsed_input}")
                
                # Validate geometry format
                if module_type == 'geometry':
                    is_valid, error_msg = validate_geometry_format(parsed_input)
                    if not is_valid:
                        print(f"AI parsing validation failed: {error_msg}")
                        # Fall back to rule-based parser
                        parsed_input = fallback_parser(original_input, module_type)
                        parsing_method = "fallback"
                        print(f"Fallback Parsed: {parsed_input}")
                
            except Exception as e:
                print(f"AI parsing failed: {str(e)}, using fallback parser")
                parsed_input = fallback_parser(original_input, module_type)
                parsing_method = "fallback"
                print(f"Fallback Parsed: {parsed_input}")
        else:
            # Use fallback parser
            parsed_input = fallback_parser(original_input, module_type)
            parsing_method = "fallback"
            print(f"Fallback Parsed: {parsed_input}")
        
        # Route to appropriate module with parsed input
        if module_type == 'calculus':
            result = process_calculus(parsed_input)
        elif module_type == 'algebra':
            result = process_algebra(parsed_input)
        elif module_type == 'geometry':
            result = process_geometry(parsed_input)
        elif module_type == 'vectors':
            result = process_vectors(parsed_input)
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown module type: {module_type}'
            }, status=400)
        
        # Add parsing info to result
        result['parsing_info'] = {
            'original_input': original_input,
            'parsed_input': parsed_input,
            'method': parsing_method
        }
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def parse_only(request):
    """
    Endpoint to test AI parsing without running visualization
    Useful for debugging
    """
    try:
        data = json.loads(request.body)
        user_input = data.get('input', '')
        module_type = data.get('module', 'geometry')
        
        # Try AI parsing
        try:
            ai_parsed = parse_with_ai(user_input, module_type)
            ai_success = True
        except Exception as e:
            ai_parsed = str(e)
            ai_success = False
        
        # Try fallback parsing
        fallback_parsed = fallback_parser(user_input, module_type)
        
        return JsonResponse({
            'success': True,
            'original_input': user_input,
            'ai_parsing': {
                'success': ai_success,
                'result': ai_parsed
            },
            'fallback_parsing': {
                'result': fallback_parsed
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Check if server is running"""
    
    has_mistral_key = bool(os.getenv("MISTRAL_API_KEY"))
    
    return JsonResponse({
        'status': 'healthy',
        'message': 'Backend is running properly',
        'ai_parser_available': has_mistral_key,
        'features': {
            'ai_parsing': has_mistral_key,
            'fallback_parsing': True,
            'modules': ['calculus', 'algebra', 'geometry', 'vectors']
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def handle_statistics(request):
    """Handle statistics and probability requests"""
    try:
        data = json.loads(request.body)
        operation = data.get('operation')
        
        if operation == 'descriptive':
            # Descriptive statistics
            result = process_statistics(data.get('data'), 'descriptive')
        
        elif operation == 'normal_distribution':
            # Normal distribution
            result = process_statistics(data.get('params'), 'normal_distribution')
        
        elif operation == 'binomial_distribution':
            # Binomial distribution
            result = process_statistics(data.get('params'), 'binomial_distribution')
        
        elif operation == 'poisson_distribution':
            # Poisson distribution
            result = process_statistics(data.get('params'), 'poisson_distribution')
        
        elif operation == 'hypothesis_test':
            # Hypothesis testing
            result = process_statistics(data.get('params'), 'hypothesis_test')
        
        elif operation == 'regression':
            # Regression analysis
            result = process_statistics(data.get('params'), 'regression')
        
        elif operation == 'correlation':
            # Correlation analysis
            result = process_statistics(data.get('params'), 'correlation')
        
        else:
            return JsonResponse({
                'success': False,
                'error': f'Unknown operation: {operation}'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        print(f"Statistics error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def test_statistics(request):
    """Test statistics module with sample data"""
    try:
        # Test descriptive statistics
        sample_data = "23, 45, 67, 34, 56, 78, 90, 12, 45, 67, 89, 34, 56"
        result = process_statistics(sample_data, 'descriptive')
        
        return JsonResponse({
            'success': True,
            'message': 'Statistics module working!',
            'sample_result': result
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)