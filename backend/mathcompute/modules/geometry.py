import sympy as sp
import numpy as np
from sympy.geometry import *
import re
import math

def process_geometry(latex_input):
    """
    Master geometry processor - FOCUSED ON VISUAL ESSENTIALS
    """
    try:
        text = latex_input.strip()
        geom_type = detect_geometry_type(text)
        
        if geom_type == 'coordinate':
            return process_coordinate_geometry(text)
        elif geom_type == 'circle':
            return process_circle(text)
        elif geom_type == 'triangle':
            return process_triangle(text)
        elif geom_type == 'mensuration_2d':
            return process_mensuration_2d(text)
        elif geom_type == 'solid_3d':
            return process_solid_3d(text)
        elif geom_type == 'equation':
            return process_geometry_equation(text)
        else:
            raise Exception(f"Could not detect geometry type for: {text}")
    
    except Exception as e:
        raise Exception(f"Geometry processing error: {str(e)}")

def detect_geometry_type(text):
    """Detect geometry problem type"""
    lower = text.lower()
    
    # 3D Solids
    if any(kw in lower for kw in ['cube', 'cuboid', 'cylinder', 'cone', 'sphere', 'hemisphere']):
        return 'solid_3d'
    
    # 2D Mensuration
    if any(kw in lower for kw in ['rectangle', 'square', 'circle_area', 'circle_circumference']):
        return 'mensuration_2d'
    
    # Circles
    if any(kw in lower for kw in ['circle', 'tangent', 'chord', 'radius']):
        return 'circle'
    
    # Triangles
    if any(kw in lower for kw in ['triangle', 'pythagoras', 'centroid', 'circumcenter', 'incenter', 'orthocenter']):
        return 'triangle'
    
    # Coordinate Geometry
    if any(kw in lower for kw in ['distance', 'midpoint', 'slope', 'line', 'area_triangle', 'collinear']):
        return 'coordinate'
    
    # Equation format
    if '=' in text and ('x' in lower or 'y' in lower):
        return 'equation'
    
    return 'unknown'

def parse_points(text):
    """Extract coordinate points"""
    pattern = r'\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)'
    matches = re.findall(pattern, text)
    return [(float(x), float(y)) for x, y in matches]

def extract_number(text, param):
    """Extract numeric parameter"""
    match = re.search(f'{param}=(-?\d+\.?\d*)', text.lower())
    return float(match.group(1)) if match else None

# ============================================
# 1. COORDINATE GEOMETRY (Essential)
# ============================================

def process_coordinate_geometry(text):
    """Process coordinate geometry"""
    lower = text.lower()
    
    if 'distance(' in lower:
        return calc_distance(text)
    elif 'midpoint(' in lower:
        return calc_midpoint(text)
    elif 'slope(' in lower:
        return calc_slope(text)
    elif 'line(' in lower:
        return calc_line_equation(text)
    elif 'area_triangle(' in lower:
        return calc_triangle_area(text)
    elif 'collinear(' in lower:
        return check_collinear(text)
    else:
        raise Exception("Unknown coordinate operation")

def calc_distance(text):
    """Distance between two points"""
    points = parse_points(text)
    if len(points) < 2:
        raise Exception("Need 2 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'distance',
        'point1': [x1, y1],
        'point2': [x2, y2],
        'distance': round(dist, 4),
        'formula': '√[(x₂-x₁)² + (y₂-y₁)²]',
        'plot_data': {
            'type': 'distance',
            'points': [[x1, y1], [x2, y2]],
            'line': [[x1, x2], [y1, y2]]
        },
        'latex': {
            'formula': r'd = \sqrt{(x_2-x_1)^2 + (y_2-y_1)^2}',
            'result': f'd = {round(dist, 4)}'
        }
    }

def calc_midpoint(text):
    """Midpoint of line segment"""
    points = parse_points(text)
    if len(points) < 2:
        raise Exception("Need 2 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'midpoint',
        'point1': [x1, y1],
        'point2': [x2, y2],
        'midpoint': [round(mx, 4), round(my, 4)],
        'formula': '((x₁+x₂)/2, (y₁+y₂)/2)',
        'plot_data': {
            'type': 'midpoint',
            'points': [[x1, y1], [x2, y2]],
            'midpoint': [mx, my],
            'line': [[x1, x2], [y1, y2]]
        },
        'latex': {
            'formula': r'M = \left(\frac{x_1+x_2}{2}, \frac{y_1+y_2}{2}\right)',
            'result': f'M = ({round(mx, 4)}, {round(my, 4)})'
        }
    }

def calc_slope(text):
    """Slope of line"""
    points = parse_points(text)
    if len(points) < 2:
        raise Exception("Need 2 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    
    if x2 == x1:
        slope = 'undefined'
        slope_num = None
    else:
        slope_num = (y2 - y1) / (x2 - x1)
        slope = round(slope_num, 4)
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'slope',
        'point1': [x1, y1],
        'point2': [x2, y2],
        'slope': slope,
        'formula': '(y₂-y₁)/(x₂-x₁)',
        'plot_data': {
            'type': 'line',
            'points': [[x1, y1], [x2, y2]],
            'line': [[x1, x2], [y1, y2]]
        },
        'latex': {
            'formula': r'm = \frac{y_2-y_1}{x_2-x_1}',
            'result': f'm = {slope}'
        }
    }

def calc_line_equation(text):
    """Equation of line"""
    points = parse_points(text)
    if len(points) < 2:
        raise Exception("Need 2 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    
    if x2 == x1:
        equation = f'x = {x1}'
        x_vals = [x1] * 100
        y_vals = np.linspace(y1-5, y2+5, 100).tolist()
    else:
        m = (y2 - y1) / (x2 - x1)
        c = y1 - m*x1
        equation = f'y = {round(m,2)}x + {round(c,2)}'
        x_vals = np.linspace(x1-5, x2+5, 100)
        y_vals = (m*x_vals + c).tolist()
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'line_equation',
        'point1': [x1, y1],
        'point2': [x2, y2],
        'equation': equation,
        'plot_data': {
            'type': 'line_plot',
            'x': x_vals if isinstance(x_vals, list) else x_vals.tolist(),
            'y': y_vals,
            'points': [[x1, y1], [x2, y2]]
        },
        'latex': {
            'equation': equation
        }
    }

def calc_triangle_area(text):
    """Area of triangle using coordinates"""
    points = parse_points(text)
    if len(points) < 3:
        raise Exception("Need 3 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    
    area = 0.5 * abs(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'triangle_area',
        'vertices': [[x1, y1], [x2, y2], [x3, y3]],
        'area': round(area, 4),
        'formula': '½|x₁(y₂-y₃) + x₂(y₃-y₁) + x₃(y₁-y₂)|',
        'plot_data': {
            'type': 'triangle',
            'vertices': [[x1, y1], [x2, y2], [x3, y3]],
            'polygon': [[x1, x2, x3, x1], [y1, y2, y3, y1]]
        },
        'latex': {
            'formula': r'A = \frac{1}{2}|x_1(y_2-y_3) + x_2(y_3-y_1) + x_3(y_1-y_2)|',
            'result': f'A = {round(area, 4)}'
        }
    }

def check_collinear(text):
    """Check if three points are collinear"""
    points = parse_points(text)
    if len(points) < 3:
        raise Exception("Need 3 points")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    
    area = 0.5 * abs(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    is_collinear = abs(area) < 1e-6
    
    return {
        'type': 'coordinate_geometry',
        'operation': 'collinearity',
        'points': [[x1, y1], [x2, y2], [x3, y3]],
        'is_collinear': is_collinear,
        'area': round(area, 6),
        'result': 'Collinear (lie on same line)' if is_collinear else 'NOT collinear',
        'plot_data': {
            'type': 'collinear',
            'points': [[x1, y1], [x2, y2], [x3, y3]],
            'line': [[x1, x2, x3], [y1, y2, y3]] if is_collinear else None
        },
        'latex': {
            'result': f'Collinear: {"Yes" if is_collinear else "No"}'
        }
    }

# ============================================
# 2. CIRCLES
# ============================================

def process_circle(text):
    """Process circle problems"""
    lower = text.lower()
    
    # Check for tangent_length function
    if 'tangent_length(' in lower:
        return calc_tangent_length(text)
    
    # Check for circle construction
    if 'circle(' in lower and 'center=' in lower:
        return create_circle(text)
    
    # Otherwise treat as equation
    return process_geometry_equation(text)

def create_circle(text):
    """Create circle from center and radius"""
    center_match = re.search(r'center=\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', text.lower())
    radius = extract_number(text, 'radius')
    
    if not center_match or radius is None:
        raise Exception("Need center=(x,y) and radius=r")
    
    h = float(center_match.group(1))
    k = float(center_match.group(2))
    r = radius
    
    # Generate circle points
    theta = np.linspace(0, 2*np.pi, 100)
    x_circle = h + r * np.cos(theta)
    y_circle = k + r * np.sin(theta)
    
    # Calculate properties
    area = math.pi * r**2
    circumference = 2 * math.pi * r
    
    return {
        'type': 'circle',
        'operation': 'circle_construction',
        'center': [h, k],
        'radius': r,
        'area': round(area, 4),
        'circumference': round(circumference, 4),
        'equation': f'(x-{h})² + (y-{k})² = {r**2}',
        'plot_data': {
            'type': 'circle',
            'x': x_circle.tolist(),
            'y': y_circle.tolist(),
            'center': [h, k],
            'radius': r
        },
        'latex': {
            'equation': f'(x-{h})^2 + (y-{k})^2 = {r**2}',
            'area': f'A = \\pi r^2 = {round(area, 4)}',
            'circumference': f'C = 2\\pi r = {round(circumference, 4)}'
        }
    }

def calc_tangent_length(text):
    """Tangent length from external point to circle"""
    center_match = re.search(r'center=\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', text.lower())
    point_match = re.search(r'point=\((-?\d+\.?\d*),\s*(-?\d+\.?\d*)\)', text.lower())
    radius = extract_number(text, 'radius')
    
    if not center_match or not point_match or radius is None:
        raise Exception("Need center=(x,y), radius=r, and point=(x,y)")
    
    cx, cy = float(center_match.group(1)), float(center_match.group(2))
    px, py = float(point_match.group(1)), float(point_match.group(2))
    r = radius
    
    # Distance from center to point
    d = math.sqrt((px-cx)**2 + (py-cy)**2)
    
    # Tangent length: L = √(d² - r²)
    if d < r:
        raise Exception("Point is inside circle - no tangent")
    
    tangent_len = math.sqrt(d**2 - r**2)
    
    # Generate circle
    theta = np.linspace(0, 2*np.pi, 100)
    x_circle = cx + r * np.cos(theta)
    y_circle = cy + r * np.sin(theta)
    
    return {
        'type': 'circle',
        'operation': 'tangent_length',
        'center': [cx, cy],
        'radius': r,
        'external_point': [px, py],
        'tangent_length': round(tangent_len, 4),
        'formula': 'L = √(d² - r²)',
        'plot_data': {
            'type': 'circle_tangent',
            'circle': {'x': x_circle.tolist(), 'y': y_circle.tolist()},
            'center': [cx, cy],
            'point': [px, py]
        },
        'latex': {
            'formula': r'L = \sqrt{d^2 - r^2}',
            'result': f'L = {round(tangent_len, 4)}'
        }
    }

# ============================================
# 3. TRIANGLES
# ============================================

def process_triangle(text):
    """Process triangle problems"""
    lower = text.lower()
    
    if 'pythagoras(' in lower:
        return calc_pythagoras(text)
    elif 'centroid(' in lower:
        return calc_centroid_triangle(text)
    elif 'circumcenter(' in lower:
        return calc_circumcenter(text)
    elif 'triangle(' in lower:
        return create_triangle(text)
    else:
        raise Exception("Unknown triangle operation")

def calc_pythagoras(text):
    """Pythagoras theorem"""
    a = extract_number(text, 'a')
    b = extract_number(text, 'b')
    c = extract_number(text, 'c')
    
    if a and b:
        c = math.sqrt(a**2 + b**2)
        unknown = 'c'
    elif a and c:
        b = math.sqrt(c**2 - a**2)
        unknown = 'b'
    elif b and c:
        a = math.sqrt(c**2 - b**2)
        unknown = 'a'
    else:
        raise Exception("Need any 2 of a, b, c")
    
    # Draw right triangle
    vertices = [[0, 0], [a, 0], [a, b]]
    
    return {
        'type': 'triangle',
        'operation': 'pythagoras',
        'sides': {'a': round(a, 4), 'b': round(b, 4), 'c': round(c, 4)},
        'unknown': unknown,
        'theorem': 'a² + b² = c²',
        'plot_data': {
            'type': 'right_triangle',
            'vertices': vertices,
            'polygon': [[0, a, a, 0], [0, 0, b, 0]]
        },
        'latex': {
            'formula': r'a^2 + b^2 = c^2',
            'result': f'{unknown} = {round(eval(unknown), 4)}'
        }
    }

def create_triangle(text):
    """Create and analyze triangle"""
    points = parse_points(text)
    if len(points) < 3:
        raise Exception("Need 3 vertices")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    
    # Side lengths
    a = math.sqrt((x2-x3)**2 + (y2-y3)**2)
    b = math.sqrt((x1-x3)**2 + (y1-y3)**2)
    c = math.sqrt((x1-x2)**2 + (y1-y2)**2)
    
    # Type
    sides = sorted([a, b, c])
    if abs(sides[0] - sides[1]) < 1e-6 and abs(sides[1] - sides[2]) < 1e-6:
        tri_type = 'Equilateral'
    elif abs(sides[0] - sides[1]) < 1e-6 or abs(sides[1] - sides[2]) < 1e-6:
        tri_type = 'Isosceles'
    elif abs(sides[0]**2 + sides[1]**2 - sides[2]**2) < 1e-6:
        tri_type = 'Right-angled'
    else:
        tri_type = 'Scalene'
    
    # Area
    area = 0.5 * abs(x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    perimeter = a + b + c
    
    return {
        'type': 'triangle',
        'operation': 'triangle_analysis',
        'vertices': [[x1, y1], [x2, y2], [x3, y3]],
        'triangle_type': tri_type,
        'sides': {'a': round(a, 4), 'b': round(b, 4), 'c': round(c, 4)},
        'area': round(area, 4),
        'perimeter': round(perimeter, 4),
        'plot_data': {
            'type': 'triangle',
            'vertices': [[x1, y1], [x2, y2], [x3, y3]],
            'polygon': [[x1, x2, x3, x1], [y1, y2, y3, y1]]
        },
        'latex': {
            'type': tri_type,
            'area': f'A = {round(area, 4)}',
            'perimeter': f'P = {round(perimeter, 4)}'
        }
    }

def calc_centroid_triangle(text):
    """Centroid of triangle"""
    points = parse_points(text)
    if len(points) < 3:
        raise Exception("Need 3 vertices")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    
    cx = (x1 + x2 + x3) / 3
    cy = (y1 + y2 + y3) / 3
    
    return {
        'type': 'triangle',
        'operation': 'centroid',
        'vertices': [[x1, y1], [x2, y2], [x3, y3]],
        'centroid': [round(cx, 4), round(cy, 4)],
        'formula': '((x₁+x₂+x₃)/3, (y₁+y₂+y₃)/3)',
        'plot_data': {
            'type': 'triangle_centroid',
            'vertices': [[x1, y1], [x2, y2], [x3, y3]],
            'polygon': [[x1, x2, x3, x1], [y1, y2, y3, y1]],
            'centroid': [cx, cy]
        },
        'latex': {
            'formula': r'G = \left(\frac{x_1+x_2+x_3}{3}, \frac{y_1+y_2+y_3}{3}\right)',
            'result': f'G = ({round(cx, 4)}, {round(cy, 4)})'
        }
    }

def calc_circumcenter(text):
    """Circumcenter of triangle"""
    points = parse_points(text)
    if len(points) < 3:
        raise Exception("Need 3 vertices")
    
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    
    # Circumcenter formulas
    D = 2 * (x1*(y2-y3) + x2*(y3-y1) + x3*(y1-y2))
    
    if abs(D) < 1e-10:
        raise Exception("Points are collinear - no circumcenter")
    
    ux = ((x1**2 + y1**2)*(y2-y3) + (x2**2 + y2**2)*(y3-y1) + (x3**2 + y3**2)*(y1-y2)) / D
    uy = ((x1**2 + y1**2)*(x3-x2) + (x2**2 + y2**2)*(x1-x3) + (x3**2 + y3**2)*(x2-x1)) / D
    
    # Circumradius
    R = math.sqrt((x1-ux)**2 + (y1-uy)**2)
    
    # Generate circumcircle
    theta = np.linspace(0, 2*np.pi, 100)
    x_circle = ux + R * np.cos(theta)
    y_circle = uy + R * np.sin(theta)
    
    return {
        'type': 'triangle',
        'operation': 'circumcenter',
        'vertices': [[x1, y1], [x2, y2], [x3, y3]],
        'circumcenter': [round(ux, 4), round(uy, 4)],
        'circumradius': round(R, 4),
        'plot_data': {
            'type': 'triangle_circumcircle',
            'vertices': [[x1, y1], [x2, y2], [x3, y3]],
            'polygon': [[x1, x2, x3, x1], [y1, y2, y3, y1]],
            'circumcenter': [ux, uy],
            'circle': {'x': x_circle.tolist(), 'y': y_circle.tolist()}
        },
        'latex': {
            'result': f'O = ({round(ux, 4)}, {round(uy, 4)}), R = {round(R, 4)}'
        }
    }

# ============================================
# 4. MENSURATION 2D
# ============================================

def process_mensuration_2d(text):
    """Process 2D mensuration"""
    lower = text.lower()
    
    if 'rectangle(' in lower:
        return calc_rectangle(text)
    elif 'square(' in lower:
        return calc_square(text)
    elif 'circle_area(' in lower:
        return calc_circle_area(text)
    elif 'circle_circumference(' in lower:
        return calc_circle_circumference(text)
    else:
        raise Exception("Unknown mensuration operation")

def calc_rectangle(text):
    """Rectangle area and perimeter"""
    length = extract_number(text, 'length')
    width = extract_number(text, 'width')
    
    if not length or not width:
        raise Exception("Need length and width")
    
    area = length * width
    perimeter = 2 * (length + width)
    
    return {
        'type': 'mensuration_2d',
        'shape': 'rectangle',
        'length': length,
        'width': width,
        'area': round(area, 4),
        'perimeter': round(perimeter, 4),
        'plot_data': {
            'type': 'rectangle',
            'vertices': [[0, 0], [length, 0], [length, width], [0, width]]
        },
        'latex': {
            'area': f'A = l \\times w = {round(area, 4)}',
            'perimeter': f'P = 2(l + w) = {round(perimeter, 4)}'
        }
    }

def calc_square(text):
    """Square area and perimeter"""
    side = extract_number(text, 'side')
    
    if not side:
        raise Exception("Need side length")
    
    area = side ** 2
    perimeter = 4 * side
    
    return {
        'type': 'mensuration_2d',
        'shape': 'square',
        'side': side,
        'area': round(area, 4),
        'perimeter': round(perimeter, 4),
        'plot_data': {
            'type': 'square',
            'vertices': [[0, 0], [side, 0], [side, side], [0, side]]
        },
        'latex': {
            'area': f'A = s^2 = {round(area, 4)}',
            'perimeter': f'P = 4s = {round(perimeter, 4)}'
        }
    }

def calc_circle_area(text):
    """Circle area"""
    radius = extract_number(text, 'radius')
    
    if not radius:
        raise Exception("Need radius")
    
    area = math.pi * radius**2
    
    # Generate circle
    theta = np.linspace(0, 2*np.pi, 100)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    
    return {
        'type': 'mensuration_2d',
        'shape': 'circle',
        'radius': radius,
        'area': round(area, 4),
        'plot_data': {
            'type': 'circle_filled',
            'x': x.tolist(),
            'y': y.tolist()
        },
        'latex': {
            'area': f'A = \\pi r^2 = {round(area, 4)}'
        }
    }

def calc_circle_circumference(text):
    """Circle circumference"""
    radius = extract_number(text, 'radius')
    
    if not radius:
        raise Exception("Need radius")
    
    circumference = 2 * math.pi * radius
    
    # Generate circle
    theta = np.linspace(0, 2*np.pi, 100)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    
    return {
        'type': 'mensuration_2d',
        'shape': 'circle',
        'radius': radius,
        'circumference': round(circumference, 4),
        'plot_data': {
            'type': 'circle',
            'x': x.tolist(),
            'y': y.tolist()
        },
        'latex': {
            'circumference': f'C = 2\\pi r = {round(circumference, 4)}'
        }
    }

# ============================================
# 5. 3D SOLIDS
# ============================================

def process_solid_3d(text):
    """Process 3D solids"""
    lower = text.lower()
    
    if 'cube(' in lower:
        return calc_cube(text)
    elif 'cuboid(' in lower:
        return calc_cuboid(text)
    elif 'cylinder(' in lower:
        return calc_cylinder(text)
    elif 'cone(' in lower:
        return calc_cone(text)
    elif 'sphere(' in lower:
        return calc_sphere(text)
    elif 'hemisphere(' in lower:
        return calc_hemisphere(text)
    else:
        raise Exception("Unknown 3D solid")

def calc_cube(text):
    """Cube calculations"""
    side = extract_number(text, 'side')
    if not side:
        raise Exception("Need side length")
    
    surface_area = 6 * side**2
    volume = side**3
    
    # 3D vertices for cube
    vertices = [
        [0, 0, 0], [side, 0, 0], [side, side, 0], [0, side, 0],  # bottom
        [0, 0, side], [side, 0, side], [side, side, side], [0, side, side]  # top
    ]
    
    return {
        'type': 'solid_3d',
        'shape': 'cube',
        'side': side,
        'surface_area': round(surface_area, 4),
        'volume': round(volume, 4),
        'formulas': {
            'surface_area': '6a²',
            'volume': 'a³'
        },
        'plot_data': {
            'type': 'cube_3d',
            'vertices': vertices,
            'side': side
        },
        'latex': {
            'surface_area': f'SA = 6a^2 = {round(surface_area, 4)}',
            'volume': f'V = a^3 = {round(volume, 4)}'
        }
    }

def calc_cuboid(text):
    """Cuboid calculations"""
    length = extract_number(text, 'length')
    width = extract_number(text, 'width')
    height = extract_number(text, 'height')
    
    if not all([length, width, height]):
        raise Exception("Need length, width, and height")
    
    surface_area = 2 * (length*width + width*height + height*length)
    volume = length * width * height
    
    vertices = [
        [0, 0, 0], [length, 0, 0], [length, width, 0], [0, width, 0],
        [0, 0, height], [length, 0, height], [length, width, height], [0, width, height]
    ]
    
    return {
        'type': 'solid_3d',
        'shape': 'cuboid',
        'dimensions': {'length': length, 'width': width, 'height': height},
        'surface_area': round(surface_area, 4),
        'volume': round(volume, 4),
        'formulas': {
            'surface_area': '2(lw + wh + hl)',
            'volume': 'lwh'
        },
        'plot_data': {
            'type': 'cuboid_3d',
            'vertices': vertices,
            'dimensions': [length, width, height]
        },
        'latex': {
            'surface_area': f'SA = 2(lw + wh + hl) = {round(surface_area, 4)}',
            'volume': f'V = lwh = {round(volume, 4)}'
        }
    }

def calc_cylinder(text):
    """Cylinder calculations"""
    radius = extract_number(text, 'radius')
    height = extract_number(text, 'height')
    
    if not radius or not height:
        raise Exception("Need radius and height")
    
    curved_surface = 2 * math.pi * radius * height
    total_surface = 2 * math.pi * radius * (radius + height)
    volume = math.pi * radius**2 * height
    
    # Generate cylinder mesh
    theta = np.linspace(0, 2*np.pi, 30)
    z = np.linspace(0, height, 30)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x = radius * np.cos(theta_grid)
    y = radius * np.sin(theta_grid)
    
    return {
        'type': 'solid_3d',
        'shape': 'cylinder',
        'radius': radius,
        'height': height,
        'curved_surface_area': round(curved_surface, 4),
        'total_surface_area': round(total_surface, 4),
        'volume': round(volume, 4),
        'formulas': {
            'curved_surface': '2πrh',
            'total_surface': '2πr(r+h)',
            'volume': 'πr²h'
        },
        'plot_data': {
            'type': 'cylinder_3d',
            'x': x.tolist(),
            'y': y.tolist(),
            'z': z_grid.tolist(),
            'radius': radius,
            'height': height
        },
        'latex': {
            'curved_surface': f'CSA = 2\\pi rh = {round(curved_surface, 4)}',
            'total_surface': f'TSA = 2\\pi r(r+h) = {round(total_surface, 4)}',
            'volume': f'V = \\pi r^2h = {round(volume, 4)}'
        }
    }

def calc_cone(text):
    """Cone calculations"""
    radius = extract_number(text, 'radius')
    height = extract_number(text, 'height')
    slant = extract_number(text, 'slant_height')
    
    if radius and height:
        slant = math.sqrt(radius**2 + height**2)
    elif radius and slant:
        height = math.sqrt(slant**2 - radius**2)
    elif height and slant:
        radius = math.sqrt(slant**2 - height**2)
    else:
        raise Exception("Need any 2 of: radius, height, slant_height")
    
    curved_surface = math.pi * radius * slant
    total_surface = math.pi * radius * (radius + slant)
    volume = (1/3) * math.pi * radius**2 * height
    
    # Generate cone mesh
    theta = np.linspace(0, 2*np.pi, 30)
    z = np.linspace(0, height, 30)
    theta_grid, z_grid = np.meshgrid(theta, z)
    r = radius * (1 - z_grid/height)
    x = r * np.cos(theta_grid)
    y = r * np.sin(theta_grid)
    
    return {
        'type': 'solid_3d',
        'shape': 'cone',
        'radius': round(radius, 4),
        'height': round(height, 4),
        'slant_height': round(slant, 4),
        'curved_surface_area': round(curved_surface, 4),
        'total_surface_area': round(total_surface, 4),
        'volume': round(volume, 4),
        'formulas': {
            'curved_surface': 'πrl',
            'total_surface': 'πr(r+l)',
            'volume': '⅓πr²h'
        },
        'plot_data': {
            'type': 'cone_3d',
            'x': x.tolist(),
            'y': y.tolist(),
            'z': z_grid.tolist(),
            'radius': radius,
            'height': height
        },
        'latex': {
            'curved_surface': f'CSA = \\pi rl = {round(curved_surface, 4)}',
            'total_surface': f'TSA = \\pi r(r+l) = {round(total_surface, 4)}',
            'volume': f'V = \\frac{1}{3}\\pi r^2h = {round(volume, 4)}'
        }
    }

def calc_sphere(text):
    """Sphere calculations"""
    radius = extract_number(text, 'radius')
    if not radius:
        raise Exception("Need radius")
    
    surface_area = 4 * math.pi * radius**2
    volume = (4/3) * math.pi * radius**3
    
    # Generate sphere mesh
    phi = np.linspace(0, np.pi, 30)
    theta = np.linspace(0, 2*np.pi, 30)
    phi_grid, theta_grid = np.meshgrid(phi, theta)
    x = radius * np.sin(phi_grid) * np.cos(theta_grid)
    y = radius * np.sin(phi_grid) * np.sin(theta_grid)
    z = radius * np.cos(phi_grid)
    
    return {
        'type': 'solid_3d',
        'shape': 'sphere',
        'radius': radius,
        'surface_area': round(surface_area, 4),
        'volume': round(volume, 4),
        'formulas': {
            'surface_area': '4πr²',
            'volume': '⁴⁄₃πr³'
        },
        'plot_data': {
            'type': 'sphere_3d',
            'x': x.tolist(),
            'y': y.tolist(),
            'z': z.tolist(),
            'radius': radius
        },
        'latex': {
            'surface_area': f'SA = 4\\pi r^2 = {round(surface_area, 4)}',
            'volume': f'V = \\frac{4}{3}\\pi r^3 = {round(volume, 4)}'
        }
    }

def calc_hemisphere(text):
    """Hemisphere calculations"""
    radius = extract_number(text, 'radius')
    if not radius:
        raise Exception("Need radius")
    
    curved_surface = 2 * math.pi * radius**2
    total_surface = 3 * math.pi * radius**2
    volume = (2/3) * math.pi * radius**3
    
    # Generate hemisphere mesh
    phi = np.linspace(0, np.pi/2, 30)
    theta = np.linspace(0, 2*np.pi, 30)
    phi_grid, theta_grid = np.meshgrid(phi, theta)
    x = radius * np.sin(phi_grid) * np.cos(theta_grid)
    y = radius * np.sin(phi_grid) * np.sin(theta_grid)
    z = radius * np.cos(phi_grid)
    
    return {
        'type': 'solid_3d',
        'shape': 'hemisphere',
        'radius': radius,
        'curved_surface_area': round(curved_surface, 4),
        'total_surface_area': round(total_surface, 4),
        'volume': round(volume, 4),
        'formulas': {
            'curved_surface': '2πr²',
            'total_surface': '3πr²',
            'volume': '⅔πr³'
        },
        'plot_data': {
            'type': 'hemisphere_3d',
            'x': x.tolist(),
            'y': y.tolist(),
            'z': z.tolist(),
            'radius': radius
        },
        'latex': {
            'curved_surface': f'CSA = 2\\pi r^2 = {round(curved_surface, 4)}',
            'total_surface': f'TSA = 3\\pi r^2 = {round(total_surface, 4)}',
            'volume': f'V = \\frac{2}{3}\\pi r^3 = {round(volume, 4)}'
        }
    }

# ============================================
# 6. GEOMETRY EQUATIONS (x^2 + y^2 = 25)
# ============================================

def process_geometry_equation(text):
    """Process geometry equations like x^2 + y^2 = 25"""
    try:
        x, y = sp.symbols('x y')
        
        # Parse equation
        if '=' in text:
            parts = text.split('=')
            lhs = parse_expr(parts[0].strip(), x, y)
            rhs = parse_expr(parts[1].strip(), x, y)
            expr = lhs - rhs
        else:
            expr = parse_expr(text, x, y)
        
        # Detect shape
        shape_type = 'unknown'
        properties = {}
        
        # Circle detection
        if expr.has(x**2) and expr.has(y**2):
            expanded = sp.expand(expr)
            x2_coeff = expanded.coeff(x**2)
            y2_coeff = expanded.coeff(y**2)
            
            if abs(x2_coeff - y2_coeff) < 1e-10:
                shape_type = 'circle'
                
                # Extract center and radius
                x_coeff = expanded.coeff(x, 1)
                y_coeff = expanded.coeff(y, 1)
                constant = expanded.as_coefficients_dict()[1]
                
                h = -x_coeff / (2 * x2_coeff)
                k = -y_coeff / (2 * y2_coeff)
                r_squared = h**2 + k**2 - constant/x2_coeff
                
                if r_squared > 0:
                    r = float(sp.sqrt(r_squared))
                    properties = {
                        'center': [float(h), float(k)],
                        'radius': r,
                        'area': round(math.pi * r**2, 4),
                        'circumference': round(2 * math.pi * r, 4)
                    }
                    
                    # Generate points
                    theta = np.linspace(0, 2*np.pi, 100)
                    x_pts = float(h) + r * np.cos(theta)
                    y_pts = float(k) + r * np.sin(theta)
                    
                    plot_data = {
                        'type': 'circle',
                        'x': x_pts.tolist(),
                        'y': y_pts.tolist(),
                        'center': [float(h), float(k)]
                    }
            else:
                shape_type = 'ellipse'
                plot_data = generate_implicit_plot(expr, x, y)
        
        # Line detection
        elif expr.as_poly(x, y) and expr.as_poly(x, y).degree() == 1:
            shape_type = 'line'
            
            # Solve for y
            y_expr = sp.solve(expr, y)[0]
            x_vals = np.linspace(-10, 10, 100)
            f = sp.lambdify(x, y_expr, 'numpy')
            y_vals = f(x_vals)
            
            plot_data = {
                'type': 'line',
                'x': x_vals.tolist(),
                'y': y_vals.tolist()
            }
            
            slope = sp.diff(y_expr, x)
            intercept = y_expr.subs(x, 0)
            properties = {
                'slope': float(slope),
                'y_intercept': float(intercept)
            }
        
        else:
            # General curve
            plot_data = generate_implicit_plot(expr, x, y)
        
        return {
            'type': 'geometry_equation',
            'shape_type': shape_type,
            'equation': str(expr),
            'properties': properties,
            'plot_data': plot_data,
            'latex': {
                'equation': sp.latex(expr) + ' = 0'
            }
        }
    
    except Exception as e:
        raise Exception(f"Equation processing error: {str(e)}")

def parse_expr(text, x, y):
    """Parse expression with geometry notation"""
    text = text.replace('\\', '')
    text = text.replace('{', '').replace('}', '')
    text = text.replace('^', '**')
    text = re.sub(r'(\d)([xy])', r'\1*\2', text)
    text = text.replace('xy', 'x*y')
    text = re.sub(r'\)([xy])', r')*\1', text)
    text = re.sub(r'([xy])\(', r'\1*(', text)
    
    return sp.sympify(text)

def generate_implicit_plot(expr, x, y, x_range=(-10, 10), y_range=(-10, 10), points=50):
    """Generate implicit plot"""
    x_vals = np.linspace(x_range[0], x_range[1], points)
    y_vals = np.linspace(y_range[0], y_range[1], points)
    X, Y = np.meshgrid(x_vals, y_vals)
    
    f = sp.lambdify((x, y), expr, 'numpy')
    
    try:
        Z = f(X, Y)
        return {
            'type': 'contour',
            'x': X.tolist(),
            'y': Y.tolist(),
            'z': Z.tolist()
        }
    except:
        return {
            'type': 'empty',
            'x': [],
            'y': []
        }