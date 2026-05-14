"""
AI-Powered Calculus LaTeX Parser using Mistral
Converts ANY LaTeX format into clean, parseable expressions

COMPLETELY FIXED - Handles all AI response formats
"""

import os
import json
import re
from mistralai import Mistral

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None

def normalize_calculus_with_ai(latex_input, operation_type="auto"):
    """
    Use Mistral AI to normalize ANY calculus LaTeX input
    
    Args:
        latex_input: Raw LaTeX string (can be messy)
        operation_type: "definite_integral", "limit", "derivative", "taylor", "partial", or "auto"
    
    Returns:
        Clean, standardized LaTeX that parse_expression() can handle
    """
    
    if not client:
        raise Exception("Mistral API key not found. Set MISTRAL_API_KEY in .env file")
    
    # Detect operation type if auto
    if operation_type == "auto":
        operation_type = detect_operation_type(latex_input)
    
    # Build prompt based on operation type
    prompt = build_normalization_prompt(latex_input, operation_type)
    
    try:
        # Call Mistral API
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistency
            max_tokens=500
        )
        
        # Extract normalized LaTeX
        raw_response = response.choices[0].message.content.strip()
        
        print(f"[AI PARSER] Raw AI Response: '{raw_response}'")
        
        # CRITICAL FIX: Clean up the AI response AGGRESSIVELY
        normalized = clean_ai_response(raw_response, latex_input)
        
        print(f"[AI PARSER] Input: {latex_input}")
        print(f"[AI PARSER] Final Output: {normalized}")
        
        return normalized
        
    except Exception as e:
        print(f"[AI PARSER] Error: {e}")
        raise Exception(f"AI parsing failed: {str(e)}")


def clean_ai_response(text, original_input):
    """
    ULTRA-AGGRESSIVE cleaning of AI response
    
    AI might return:
    - "Understood. Please provide the LaTeX expression you'd like me to normalize."
    - "Input: ( sin x \cos^{4} x ) Output: sin(x)*cos(x)**4"
    - "```latex\n\\int x^2 dx\n```"
    - "Output: \\int x^2 dx"
    - Just the LaTeX itself
    
    We need ONLY the cleaned LaTeX expression.
    """
    original = text
    
    # STEP 1: If AI is asking for input, it means it didn't understand - return original
    asking_phrases = [
        'please provide',
        'what expression',
        'which expression',
        'understood',
        'i need',
        'can you provide',
        'what would you like'
    ]
    
    if any(phrase in text.lower() for phrase in asking_phrases):
        print(f"[CLEAN] AI is asking for input, returning original")
        return original_input
    
    # STEP 2: Remove markdown code blocks
    text = re.sub(r'```(?:latex|math)?\s*', '', text)
    text = text.replace('```', '')
    
    # STEP 3: Remove "Input: ..." patterns AGGRESSIVELY
    # Match "Input:" followed by anything until "Output:" or end
    text = re.sub(r'Input\s*:.*?(?=Output\s*:|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # STEP 4: Extract after "Output:" if present
    output_match = re.search(r'Output\s*:\s*(.+)', text, re.IGNORECASE | re.DOTALL)
    if output_match:
        text = output_match.group(1)
    
    # STEP 5: Remove common prefixes
    prefixes_to_remove = [
        r'^\s*Output\s*:\s*',
        r'^\s*Result\s*:\s*',
        r'^\s*Answer\s*:\s*',
        r'^\s*LaTeX\s*:\s*',
        r'^\s*Normalized\s*:\s*',
        r'^\s*Clean\s*:\s*',
        r'^\s*Expression\s*:\s*',
        r'^\s*The\s+(?:normalized|cleaned|result)\s+(?:expression|latex)\s+is\s*:\s*',
    ]
    
    for prefix_pattern in prefixes_to_remove:
        text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE)
    
    # STEP 6: If there's a colon followed by LaTeX, take everything after the last colon
    if ':' in text and ('\\' in text or 'x' in text):
        # Find the last colon before LaTeX/math content
        parts = text.split(':')
        if len(parts) > 1:
            # Take the last part after a colon
            text = parts[-1]
    
    # STEP 7: Remove any remaining sentence fragments
    # If text starts with words like "The", "This", "Here", remove until we hit LaTeX
    text = re.sub(r'^(?:The|This|Here|It)\s+\w+\s+(?:is|are)\s*:?\s*', '', text, flags=re.IGNORECASE)
    
    # STEP 8: Clean up whitespace and newlines
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    
    # STEP 9: Remove trailing punctuation that's not part of LaTeX
    text = re.sub(r'[,;]+$', '', text)
    
    # STEP 10: If result is empty or too short, return original input
    if len(text) < 3 or not any(c in text for c in ['x', '\\', '(', '+', '-', '*', '/']):
        print(f"[CLEAN] Result too short or invalid, returning original")
        return original_input
    
    print(f"[CLEAN] Before: '{original}'")
    print(f"[CLEAN] After: '{text}'")
    
    return text


def detect_operation_type(latex_input):
    """Detect what type of calculus operation this is"""
    lower = latex_input.lower()
    
    if '\\int_' in lower or 'int_' in lower:
        return "definite_integral"
    elif '\\int' in lower or 'int' in lower:
        return "indefinite_integral"
    elif '\\lim' in lower or 'lim' in lower:
        return "limit"
    elif '\\frac{d' in lower or 'frac{d' in lower or 'derivative' in lower:
        return "derivative"
    elif 'taylor' in lower or 'maclaurin' in lower or 'series' in lower:
        return "taylor"
    elif 'partial' in lower or '\\partial' in lower:
        return "partial"
    else:
        return "standard_function"


def build_normalization_prompt(latex_input, operation_type):
    """Build the perfect prompt for each operation type"""
    
    # CRITICAL: Make the prompt VERY explicit about output format
    base_instruction = f"""
You are a LaTeX normalization expert. Your job is to convert the given LaTeX expression into a clean, Python-parseable format.

INPUT: {latex_input}

CRITICAL RULES:
1. Respond with ONLY the cleaned expression
2. NO explanations, NO labels like "Output:", NO markdown
3. Just the raw cleaned expression and nothing else

"""
    
    if operation_type == "definite_integral":
        return base_instruction + """
DEFINITE INTEGRAL FORMAT:
Convert to: \\int_{a}^{b} f(x) dx

Rules:
- Bounds in {braces}: \\int_{-1}^{1}
- Clean function: sin(x)*cos(x)**4
- Remove \\, spacing

Example: \\sin x \\cos^4 x → sin(x)*cos(x)**4

Respond with ONLY the cleaned LaTeX:"""
    
    elif operation_type == "limit":
        return base_instruction + """
LIMIT FORMAT:
Convert to: \\lim_{x \\to a} f(x)

Rules:
- Approach in braces: \\lim_{x \\to 2}
- Use \\infty for infinity
- Clean function with parentheses

Respond with ONLY the cleaned LaTeX:"""
    
    elif operation_type == "derivative":
        return base_instruction + """
DERIVATIVE FORMAT:
Convert to: \\frac{d}{dx} f(x)

Rules:
- Keep derivative notation clean
- Function with proper parentheses: sin(x)
- Powers: cos^2(x) → (cos(x))**2

Respond with ONLY the cleaned LaTeX:"""
    
    elif operation_type == "taylor":
        return base_instruction + """
TAYLOR SERIES FORMAT:
Convert to: taylor f(x) at center order n

Example: taylor sin(x) at 0 order 5

Respond with ONLY the cleaned LaTeX:"""
    
    elif operation_type == "partial":
        return base_instruction + """
PARTIAL DERIVATIVE FORMAT:
Convert to: \\frac{\\partial}{\\partial x} f(x,y)

Or for second order: \\frac{\\partial^2}{\\partial x^2} f(x,y)

Respond with ONLY the cleaned LaTeX:"""
    
    else:  # standard_function
        return base_instruction + """
STANDARD FUNCTION FORMAT:
Convert to clean expression like: sin(x)*cos(x)**2 + x**3

CRITICAL TRANSFORMATIONS:
- sin x → sin(x)
- cos^4 x → (cos(x))**4
- x sin(x) → x*sin(x)
- 2x → 2*x
- e^x → exp(x)
- \\ln x → log(x)

Respond with ONLY the cleaned expression (NO "Output:" prefix):"""


# System prompt for Mistral - ULTRA EXPLICIT
SYSTEM_PROMPT = """You are a LaTeX-to-Python expression converter.

YOUR ONLY JOB: Convert LaTeX math expressions into clean, parseable format.

CRITICAL OUTPUT RULES:
1. Output ONLY the converted expression
2. NO explanations
3. NO prefixes like "Output:", "Result:", "The expression is:"
4. NO markdown code blocks
5. NO conversational text
6. Just the raw cleaned expression

TRANSFORMATION RULES:
- sin x → sin(x)
- cos^4 x → (cos(x))**4  
- x sin(x) → x*sin(x)
- 2x → 2*x
- e^x → exp(x)
- \\ln x → log(x)
- \\sqrt{x} → sqrt(x)
- \\frac{a}{b} → (a)/(b)

EXAMPLES:
User: \\sin x \\cos^{4} x
You: sin(x)*cos(x)**4

User: \\frac{x^2 + 1}{x - 2}
You: (x**2 + 1)/(x - 2)

User: e^x \\ln x
You: exp(x)*log(x)

Remember: Respond with ONLY the expression, nothing else. No "Output:", no "The result is", just the clean expression."""


def test_ai_parser():
    """Test function to verify AI parser works"""
    test_cases = [
        ("\\sin x \\cos^{4} x", "standard_function"),
        ("\\lim_{x \\to 2} \\frac{x^2 - 4}{x - 2}", "limit"),
        ("\\frac{d}{dx} \\sin x \\cos x", "derivative"),
        ("e^x + \\ln x", "standard_function"),
        ("\\int_{-1}^{1} x^2 dx", "definite_integral"),
    ]
    
    print("=" * 60)
    print("TESTING AI PARSER")
    print("=" * 60)
    
    for latex_input, op_type in test_cases:
        try:
            result = normalize_calculus_with_ai(latex_input, op_type)
            print(f"✅ {latex_input}")
            print(f"   → {result}\n")
        except Exception as e:
            print(f"❌ {latex_input}")
            print(f"   Error: {e}\n")


if __name__ == "__main__":
    # Test if run directly
    test_ai_parser()