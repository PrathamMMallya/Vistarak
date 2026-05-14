import sympy as sp
import numpy as np
from sympy import symbols, diff, integrate, limit, series, solve, oo
from sympy import sin, cos, tan, exp, log, sqrt, Abs, pi, factorial
import re
from calculus_ai_parser import normalize_calculus_with_ai

def sanitize_for_json(arr):
    """Convert numpy array to JSON-safe list (replace NaN/Inf with None)"""
    if isinstance(arr, np.ndarray):
        arr = arr.tolist()
    
    def clean_value(val):
        if isinstance(val, (list, tuple)):
            return [clean_value(v) for v in val]
        if isinstance(val, (np.integer, np.int32, np.int64)):
            return int(val)
        if isinstance(val, (np.floating, np.float32, np.float64)):
            if np.isnan(val) or np.isinf(val):
                return None
            return float(val)
        if isinstance(val, float):
            if np.isnan(val) or np.isinf(val):
                return None
        return val
    
    return clean_value(arr)

def process_calculus(latex_input):
    """
    ULTRA-COMPREHENSIVE Calculus Module with AI parsing AS FALLBACK
    
    STRATEGY:
    1. Try manual parsing first (our regex is already good!)
    2. Only use AI if manual parsing fails
    3. AI helps with weird formats our regex can't handle
    """
    try:
        print(f"\n{'='*60}")
        print(f"[CALCULUS] Processing: '{latex_input}'")
        print(f"{'='*60}")
        
        # STEP 1: Clean delimiters first (always needed)
        cleaned_input = clean_latex_delimiters(latex_input)
        print(f"[CALCULUS] After cleaning delimiters: '{cleaned_input}'")
        
        # STEP 2: Try MANUAL parsing first
        try:
            print("[CALCULUS] Attempting MANUAL parsing...")
            result = try_manual_parsing(cleaned_input)
            print("[CALCULUS] ✅ Manual parsing SUCCESS")
            return result
            
        except Exception as manual_error:
            print(f"[CALCULUS] ⚠️  Manual parsing failed: {manual_error}")
            print("[CALCULUS] Falling back to AI normalization...")
            
            # STEP 3: AI normalization as FALLBACK
            try:
                from calculus_ai_parser import normalize_calculus_with_ai
                
                normalized_input = normalize_calculus_with_ai(latex_input, operation_type="auto")
                print(f"[CALCULUS] AI normalized: '{normalized_input}'")
                
                # Try manual parsing again with AI-normalized input
                result = try_manual_parsing(normalized_input)
                print("[CALCULUS] ✅ AI normalization + Manual parsing SUCCESS")
                return result
                
            except Exception as ai_error:
                print(f"[CALCULUS] ❌ AI parsing also failed: {ai_error}")
                # Re-raise the original manual error (more informative)
                raise manual_error
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"CALCULUS PROCESSING ERROR")
        print(f"{'='*60}")
        print(f"Original Input: '{latex_input}'")
        print(f"Error: {str(e)}")
        print(f"\nFull Traceback:\n{error_details}")
        print(f"{'='*60}\n")
        raise Exception(f"Calculus error: {str(e)}")
    
def try_manual_parsing(latex_input):
    """
    Try manual parsing with all our regex patterns
    Throws exception if it can't parse
    """
    # Detect operation type and route
    if 'int_' in latex_input or '\\int_' in latex_input:
        return process_definite_integral(latex_input)
    elif 'lim_' in latex_input or '\\lim' in latex_input:
        return process_limit(latex_input)
    elif 'taylor' in latex_input.lower() or 'series' in latex_input.lower():
        return process_taylor_series(latex_input)
    elif 'partial' in latex_input.lower():
        return process_partial_derivative(latex_input)
    else:
        return process_standard_calculus(latex_input)

def clean_latex_delimiters(text):
    """Remove LaTeX delimiters - COMPLETELY FIXED"""
    # Remove display math delimiters
    text = text.replace('\\[', '').replace('\\]', '').replace('$$', '').strip()
    text = text.replace('\\(', '').replace('\\)', '')
    
    # CRITICAL: Remove \left and \right
    text = text.replace('\\left', '').replace('\\right', '')
    
    # Handle \begin{equation} ... \end{equation}
    # FIXED: Use case-insensitive and handle both with/without backslash
    text = re.sub(r'\\?begin\s*\{\s*equation\s*\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\?end\s*\{\s*equation\s*\}', '', text, flags=re.IGNORECASE)
    
    # Handle piecewise: \begin{cases}...\end{cases}
    if 'begin{cases}' in text or '\\begin{cases}' in text:
        # Extract first case only (before &)
        text = re.sub(r'\\?begin\{cases\}', '', text)
        text = re.sub(r'\\?end\{cases\}', '', text)
        if '&' in text:
            text = text.split('&')[0]
        if '\\\\' in text:
            text = text.split('\\\\')[0]
    
    # Remove any remaining \begin{...} and \end{...} patterns
    text = re.sub(r'\\?begin\s*\{[^}]*\}', '', text)
    text = re.sub(r'\\?end\s*\{[^}]*\}', '', text)
    
    # Clean up extra whitespace
    text = ' '.join(text.split()).strip()
    
    return text

def process_standard_calculus(latex_input):
    """Standard calculus - FIXED for all derivative notations"""
    x = sp.Symbol('x')
    
    # STEP 0: Detect and handle higher-order derivatives
    # Pattern: \frac{d^n}{dx^n} or \frac{d^n f}{dx^n}
    higher_deriv_pattern = r'\\?frac\{d\^(\d+)\s*f?\}\{dx\^(\d+)\}'
    higher_match = re.search(higher_deriv_pattern, latex_input)
    
    if higher_match:
        order = int(higher_match.group(1))
        # Remove the derivative notation completely
        func_str = re.sub(higher_deriv_pattern, '', latex_input)
        func_str = func_str.strip('()')
        print(f"Detected {order}-order derivative, extracted: '{func_str}'")
        
        # Parse and compute nth derivative
        expr = parse_expression(func_str)
        print(f"Parsed expression: {expr}")
        
        # Compute derivatives up to order n
        derivatives = [expr]
        for i in range(1, order + 1):
            derivatives.append(diff(derivatives[-1], x))
        
        f_prime = derivatives[1] if len(derivatives) > 1 else diff(expr, x)
        f_double_prime = derivatives[2] if len(derivatives) > 2 else diff(f_prime, x)
        f_triple = derivatives[3] if len(derivatives) > 3 else diff(f_double_prime, x)
        
        # Continue with standard analysis using original function
        try:
            integral = integrate(expr, x)
        except:
            integral = sp.Integral(expr, x)
        
        critical_pts = find_real_solutions(f_prime, x)
        inflection_pts = find_real_solutions(f_double_prime, x)
        
        classified = []
        for cp in critical_pts:
            try:
                val = float(f_double_prime.subs(x, cp))
                if val > 0.001:
                    classified.append({'point': float(cp), 'type': 'local minimum'})
                elif val < -0.001:
                    classified.append({'point': float(cp), 'type': 'local maximum'})
                else:
                    classified.append({'point': float(cp), 'type': 'inconclusive'})
            except:
                classified.append({'point': float(cp), 'type': 'inconclusive'})
        
        intervals = analyze_intervals(f_prime, f_double_prime, x, critical_pts, inflection_pts)
        plot_data = generate_advanced_plot(expr, f_prime, f_double_prime, x, critical_pts, inflection_pts)
        
        return {
            'type': 'calculus_standard',
            'original_function': str(expr),
            'derivative_1': str(f_prime),
            'derivative_2': str(f_double_prime),
            'derivative_3': str(f_triple),
            'integral': str(integral),
            'critical_points': [float(cp) for cp in critical_pts],
            'classified_points': classified,
            'inflection_points': [float(ip) for ip in inflection_pts],
            'interval_analysis': intervals,
            'plot_data': plot_data,
            'latex': {
                'function': sp.latex(expr),
                'derivative_1': sp.latex(f_prime),
                'derivative_2': sp.latex(f_double_prime),
                'integral': sp.latex(integral)
            }
        }
    
    # STEP 1: Handle first-order derivative notation
    if '\\frac{d}' in latex_input or 'frac{d}' in latex_input:
        # Remove derivative notation: \frac{d}{dx}, \frac{d}{dy}, etc.
        func_str = re.sub(r'\\?frac\{d\}\{d[a-z]\}', '', latex_input)
        # CRITICAL FIX: Handle equations properly
        if '=' in func_str:
            # Split and take left side (the function being differentiated)
            parts = func_str.split('=')
            func_str = parts[0].strip()
        # Remove parentheses around function if present
        func_str = clean_parentheses(func_str)
        print(f"Detected derivative notation, extracted function: '{func_str}'")
    else:
        # Clean input (original code)
        func_str = latex_input.replace('\\int', '').replace('int', '')
        func_str = func_str.replace('dx', '').replace('d x', '').replace('\\,', '').strip()
        
        # STEP 2: If equation with = sign, take LEFT side only (the function)
        if '=' in func_str:
            func_str = func_str.split('=')[0].strip()
            func_str = clean_parentheses(func_str)
            print(f"Detected equation, using LHS: '{func_str}'")
    
    print(f"Processing standard calculus: '{func_str}'")
    
    expr = parse_expression(func_str)
    print(f"Parsed expression: {expr}")
    
    # Derivatives
    f_prime = diff(expr, x)
    f_double_prime = diff(f_prime, x)
    f_triple = diff(f_double_prime, x)
    
    # Integral - wrap in try-catch for complex expressions
    try:
        integral = integrate(expr, x)
    except Exception as e:
        print(f"Warning: Could not compute integral: {e}")
        integral = sp.Integral(expr, x)
    
    # Critical points (f'(x) = 0)
    critical_pts = find_real_solutions(f_prime, x)
    
    # Inflection points (f''(x) = 0)
    inflection_pts = find_real_solutions(f_double_prime, x)
    
    # Classify critical points using second derivative test
    classified = []
    for cp in critical_pts:
        try:
            val = float(f_double_prime.subs(x, cp))
            if val > 0.001:
                classified.append({'point': float(cp), 'type': 'local minimum'})
            elif val < -0.001:
                classified.append({'point': float(cp), 'type': 'local maximum'})
            else:
                classified.append({'point': float(cp), 'type': 'inconclusive'})
        except:
            classified.append({'point': float(cp), 'type': 'inconclusive'})
    
    # Interval analysis
    intervals = analyze_intervals(f_prime, f_double_prime, x, critical_pts, inflection_pts)
    
    # Plot
    plot_data = generate_advanced_plot(expr, f_prime, f_double_prime, x, critical_pts, inflection_pts)
    
    return {
        'type': 'calculus_standard',
        'original_function': str(expr),
        'derivative_1': str(f_prime),
        'derivative_2': str(f_double_prime),
        'derivative_3': str(f_triple),
        'integral': str(integral),
        'critical_points': [float(cp) for cp in critical_pts],
        'classified_points': classified,
        'inflection_points': [float(ip) for ip in inflection_pts],
        'interval_analysis': intervals,
        'plot_data': plot_data,
        'latex': {
            'function': sp.latex(expr),
            'derivative_1': sp.latex(f_prime),
            'derivative_2': sp.latex(f_double_prime),
            'integral': sp.latex(integral)
        }
    }

def clean_parentheses(text):
    """Remove unmatched parentheses and clean up"""
    # Count parentheses
    open_count = text.count('(')
    close_count = text.count(')')
    
    # Remove trailing unmatched closing parentheses
    while close_count > open_count and text.endswith(')'):
        text = text[:-1]
        close_count -= 1
    
    # Remove leading unmatched opening parentheses
    while open_count > close_count and text.startswith('('):
        text = text[1:]
        open_count -= 1
    
    # If wrapped in matching parens, remove them
    if text.startswith('(') and text.endswith(')'):
        # Check if they match
        depth = 0
        for i, c in enumerate(text):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            if depth == 0 and i < len(text) - 1:
                # The opening paren closes before the end, don't strip
                break
        else:
            # The opening paren's match is at the end, safe to strip
            text = text[1:-1]
    
    return text.strip()

def process_definite_integral(latex_input):
    """Definite integrals with bounds - COMPLETELY FIXED"""
    x = sp.Symbol('x')
    
    print(f"[DEFINITE INTEGRAL] Input: '{latex_input}'")
    
    # Parse: \int_{a}^{b} f(x) dx or \int_a^b f(x) dx
    # Try multiple patterns
    
    # Pattern 1: \int_{-1}^{1}
    bounds_match = re.search(r'\\int_\{([^}]+)\}\^\{([^}]+)\}', latex_input)
    
    # Pattern 2: \int_-1^1 (without braces)
    if not bounds_match:
        bounds_match = re.search(r'\\int_([^\^{\s]+)\^([^\s{]+)', latex_input)
    
    if bounds_match:
        lower = bounds_match.group(1).strip()
        upper = bounds_match.group(2).strip()
        
        print(f"[DEFINITE INTEGRAL] Bounds: [{lower}, {upper}]")
        
        # Parse bounds
        a = parse_bound(lower)
        b = parse_bound(upper)
        
        print(f"[DEFINITE INTEGRAL] Parsed bounds: [{a}, {b}]")
        
        # Get function - remove the integral notation
        func_str = latex_input
        
        # Remove \int_{}^{} pattern
        func_str = re.sub(r'\\int_\{[^}]*\}\^\{[^}]*\}', '', func_str)
        func_str = re.sub(r'\\int_[^\^{\s]+\^[^\s{]+', '', func_str)
        
        # Remove dx, d x
        func_str = func_str.replace('dx', '').replace('d x', '')
        
        # Remove spacing commands
        func_str = func_str.replace('\\,', '').replace('\\:', '').replace('\\;', '')
        
        # Clean LaTeX delimiters
        func_str = clean_latex_delimiters(func_str)
        
        func_str = func_str.strip()
        
        print(f"[DEFINITE INTEGRAL] Function string: '{func_str}'")
        
        if not func_str:
            raise Exception("No function found after removing integral notation")
        
        expr = parse_expression(func_str)
        print(f"[DEFINITE INTEGRAL] Parsed expression: {expr}")
        
        # Calculate
        try:
            definite_val = integrate(expr, (x, a, b))
            indefinite = integrate(expr, x)
        except Exception as e:
            print(f"[DEFINITE INTEGRAL] Integration error: {e}")
            raise Exception(f"Could not integrate: {str(e)}")
        
        # Numerical value
        try:
            numerical = float(definite_val.evalf())
        except:
            numerical = None
        
        # Plot
        plot_data = generate_definite_integral_plot(expr, x, a, b)
        
        return {
            'type': 'calculus_definite_integral',
            'function': str(expr),
            'lower_bound': str(a),
            'upper_bound': str(b),
            'definite_value': str(definite_val),
            'numerical_value': numerical,
            'indefinite_integral': str(indefinite),
            'plot_data': plot_data,
            'latex': {
                'function': sp.latex(expr),
                'integral': f"\\int_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} {sp.latex(expr)} \\, dx",
                'result': sp.latex(definite_val)
            }
        }
    
    # If no bounds found, treat as indefinite integral
    raise Exception("Could not parse definite integral bounds. Use format: \\int_{a}^{b} f(x) dx")

def process_limit(latex_input):
    """Limits including infinity and one-sided - FIXED"""
    x = sp.Symbol('x')
    
    # Try different limit patterns
    limit_match = re.search(r'\\?lim_\{?x\s*\\?to\s*([^}]+)\}?', latex_input)
    
    if not limit_match:
        # Try without braces: \lim x \to 2
        limit_match = re.search(r'\\?lim\s+x\s+\\?to\s+([^\s\\]+)', latex_input)
    
    if limit_match:
        approach = limit_match.group(1).strip().replace('}', '')
        
        if 'inf' in approach or '\\infty' in approach:
            a = oo if '-' not in approach else -oo
            direction = None
        else:
            if '+' in approach:
                a = sp.sympify(approach.replace('+', '').strip())
                direction = '+'
            elif '-' in approach and 'inf' not in approach:
                a = sp.sympify(approach.replace('-', '').strip())
                direction = '-'
            else:
                try:
                    a = sp.sympify(approach)
                    direction = None
                except:
                    a = float(approach)
                    direction = None
        
        # Extract function
        func_str = re.sub(r'\\?lim_?\{?x\s*\\?to\s*[^}]+\}?', '', latex_input).strip()
        func_str = re.sub(r'\\?lim\s+x\s+\\?to\s+[^\s\\]+', '', func_str).strip()
        
        print(f"Limit function: '{func_str}'")
        
        expr = parse_expression(func_str)
        
        if direction:
            main_limit = limit(expr, x, a, dir=direction)
        else:
            main_limit = limit(expr, x, a)
        
        left_lim = limit(expr, x, a, dir='-')
        right_lim = limit(expr, x, a, dir='+')
        
        exists = sp.simplify(left_lim - right_lim) == 0
        
        plot_data = generate_limit_plot(expr, x, a)
        
        return {
            'type': 'calculus_limit',
            'function': str(expr),
            'approach_value': str(a),
            'limit_value': str(main_limit),
            'left_limit': str(left_lim),
            'right_limit': str(right_lim),
            'limit_exists': exists,
            'plot_data': plot_data,
            'latex': {
                'function': sp.latex(expr),
                'limit': f"\\lim_{{x \\to {sp.latex(a)}}} {sp.latex(expr)}",
                'result': sp.latex(main_limit)
            }
        }
    raise Exception("Could not parse limit")

def process_taylor_series(latex_input):
    """Taylor/Maclaurin series expansion"""
    x = sp.Symbol('x')
    
    center = 0
    order = 5
    
    func_str = latex_input.strip()
    func_lower = func_str.lower()
    
    order_match = re.search(r'order\s*[=:]?\s*(\d+)', func_lower)
    if order_match:
        order = int(order_match.group(1))
        func_str = func_str[:order_match.start()] + func_str[order_match.end():]
    
    at_match = re.search(r'at\s+([+-]?\d+\.?\d*)', func_lower)
    if at_match:
        center = float(at_match.group(1))
        at_pos = func_lower.find('at')
        func_str = func_str[:at_pos] + func_str[at_match.end():]
    
    func_str = re.sub(r'\btaylor\b', '', func_str, flags=re.IGNORECASE)
    func_str = re.sub(r'\bseries\b', '', func_str, flags=re.IGNORECASE)
    func_str = re.sub(r'\bmaclaurin\b', '', func_str, flags=re.IGNORECASE)
    
    func_str = ' '.join(func_str.split()).strip()
    
    if not func_str:
        raise Exception("No function found in Taylor series input")
    
    expr = parse_expression(func_str)
    
    taylor_poly = series(expr, x, center, order + 1).removeO()
    
    terms = []
    for i in range(order + 1):
        coeff = diff(expr, x, i).subs(x, center) / factorial(i)
        if coeff != 0:
            terms.append({
                'order': i,
                'coefficient': str(coeff),
                'term': str(coeff * (x - center)**i)
            })
    
    plot_data = generate_taylor_plot(expr, taylor_poly, x, center)
    
    return {
        'type': 'calculus_taylor_series',
        'original_function': str(expr),
        'center': center,
        'order': order,
        'series_name': 'Maclaurin' if center == 0 else 'Taylor',
        'taylor_polynomial': str(taylor_poly),
        'terms': terms,
        'plot_data': plot_data,
        'latex': {
            'function': sp.latex(expr),
            'series': sp.latex(taylor_poly)
        }
    }

def process_partial_derivative(latex_input):
    """Partial derivatives - ENHANCED"""
    x, y = symbols('x y')
    
    # Check for second-order partial: \frac{\partial^2 f}{\partial x^2}
    second_order_match = re.search(r'\\?frac\{\\?partial\^2\s*f?\}\{\\?partial\s*([xyz])\^2\}', latex_input)
    
    if second_order_match:
        var_name = second_order_match.group(1)
        var = {'x': x, 'y': y}.get(var_name, x)
        
        # Get the function
        func_str = re.sub(r'\\?frac\{\\?partial\^2\s*f?\}\{\\?partial\s*[xyz]\^2\}', '', latex_input)
        func_str = func_str.strip()
        
        if not func_str:
            # No function provided, can't compute
            raise Exception("No function provided for partial derivative")
        
        expr = parse_multivariable_expression(func_str)
        
        # Compute second partial
        second_partial = diff(expr, var, 2)
        
        return {
            'type': 'calculus_partial_derivatives',
            'function': str(expr),
            'variables': [var_name],
            'partial_derivatives': {
                var_name: {
                    'first': str(diff(expr, var)),
                    'second': str(second_partial)
                }
            },
            'mixed_partials': {},
            'critical_points': [],
            'plot_data': None,
            'latex': {
                'function': sp.latex(expr)
            }
        }
    
    # Regular partial derivative processing
    func_str = re.sub(r'\\frac\{\\partial[^}]*\}\{\\partial\s*[xyz]\}', '', latex_input)
    func_str = func_str.replace('partial', '').strip()
    
    expr = parse_multivariable_expression(func_str)
    
    vars_in_expr = []
    if x in expr.free_symbols:
        vars_in_expr.append(x)
    if y in expr.free_symbols:
        vars_in_expr.append(y)
    
    partials = {}
    for var in vars_in_expr:
        partials[str(var)] = {
            'first': str(diff(expr, var)),
            'second': str(diff(expr, var, 2))
        }
    
    mixed = {}
    if len(vars_in_expr) == 2:
        mixed['∂²/∂x∂y'] = str(diff(expr, x, y))
    
    critical_pts = []
    if len(vars_in_expr) == 2:
        fx = diff(expr, x)
        fy = diff(expr, y)
        
        try:
            crit = solve([fx, fy], [x, y], dict=True)
            
            fxx = diff(fx, x)
            fyy = diff(fy, y)
            fxy = diff(fx, y)
            
            for pt in crit:
                if x in pt and y in pt:
                    D = fxx.subs(pt) * fyy.subs(pt) - (fxy.subs(pt))**2
                    
                    if D > 0:
                        classification = 'local minimum' if fxx.subs(pt) > 0 else 'local maximum'
                    elif D < 0:
                        classification = 'saddle point'
                    else:
                        classification = 'inconclusive'
                    
                    critical_pts.append({
                        'point': f"({pt[x]}, {pt[y]})",
                        'classification': classification
                    })
        except:
            pass
    
    plot_data = None
    if len(vars_in_expr) == 2:
        plot_data = generate_3d_surface(expr, x, y)
    
    return {
        'type': 'calculus_partial_derivatives',
        'function': str(expr),
        'variables': [str(v) for v in vars_in_expr],
        'partial_derivatives': partials,
        'mixed_partials': mixed,
        'critical_points': critical_pts,
        'plot_data': plot_data,
        'latex': {
            'function': sp.latex(expr)
        }
    }

# ============================================================================
# ULTRA-ROBUST LATEX PARSER - Handles EVERY format
# ============================================================================

def parse_expression(expr_string):
    """
    Ultra-robust LaTeX parser - COMPLETELY FIXED
    Handles ALL edge cases including cos^4 x, sin^2 x, etc.
    """
    text = expr_string.strip()
    
    print(f"[PARSE] Input: '{text}'")
    
    # Step 1: Remove spacing commands
    for cmd in ['\\,', '\\:', '\\;', '\\!', '\\quad', '\\qquad', '\\ ', '~']:
        text = text.replace(cmd, ' ')
    
    # Step 2: Handle sqrt FIRST
    text = handle_sqrt(text)
    print(f"[PARSE] After sqrt: '{text}'")
    
    # Step 3: Handle frac
    text = handle_frac(text)
    print(f"[PARSE] After frac: '{text}'")
    
    # Step 4: Replace LaTeX commands with Python equivalents
    replacements = {
        '\\sin': 'sin',
        '\\cos': 'cos',
        '\\tan': 'tan',
        '\\cot': 'cot',
        '\\sec': 'sec',
        '\\csc': 'csc',
        '\\arcsin': 'asin',
        '\\arccos': 'acos',
        '\\arctan': 'atan',
        '\\sinh': 'sinh',
        '\\cosh': 'cosh',
        '\\tanh': 'tanh',
        '\\ln': 'log',
        '\\log': 'log',
        '\\exp': 'exp',
        '\\abs': 'Abs',
        '\\pi': 'pi',
        '\\e': 'E'
    }
    
    for latex_cmd, py_cmd in replacements.items():
        text = text.replace(latex_cmd, py_cmd)
    
    print(f"[PARSE] After replacements: '{text}'")
    
    # Step 5: CRITICAL FIX - Handle trigonometric powers BEFORE removing backslashes
    # Pattern: cos^4 x, sin^2 x, tan^3 x, etc.
    # Convert to: (cos(x))^4, (sin(x))^2, etc.
    
    trig_funcs = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'asin', 'acos', 'atan']
    
    for func in trig_funcs:
        # Pattern: func^{n} x or func^n x
        # Match: cos^{4} x or cos^4 x
        pattern = rf'{func}\^(\d+|\{{\d+\}})\s+([a-zA-Z])'
        
        def replace_trig_power(match):
            power = match.group(1).strip('{}')
            var = match.group(2)
            return f'({func}({var}))**{power}'
        
        text = re.sub(pattern, replace_trig_power, text)
    
    print(f"[PARSE] After trig powers: '{text}'")
    
    # Step 6: Remove any remaining backslashes
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = text.replace('\\', '')
    
    # Step 7: Replace ^ with ** (for remaining exponents)
    text = text.replace('^', '**')
    
    # Step 8: Replace braces with parens
    text = text.replace('{', '(').replace('}', ')')
    
    print(f"[PARSE] Before implicit mult: '{text}'")
    
    # Step 9: Implicit multiplication
    text = add_implicit_multiplication(text)
    
    print(f"[PARSE] After implicit mult: '{text}'")
    
    # Step 10: Clean up spaces
    text = ' '.join(text.split())
    
    print(f"[PARSE] Final: '{text}'")
    
    # Step 11: Parse with SymPy
    try:
        result = sp.sympify(text, rational=False, locals={'E': sp.E})
        print(f"[PARSE] ✅ Success: {result}")
        return result
    except Exception as e:
        print(f"[PARSE] ❌ SymPy error: {e}")
        raise Exception(f"Could not parse: '{expr_string}' -> '{text}'\nError: {str(e)}")

def add_implicit_multiplication(text):
    """
    Add * for implicit multiplication - ENHANCED
    Process character by character to be safe
    """
    result = []
    i = 0
    
    # Function names that should NOT have * inserted
    functions = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 
                 'asin', 'acos', 'atan', 'acot', 'asec', 'acsc',
                 'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
                 'log', 'exp', 'sqrt', 'Abs', 'abs']
    
    while i < len(text):
        char = text[i]
        result.append(char)
        
        if i < len(text) - 1:
            next_char = text[i + 1]
            
            # Check if we need to insert *
            need_mult = False
            
            # Rule 1: digit followed by letter -> 2x, 3sin, 12cos
            if char.isdigit() and next_char.isalpha():
                # Always add * before functions or variables
                need_mult = True
            
            # Rule 2: digit followed by ( -> 2(
            elif char.isdigit() and next_char == '(':
                need_mult = True
            
            # Rule 3: ) followed by ( -> )(
            elif char == ')' and next_char == '(':
                need_mult = True
            
            # Rule 4: ) followed by digit or letter -> )x, )2
            elif char == ')' and (next_char.isalnum()):
                need_mult = True
            
            # Rule 5: letter followed by ( -> x(, but NOT sin(, cos(, etc.
            elif char.isalpha() and next_char == '(':
                # Check if current position is end of a function name
                is_func_end = False
                for func in functions:
                    if text[max(0, i-len(func)+1):i+1] == func:
                        is_func_end = True
                        break
                if not is_func_end:
                    need_mult = True
            
            # Rule 6: letter followed by digit -> x2
            elif char.isalpha() and next_char.isdigit():
                # Check if we're at end of a function name
                is_func_end = False
                for func in functions:
                    if text[max(0, i-len(func)+1):i+1] == func:
                        is_func_end = True
                        break
                if not is_func_end:
                    need_mult = True
            
            # NEW Rule 7: ) followed by letter (for cases like )e)
            elif char == ')' and next_char.isalpha():
                need_mult = True
            
            # NEW Rule 8: letter followed by letter that starts a function
            # Example: x sin(x) -> x*sin(x)
            elif char.isalpha() and next_char.isalpha():
                # Check if next letters form a function name
                is_next_func = False
                for func in functions:
                    if text[i+1:i+1+len(func)] == func:
                        is_next_func = True
                        break
                if is_next_func:
                    need_mult = True
            
            if need_mult:
                result.append('*')
        
        i += 1
    
    return ''.join(result)

def handle_sqrt(text):
    """
    Handle ALL sqrt variations iteratively
    """
    max_iterations = 10
    iteration = 0
    
    while '\\sqrt' in text and iteration < max_iterations:
        iteration += 1
        
        # nth root: \sqrt[n]{content}
        pattern_nth = r'\\sqrt\[([^\]]+)\]\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        match = re.search(pattern_nth, text)
        
        if match:
            n = match.group(1).strip()
            content = match.group(2).strip()
            replacement = f'(({content})**(1/({n})))'
            text = text[:match.start()] + replacement + text[match.end():]
            print(f"[SQRT] nth root: \\sqrt[{n}]{{{content}}} -> {replacement}")
            continue
        
        # Regular square root: \sqrt{content}
        pattern_regular = r'\\sqrt\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        match = re.search(pattern_regular, text)
        
        if match:
            content = match.group(1).strip()
            replacement = f'sqrt({content})'
            text = text[:match.start()] + replacement + text[match.end():]
            print(f"[SQRT] square root: \\sqrt{{{content}}} -> {replacement}")
            continue
        
        break
    
    return text

def handle_frac(text):
    """
    Handle ALL frac variations - ULTRA-FIXED
    """
    max_iterations = 15  # Increase for nested fractions
    iteration = 0
    
    while ('\\frac' in text or 'frac' in text) and iteration < max_iterations:
        iteration += 1
        
        # SPECIAL CASE 1: derivative notation \frac{d}{dx} or \frac{d^n}{dx^n}
        derivative_pattern = r'\\?frac\{d\^?\d*\s*f?\}\{d[a-z]\^?\d*\}'
        if re.search(derivative_pattern, text):
            text = re.sub(derivative_pattern, '', text)
            print(f"[FRAC] Removed derivative notation")
            continue
        
        # SPECIAL CASE 2: partial derivatives
        partial_pattern = r'\\?frac\{\\?partial\^?\d*\s*f?\}\{\\?partial\s*[xyz]\^?\d*\}'
        if re.search(partial_pattern, text):
            text = re.sub(partial_pattern, '', text)
            print(f"[FRAC] Removed partial derivative notation")
            continue
        
        # Regular fractions - IMPROVED regex for deeply nested structures
        pattern = r'\\?frac\{([^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}[^{}]*)*)\}'
        match = re.search(pattern, text)
        
        if match:
            numerator = match.group(1).strip()
            denominator = match.group(2).strip()
            
            # Skip if denominator is empty
            if not denominator:
                text = text[:match.start()] + numerator + text[match.end():]
                print(f"[FRAC] Empty denominator, using numerator only")
                continue
            
            replacement = f'(({numerator})/({denominator}))'
            text = text[:match.start()] + replacement + text[match.end():]
            print(f"[FRAC] Converted fraction")
        else:
            break
    
    return text

def parse_multivariable_expression(expr_string):
    """Parse multivariable expressions"""
    # Use the same robust parser
    return parse_expression(expr_string)

def parse_bound(bound_str):
    """Parse integral bound"""
    bound_str = bound_str.strip()
    if 'inf' in bound_str.lower() or 'infty' in bound_str.lower():
        return oo if '-' not in bound_str else -oo
    try:
        return sp.sympify(bound_str)
    except:
        return float(bound_str)

def find_real_solutions(expr, x):
    """Find real solutions"""
    try:
        sols = solve(expr, x)
        real_sols = []
        for s in sols:
            try:
                val = complex(s)
                if abs(val.imag) < 1e-10:
                    real_sols.append(val.real)
            except:
                pass
        return real_sols
    except:
        return []

def analyze_intervals(f_prime, f_double_prime, x, critical_pts, inflection_pts):
    """Analyze function behavior on intervals"""
    all_pts = sorted(set(critical_pts + inflection_pts))
    if not all_pts:
        return []
    
    fp = sp.lambdify(x, f_prime, 'numpy')
    fpp = sp.lambdify(x, f_double_prime, 'numpy')
    
    analysis = []
    
    # Before first point
    test = all_pts[0] - 1
    try:
        analysis.append({
            'interval': f"(-∞, {all_pts[0]:.2f})",
            'increasing': bool(fp(test) > 0),
            'concave_up': bool(fpp(test) > 0)
        })
    except:
        pass
    
    # Between points
    for i in range(len(all_pts) - 1):
        test = (all_pts[i] + all_pts[i+1]) / 2
        try:
            analysis.append({
                'interval': f"({all_pts[i]:.2f}, {all_pts[i+1]:.2f})",
                'increasing': bool(fp(test) > 0),
                'concave_up': bool(fpp(test) > 0)
            })
        except:
            pass
    
    # After last point
    test = all_pts[-1] + 1
    try:
        analysis.append({
            'interval': f"({all_pts[-1]:.2f}, ∞)",
            'increasing': bool(fp(test) > 0),
            'concave_up': bool(fpp(test) > 0)
        })
    except:
        pass
    
    return analysis

# ============================================================================
# PLOTTING FUNCTIONS - ALL FIXED WITH JSON SANITIZATION
# ============================================================================

def generate_advanced_plot(expr, f_prime, f_double_prime, x, critical_pts, inflection_pts):
    """Generate comprehensive plot data - FIXED"""
    x_vals = np.linspace(-10, 10, 500)
    
    f = sp.lambdify(x, expr, 'numpy')
    fp = sp.lambdify(x, f_prime, 'numpy')
    fpp = sp.lambdify(x, f_double_prime, 'numpy')
    
    try:
        y = f(x_vals)
        y = np.clip(y, -100, 100)
        yp = fp(x_vals)
        yp = np.clip(yp, -100, 100)
        ypp = fpp(x_vals)
        ypp = np.clip(ypp, -100, 100)
    except:
        y = yp = ypp = np.zeros_like(x_vals)
    
    crit_markers = []
    for cp in critical_pts:
        if -10 <= cp <= 10:
            try:
                y_val = float(f(cp))
                if not np.isnan(y_val) and not np.isinf(y_val):
                    crit_markers.append({'x': float(cp), 'y': y_val})
            except:
                pass
    
    infl_markers = []
    for ip in inflection_pts:
        if -10 <= ip <= 10:
            try:
                y_val = float(f(ip))
                if not np.isnan(y_val) and not np.isinf(y_val):
                    infl_markers.append({'x': float(ip), 'y': y_val})
            except:
                pass
    
    return {
        'x': sanitize_for_json(x_vals),
        'y_original': sanitize_for_json(y),
        'y_derivative': sanitize_for_json(yp),
        'y_second_derivative': sanitize_for_json(ypp),
        'critical_points': crit_markers,
        'inflection_points': infl_markers
    }

def generate_definite_integral_plot(expr, x, a, b):
    """Plot for definite integrals - FIXED"""
    try:
        a_val = float(a) if a != oo and a != -oo else (-10 if a == -oo else 10)
        b_val = float(b) if b != oo and b != -oo else (-10 if b == -oo else 10)
    except:
        a_val, b_val = 0, 5
    
    # Avoid division by zero at x=0 for 1/sqrt(x)
    if a_val == 0:
        a_val = 0.001
    
    x_vals = np.linspace(max(a_val - 2, -10), min(b_val + 2, 10), 500)
    x_fill = np.linspace(a_val, b_val, 200)
    
    f = sp.lambdify(x, expr, 'numpy')
    
    try:
        y = f(x_vals)
        y = np.clip(y, -100, 100)
        y_fill = f(x_fill)
        y_fill = np.clip(y_fill, -100, 100)
    except:
        y = np.zeros_like(x_vals)
        y_fill = np.zeros_like(x_fill)
    
    return {
        'x': sanitize_for_json(x_vals),
        'y': sanitize_for_json(y),
        'x_fill': sanitize_for_json(x_fill),
        'y_fill': sanitize_for_json(y_fill),
        'bounds': [a_val, b_val]
    }

def generate_limit_plot(expr, x, a):
    """Plot for limits - FIXED"""
    try:
        a_val = float(a) if a not in [oo, -oo] else 0
    except:
        a_val = 0
    
    if a in [oo, -oo]:
        x_vals = np.linspace(-20, 20, 500)
    else:
        x_vals = np.concatenate([
            np.linspace(a_val - 5, a_val - 0.01, 250),
            np.linspace(a_val + 0.01, a_val + 5, 250)
        ])
    
    f = sp.lambdify(x, expr, 'numpy')
    
    try:
        y = f(x_vals)
        y = np.clip(y, -100, 100)
    except:
        y = np.zeros_like(x_vals)
    
    return {
        'x': sanitize_for_json(x_vals),
        'y': sanitize_for_json(y),
        'approach_point': a_val if a not in [oo, -oo] else None
    }

def generate_taylor_plot(original, taylor_poly, x, center):
    """Plot original vs Taylor approximation - FIXED"""
    x_vals = np.linspace(center - 5, center + 5, 500)
    
    f = sp.lambdify(x, original, 'numpy')
    f_taylor = sp.lambdify(x, taylor_poly, 'numpy')
    
    try:
        y_orig = f(x_vals)
        y_orig = np.clip(y_orig, -50, 50)
        y_taylor = f_taylor(x_vals)
        y_taylor = np.clip(y_taylor, -50, 50)
    except:
        y_orig = y_taylor = np.zeros_like(x_vals)
    
    return {
        'x': sanitize_for_json(x_vals),
        'y_original': sanitize_for_json(y_orig),
        'y_taylor': sanitize_for_json(y_taylor),
        'center': center
    }

def generate_3d_surface(expr, x, y):
    """Generate 3D surface plot data - FIXED"""
    x_vals = np.linspace(-5, 5, 50)
    y_vals = np.linspace(-5, 5, 50)
    X, Y = np.meshgrid(x_vals, y_vals)
    
    f = sp.lambdify((x, y), expr, 'numpy')
    
    try:
        Z = f(X, Y)
        Z = np.clip(Z, -50, 50)
    except:
        Z = np.zeros_like(X)
    
    return {
        'type': '3d_surface',
        'x': sanitize_for_json(X),
        'y': sanitize_for_json(Y),
        'z': sanitize_for_json(Z)
    }