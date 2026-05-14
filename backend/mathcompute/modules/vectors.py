import sympy as sp
import numpy as np
from sympy.vector import CoordSys3D

def process_vectors(latex_input):
    """
    Process 3D vectors: operations, visualization
    
    Examples:
    - "3i + 2j + k" or "3\\hat{i} + 2\\hat{j} + \\hat{k}"
    - "[1, 2, 3]"
    - "\\vec{v} = 2i + 3j + 4k"
    """
    try:
        # Parse vector input
        # Handle different formats
        vector_components = parse_vector_input(latex_input)
        
        if len(vector_components) == 1:
            # Single vector - just visualize it
            v = np.array(vector_components[0])
            
            result = {
                'type': 'vector_single',
                'vector': v.tolist(),
                'magnitude': float(np.linalg.norm(v)),
                'unit_vector': (v / np.linalg.norm(v)).tolist() if np.linalg.norm(v) != 0 else [0, 0, 0],
                'plot_data': {
                    'vectors': [{
                        'origin': [0, 0, 0],
                        'vector': v.tolist(),
                        'label': 'v'
                    }]
                }
            }
        
        elif len(vector_components) == 2:
            # Two vectors - show dot product, cross product
            v1 = np.array(vector_components[0])
            v2 = np.array(vector_components[1])
            
            dot_product = np.dot(v1, v2)
            cross_product = np.cross(v1, v2)
            
            # Angle between vectors
            cos_angle = dot_product / (np.linalg.norm(v1) * np.linalg.norm(v2))
            angle_rad = np.arccos(np.clip(cos_angle, -1, 1))
            angle_deg = np.degrees(angle_rad)
            
            result = {
                'type': 'vector_pair',
                'vector1': v1.tolist(),
                'vector2': v2.tolist(),
                'dot_product': float(dot_product),
                'cross_product': cross_product.tolist(),
                'angle_degrees': float(angle_deg),
                'angle_radians': float(angle_rad),
                'plot_data': {
                    'vectors': [
                        {
                            'origin': [0, 0, 0],
                            'vector': v1.tolist(),
                            'label': 'v₁',
                            'color': 'blue'
                        },
                        {
                            'origin': [0, 0, 0],
                            'vector': v2.tolist(),
                            'label': 'v₂',
                            'color': 'red'
                        },
                        {
                            'origin': [0, 0, 0],
                            'vector': cross_product.tolist(),
                            'label': 'v₁ × v₂',
                            'color': 'green'
                        }
                    ]
                }
            }
        else:
            # Multiple vectors
            result = {
                'type': 'vector_multiple',
                'vectors': [v.tolist() for v in vector_components],
                'plot_data': {
                    'vectors': [
                        {
                            'origin': [0, 0, 0],
                            'vector': v.tolist(),
                            'label': f'v₍{i+1}₎'
                        } for i, v in enumerate(vector_components)
                    ]
                }
            }
        
        return result
    
    except Exception as e:
        raise Exception(f"Vector processing error: {str(e)}")

def parse_vector_input(latex_input):
    """
    Parse various vector input formats
    Returns list of numpy arrays
    """
    vectors = []
    
    # Clean input
    text = latex_input.replace('\\vec{v}', '').replace('=', '').strip()
    text = text.replace('\\hat{i}', 'i').replace('\\hat{j}', 'j').replace('\\hat{k}', 'k')
    text = text.replace('\\mathbf{i}', 'i').replace('\\mathbf{j}', 'j').replace('\\mathbf{k}', 'k')
    
    # Check for bracket notation [1, 2, 3]
    if '[' in text:
        import re
        matches = re.findall(r'\[([\d\s,.-]+)\]', text)
        for match in matches:
            components = [float(x.strip()) for x in match.split(',')]
            if len(components) == 3:
                vectors.append(components)
    
    # Check for i, j, k notation
    elif 'i' in text or 'j' in text or 'k' in text:
        # Split by semicolon or 'and' for multiple vectors
        parts = text.replace(' and ', ';').split(';')
        
        for part in parts:
            i_coeff = extract_coefficient(part, 'i')
            j_coeff = extract_coefficient(part, 'j')
            k_coeff = extract_coefficient(part, 'k')
            
            vectors.append([i_coeff, j_coeff, k_coeff])
    
    # Default: try to parse as comma-separated
    else:
        try:
            components = [float(x.strip()) for x in text.split(',')]
            if len(components) == 3:
                vectors.append(components)
        except:
            # Default vector
            vectors.append([1, 1, 1])
    
    return vectors

def extract_coefficient(text, var):
    """Extract coefficient of i, j, or k"""
    import re
    
    # Pattern: optional sign, optional number, then variable
    pattern = rf'([+-]?\s*\d*\.?\d*)\s*{var}'
    match = re.search(pattern, text)
    
    if match:
        coeff_str = match.group(1).replace(' ', '')
        if coeff_str in ['', '+']:
            return 1.0
        elif coeff_str == '-':
            return -1.0
        else:
            return float(coeff_str)
    return 0.0