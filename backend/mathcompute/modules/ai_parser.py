"""
AI Parser using Mistral API
Converts natural language/flexible inputs into structured geometry function calls
"""

import os
import json
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Mistral client
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
client = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None

def parse_with_ai(user_input, module_type='geometry'):
    """
    Use Mistral AI to parse user input into structured format
    
    Args:
        user_input: Natural language or LaTeX input from user
        module_type: The math module (geometry, calculus, algebra, vectors)
    
    Returns:
        Structured function call string
    """
    
    if not client:
        raise Exception("Mistral API key not configured. Set MISTRAL_API_KEY environment variable.")
    
    # Quick check: If input is already in correct format, return as-is
    if is_already_formatted(user_input, module_type):
        return user_input
    
    # Create comprehensive prompt based on module type
    system_prompt = get_system_prompt(module_type)
    
    try:
        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Convert this input to the correct function format: {user_input}"
                }
            ],
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=500
        )
        
        parsed_output = response.choices[0].message.content.strip()
        
        # Extract just the function call if AI adds explanation
        parsed_output = extract_function_call(parsed_output)
        
        return parsed_output
    
    except Exception as e:
        raise Exception(f"AI parsing failed: {str(e)}")


def get_system_prompt(module_type):
    """Generate system prompt based on module type"""
    
    if module_type == 'geometry':
        return """You are a geometry input parser. Convert user inputs into exact function calls.

**COORDINATE GEOMETRY:**
- Distance: distance((x1,y1), (x2,y2))
- Midpoint: midpoint((x1,y1), (x2,y2))
- Slope: slope((x1,y1), (x2,y2))
- Line equation: line((x1,y1), (x2,y2))
- Triangle area: area_triangle((x1,y1), (x2,y2), (x3,y3))
- Collinearity: collinear((x1,y1), (x2,y2), (x3,y3))

**CIRCLES:**
- From equation: x^2 + y^2 = r^2  OR  (x-h)^2 + (y-k)^2 = r^2
- Construction: circle(center=(h,k), radius=r)
- Tangent: tangent_length(circle=(center=(h,k), radius=r), point=(x,y))

**TRIANGLES:**
- Pythagoras: pythagoras(a=val, b=val) OR pythagoras(a=val, c=val) OR pythagoras(b=val, c=val)
  * "legs" or "sides" = a and b (unknown is c/hypotenuse)
  * "hypotenuse" = c
  * Examples:
    - "right triangle with legs 3 and 4" → pythagoras(a=3, b=4)
    - "find hypotenuse of triangle with legs 3 and 4" → pythagoras(a=3, b=4)
    - "right triangle sides 3 and 4" → pythagoras(a=3, b=4)
    - "triangle with side a=5 and hypotenuse c=13" → pythagoras(a=5, c=13)
- Analysis: triangle((x1,y1), (x2,y2), (x3,y3))
- Centroid: centroid((x1,y1), (x2,y2), (x3,y3))
- Circumcenter: circumcenter((x1,y1), (x2,y2), (x3,y3))

**2D MENSURATION:**
- Rectangle: rectangle(length=L, width=W)
- Square: square(side=s)
- Circle area: circle_area(radius=r)
- Circle circumference: circle_circumference(radius=r)

**3D SOLIDS:**
- Cube: cube(side=s)
- Cuboid: cuboid(length=L, width=W, height=H)
- Cylinder: cylinder(radius=r, height=h)
- Cone: cone(radius=r, height=h) OR cone(radius=r, slant_height=l)
- Sphere: sphere(radius=r)
- Hemisphere: hemisphere(radius=r)

**RULES:**
1. Return ONLY the function call or equation, nothing else
2. If input is ALREADY in correct format (e.g., "distance((2,3), (5,7))"), return it UNCHANGED
3. If input is a LaTeX equation (e.g., "x^2 + y^2 = 25"), return it UNCHANGED
4. Use exact parameter names (length=, width=, radius=, etc.)
5. Points must be in parentheses: (x,y)
6. Numbers can be integers or decimals
7. For equations, preserve the exact format with ^, =, etc.

**EXAMPLES:**
Input: "distance between (2,3) and (5,7)"
Output: distance((2,3), (5,7))

Input: "distance((2,3), (5,7))"  ← Already formatted
Output: distance((2,3), (5,7))

Input: "x^2 + y^2 = 25"  ← LaTeX equation
Output: x^2 + y^2 = 25

Input: "(x-2)^2 + (y-3)^2 = 16"  ← LaTeX equation
Output: (x-2)^2 + (y-3)^2 = 16

Input: "find the midpoint of points 1,2 and 5,8"
Output: midpoint((1,2), (5,8))

Input: "circle with center at origin and radius 5"
Output: circle(center=(0,0), radius=5)

Input: "right triangle with sides 3 and 4"
Output: pythagoras(a=3, b=4)

Input: "find hypotenuse of triangle with legs 3 and 4"
Output: pythagoras(a=3, b=4)

Input: "right triangle legs 3 and 4"
Output: pythagoras(a=3, b=4)

Input: "pythagorean theorem with a=5 and c=13"
Output: pythagoras(a=5, c=13)

Input: "cube of side 5"
Output: cube(side=5)

Input: "rectangle 10 by 6"
Output: rectangle(length=10, width=6)

Input: "x squared plus y squared equals 25"
Output: x^2 + y^2 = 25

Now convert the user's input following these exact patterns."""

    elif module_type == 'calculus':
        return """You are a calculus input parser. Convert user inputs into function format.

**SUPPORTED OPERATIONS:**
- Derivative: Use standard calculus notation or describe the function
- Integral: Use standard integral notation
- Limit: Describe the limit
- Series: Describe the series

Return the mathematical expression in standard LaTeX/symbolic form.

**EXAMPLES:**
Input: "derivative of x squared"
Output: x^2

Input: "integrate sin(x)"
Output: sin(x)

Convert the user's input to proper mathematical notation."""

    elif module_type == 'algebra':
        return """You are an algebra input parser. Convert user inputs into equation format.

**SUPPORTED:**
- Linear equations: ax + b = c
- Quadratic equations: ax^2 + bx + c = 0
- System of equations
- Polynomial equations

Return equations in standard mathematical notation.

**EXAMPLES:**
Input: "solve x plus 5 equals 10"
Output: x + 5 = 10

Input: "quadratic x squared minus 3x plus 2 equals zero"
Output: x^2 - 3*x + 2 = 0

Convert the user's input to proper equation format."""

    elif module_type == 'vectors':
        return """You are a vector input parser. Convert user inputs into vector format.

**SUPPORTED:**
- Single vector: Use i, j, k notation or bracket notation
- Vector pairs: For operations like dot product, cross product

Return vectors in i, j, k notation or bracket form.

**EXAMPLES:**
Input: "vector 3i + 4j + 5k"
Output: 3i + 4j + 5k

Input: "vector [1, 2, 3]"
Output: 1i + 2j + 3k

Convert the user's input to proper vector notation."""
    
    return "You are a math input parser. Convert the input to proper mathematical notation."


def extract_function_call(ai_response):
    """Extract just the function call from AI response"""
    
    # Remove common prefixes
    prefixes = ["Output:", "Result:", "Answer:", "Function:", "Call:"]
    for prefix in prefixes:
        if ai_response.startswith(prefix):
            ai_response = ai_response[len(prefix):].strip()
    
    # Remove markdown code blocks if present
    if "```" in ai_response:
        lines = ai_response.split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code or (not in_code and line.strip() and not line.startswith("#")):
                code_lines.append(line)
        ai_response = "\n".join(code_lines).strip()
    
    # Take first line if multi-line
    if "\n" in ai_response:
        ai_response = ai_response.split("\n")[0].strip()
    
    return ai_response


def validate_geometry_format(parsed_input):
    """
    Validate that the parsed input matches expected geometry formats
    Returns (is_valid, error_message)
    """
    
    # List of valid geometry functions
    valid_functions = [
        'distance', 'midpoint', 'slope', 'line', 'area_triangle', 'collinear',
        'circle', 'tangent_length',
        'pythagoras', 'triangle', 'centroid', 'circumcenter',
        'rectangle', 'square', 'circle_area', 'circle_circumference',
        'cube', 'cuboid', 'cylinder', 'cone', 'sphere', 'hemisphere'
    ]
    
    # Check if it's an equation (contains =)
    if '=' in parsed_input and ('x' in parsed_input.lower() or 'y' in parsed_input.lower()):
        return True, None
    
    # Check if it starts with a valid function
    func_name = parsed_input.split('(')[0].strip()
    if func_name in valid_functions:
        return True, None
    
    return False, f"Invalid format. Function '{func_name}' not recognized."


# Fallback parser (rule-based) if AI fails or API key not available
def fallback_parser(user_input, module_type='geometry'):
    """Simple rule-based parser as fallback"""
    
    import re
    
    lower = user_input.lower().strip()
    
    # Distance detection
    if any(word in lower for word in ['distance', 'dist']):
        points = re.findall(r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', user_input)
        if len(points) >= 2:
            return f"distance(({points[0][0]},{points[0][1]}), ({points[1][0]},{points[1][1]}))"
    
    # Midpoint detection
    if 'midpoint' in lower or 'middle' in lower:
        points = re.findall(r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', user_input)
        if len(points) >= 2:
            return f"midpoint(({points[0][0]},{points[0][1]}), ({points[1][0]},{points[1][1]}))"
    
    # Circle detection
    if 'circle' in lower:
        center = re.search(r'center.*?\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', lower)
        radius = re.search(r'radius.*?(\d+\.?\d*)', lower)
        if center and radius:
            return f"circle(center=({center.group(1)},{center.group(2)}), radius={radius.group(1)})"
    
    # Pythagoras detection - Enhanced for natural language
    if any(word in lower for word in ['pythag', 'right triangle', 'hypotenuse', 'legs', 'leg']):
        # Try to extract numbers
        numbers = re.findall(r'\b(\d+\.?\d*)\b', lower)
        
        # Check for explicit parameter labels
        a = re.search(r'a\s*=?\s*(\d+\.?\d*)', lower)
        b = re.search(r'b\s*=?\s*(\d+\.?\d*)', lower)
        c = re.search(r'c\s*=?\s*(\d+\.?\d*)', lower)
        
        params = []
        
        if a:
            params.append(f"a={a.group(1)}")
        if b:
            params.append(f"b={b.group(1)}")
        if c:
            params.append(f"c={c.group(1)}")
        
        # If no explicit labels but we have numbers
        if len(params) < 2 and len(numbers) >= 2:
            # Check context for what's being asked
            if 'hypotenuse' in lower or 'find c' in lower:
                # User wants to find hypotenuse, so numbers are a and b
                params = [f"a={numbers[0]}", f"b={numbers[1]}"]
            elif 'leg' in lower or 'side' in lower:
                # Extract based on context
                if len(numbers) == 2:
                    params = [f"a={numbers[0]}", f"b={numbers[1]}"]
                elif len(numbers) == 3:
                    params = [f"a={numbers[0]}", f"b={numbers[1]}", f"c={numbers[2]}"]
        
        if len(params) >= 2:
            return f"pythagoras({', '.join(params)})"
    
    # Rectangle detection
    if 'rectangle' in lower:
        length = re.search(r'(?:length|l)\s*=?\s*(\d+\.?\d*)', lower)
        width = re.search(r'(?:width|w)\s*=?\s*(\d+\.?\d*)', lower)
        if length and width:
            return f"rectangle(length={length.group(1)}, width={width.group(1)})"
    
    # Cube detection
    if 'cube' in lower:
        side = re.search(r'(?:side|s)\s*=?\s*(\d+\.?\d*)', lower)
        if side:
            return f"cube(side={side.group(1)})"
    
    # Sphere detection
    if 'sphere' in lower:
        radius = re.search(r'(?:radius|r)\s*=?\s*(\d+\.?\d*)', lower)
        if radius:
            return f"sphere(radius={radius.group(1)})"
    
    # If no pattern matched, return original input
    return user_input

def is_already_formatted(user_input, module_type):
    """
    Check if input is already in correct format
    Returns True if no parsing needed
    """
    lower = user_input.lower().strip()
    
    if module_type == 'geometry':
        # Check for function format: function_name(params)
        valid_functions = [
            'distance', 'midpoint', 'slope', 'line', 'area_triangle', 'collinear',
            'circle', 'tangent_length', 'pythagoras', 'triangle', 'centroid', 'circumcenter',
            'rectangle', 'square', 'circle_area', 'circle_circumference',
            'cube', 'cuboid', 'cylinder', 'cone', 'sphere', 'hemisphere'
        ]
        
        for func in valid_functions:
            if lower.startswith(func + '('):
                return True
        
        # Check for equation format (x^2 + y^2 = 25)
        if '=' in user_input and ('^' in user_input or '**' in user_input):
            return True
    
    elif module_type == 'algebra':
        # Algebra equations are typically already formatted
        if '=' in user_input:
            return True
    
    return False