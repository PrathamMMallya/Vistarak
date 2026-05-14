import sympy as sp
import numpy as np
from sympy.parsing.latex import parse_latex
from sympy import symbols, Eq, solve, factor, expand, simplify, apart, together
from sympy import Poly, roots, degree, LC, LT, Abs, sqrt, Interval, Union, FiniteSet
from sympy.solvers.inequalities import solve_univariate_inequality, reduce_rational_inequalities
from sympy.core.relational import Relational, StrictLessThan, LessThan, StrictGreaterThan, GreaterThan
import re
import json

def process_algebra(latex_input):
    """
    COMPREHENSIVE ADVANCED Algebra Module - FIXED VERSION
    
    Handles:
    ✅ Polynomial equations (all degrees)
    ✅ Systems of equations (LINEAR + NONLINEAR with numerical solving)
    ✅ Inequalities (with interval notation and number line)
    ✅ Rational inequalities (with sign analysis)
    ✅ Absolute value equations
    ✅ Radical equations (sqrt)
    ✅ Rational expressions
    ✅ Complex solutions (with complex plane plot)
    ✅ Multi-variable equations
    """
    try:
        # Clean LaTeX delimiters
        latex_input = clean_latex_delimiters(latex_input)
        
        # Detect type and process
        if ';' in latex_input or ('\\begin{equation}' in latex_input and latex_input.count('=') > 1):
            return process_system_of_equations(latex_input)
        elif any(op in latex_input for op in ['<', '>', '≤', '≥', 'leq', 'geq', 'le ', 'ge ']):
            return process_inequality(latex_input)
        elif '|' in latex_input or 'abs' in latex_input.lower() or 'vert' in latex_input.lower():
            return process_absolute_value(latex_input)
        elif 'sqrt' in latex_input.lower() or '√' in latex_input:
            return process_radical_equation(latex_input)
        else:
            return process_single_algebra(latex_input)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Algebra processing error: {str(e)}")

def clean_latex_delimiters(text):
    """Remove LaTeX display delimiters"""
    text = text.replace('\\[', '').replace('\\]', '')
    text = text.replace('\\(', '').replace('\\)', '')
    text = text.replace('$$', '')
    text = text.strip()
    return text

def process_single_algebra(latex_input):
    """Process single algebraic equation or expression - FIXED"""
    x = sp.Symbol('x', real=True)
    
    cleaned_input = normalize_latex_input(latex_input)
    is_equation = '=' in cleaned_input
    
    if is_equation:
        parts = cleaned_input.split('=', 1)
        lhs = parse_expression(parts[0].strip())
        rhs = parse_expression(parts[1].strip())
        
        equation = Eq(lhs, rhs)
        expr = lhs - rhs
        
        # Solve with error handling
        try:
            solutions = solve(equation, x, dict=False)
            if not isinstance(solutions, list):
                solutions = [solutions] if solutions else []
        except Exception as e:
            print(f"Solve error: {e}")
            solutions = []
        
        equation_type = classify_equation(expr, x)
    else:
        expr = parse_expression(cleaned_input)
        equation = None
        solutions = []
        equation_type = "Expression"
    
    # Perform analysis
    analysis = perform_algebraic_analysis(expr, x, solutions)
    
    # Check if solutions are complex
    has_complex = False
    for sol in solutions:
        try:
            sol_complex = sp.sympify(sol)
            if sol_complex.has(sp.I) or (hasattr(sol_complex, 'is_complex') and sol_complex.is_complex):
                has_complex = True
                break
        except:
            pass
    
    # Generate appropriate plot
    if has_complex and solutions:
        plot_data = generate_complex_plane_plot(solutions)
        plot_data['plot_type'] = 'complex_plane'
    else:
        plot_data = generate_plot_data(expr, x, solutions)
        plot_data['plot_type'] = 'standard'
    
    return {
        'type': 'algebra',
        'equation_type': equation_type,
        'original_expression': str(expr),
        'solutions': analysis['solutions'],
        'real_solutions': analysis['real_solutions'],
        'complex_solutions': analysis['complex_solutions'],
        'factored': analysis['factored'],
        'expanded': analysis['expanded'],
        'simplified': analysis['simplified'],
        'domain_restrictions': analysis['domain_restrictions'],
        'plot_data': plot_data,
        'latex': {
            'expression': sp.latex(expr),
            'factored': sp.latex(analysis['factored_expr']),
            'solutions': [sp.latex(s) for s in solutions]
        },
        'analysis': analysis['additional_info']
    }

def process_system_of_equations(latex_input):
    """Process system of equations WITH NONLINEAR SUPPORT - FIXED"""
    # Parse equations - handle both ; and \begin{equation} formats
    if '\\begin{equation}' in latex_input:
        # Extract equations between \begin and \end
        equations_text = re.findall(r'\\begin\{equation\}(.*?)\\end\{equation\}', latex_input, re.DOTALL)
        if not equations_text:
            # Try alternate format
            equations_text = [eq.strip() for eq in latex_input.split('\n') if '=' in eq]
    else:
        equations_text = re.split(r'[;\n]', latex_input)
    
    x, y, z = symbols('x y z', real=True)
    variables = [x, y]
    
    equations = []
    is_nonlinear = False
    
    for eq_text in equations_text:
        eq_text = eq_text.strip()
        if not eq_text or '=' not in eq_text:
            continue
            
        try:
            cleaned = normalize_latex_input(eq_text)
            parts = cleaned.split('=', 1)
            lhs = parse_expression(parts[0].strip())
            rhs = parse_expression(parts[1].strip())
            eq = Eq(lhs, rhs)
            equations.append(eq)
            
            # Check if nonlinear
            try:
                expr_check = lhs - rhs
                for var in [x, y]:
                    poly_degree = sp.degree(expr_check, gen=var)
                    if poly_degree > 1:
                        is_nonlinear = True
            except Exception:
                # Check string representation
                expr_str = str(lhs - rhs)
                if 'x**2' in expr_str or 'y**2' in expr_str or 'x*y' in expr_str:
                    is_nonlinear = True
        except Exception as e:
            print(f"Error parsing equation '{eq_text}': {e}")
            continue
    
    if not equations:
        raise Exception("No valid equations found in system")
    
    # Check for z variable
    if any('z' in str(eq) for eq in equations):
        variables.append(z)
    
    # Solve system with better error handling
    solution = []
    solution_method = "symbolic"
    
    try:
        if is_nonlinear and len(variables) == 2:
            # Try symbolic first
            try:
                sol = solve(equations, variables, dict=True)
                if sol and len(sol) > 0:
                    solution = sol
                    solution_method = "symbolic"
                else:
                    # Numerical fallback
                    solution, solution_method = solve_nonlinear_system_numerical(equations, variables)
            except Exception as e:
                print(f"Symbolic solve failed: {e}")
                # Numerical fallback
                solution, solution_method = solve_nonlinear_system_numerical(equations, variables)
        else:
            # Linear system
            try:
                solution = solve(equations, variables, dict=True)
                if not solution:
                    # Try non-dict mode
                    solution_alt = solve(equations, variables, dict=False)
                    if solution_alt:
                        if isinstance(solution_alt, dict):
                            solution = [solution_alt]
                        elif isinstance(solution_alt, list):
                            solution = solution_alt
            except Exception as e:
                print(f"Linear solve error: {e}")
                solution = []
    except Exception as e:
        print(f"System solving error: {e}")
        # Last resort numerical fallback for 2D
        if len(variables) == 2:
            try:
                solution, solution_method = solve_nonlinear_system_numerical(equations, variables)
            except:
                solution = []
        else:
            solution = []
    
    # Generate visualization for 2D system
    plot_data = None
    if len(variables) == 2 and len(equations) >= 2:
        plot_data = visualize_2d_system(equations[:2], x, y, solution, is_nonlinear)
    
    return {
        'type': 'algebra_system',
        'system_size': f"{len(equations)}x{len(variables)}",
        'is_nonlinear': is_nonlinear,
        'solution_method': solution_method,
        'equations': [str(eq) for eq in equations],
        'solution': solution,
        'plot_data': plot_data,
        'latex': {
            'equations': [sp.latex(eq) for eq in equations],
            'solution': [sp.latex(sol) for sol in solution] if solution else []
        }
    }

def solve_nonlinear_system_numerical(equations, variables):
    """Solve nonlinear system using numerical methods - FIXED"""
    from scipy.optimize import fsolve
    
    x, y = variables[0], variables[1]
    
    # Convert to numerical functions
    try:
        eq1 = equations[0].lhs - equations[0].rhs
        eq2 = equations[1].lhs - equations[1].rhs
        
        f1 = sp.lambdify((x, y), eq1, 'numpy')
        f2 = sp.lambdify((x, y), eq2, 'numpy')
    except Exception as e:
        print(f"Lambdify error: {e}")
        return [], "failed"
    
    def system(vars):
        x_val, y_val = vars
        try:
            return [float(f1(x_val, y_val)), float(f2(x_val, y_val))]
        except:
            return [1e10, 1e10]
    
    # Try multiple initial guesses
    initial_guesses = [
        (0, 0), (1, 1), (-1, -1), (2, 2), (-2, -2),
        (5, 5), (-5, -5), (0, 5), (5, 0), (1, -1),
        (0, 1), (1, 0), (2, -2), (-2, 2), (3, 3)
    ]
    
    solutions = []
    for guess in initial_guesses:
        try:
            sol = fsolve(system, guess, full_output=True)
            x_sol, y_sol = sol[0]
            info = sol[1]
            
            # Check if solution converged
            residual = sum([abs(val) for val in info['fvec']])
            
            if residual < 0.001:
                # Check if already found (avoid duplicates)
                is_duplicate = False
                for existing in solutions:
                    if abs(existing[x] - x_sol) < 0.01 and abs(existing[y] - y_sol) < 0.01:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    solutions.append({x: float(x_sol), y: float(y_sol)})
        except Exception as e:
            continue
    
    return solutions, "numerical" if solutions else "failed"

def visualize_2d_system(equations, x, y, solution, is_nonlinear):
    """Create visualization for 2D system - FIXED"""
    
    if is_nonlinear:
        # Use contour plotting for nonlinear
        x_vals = np.linspace(-10, 10, 300)
        y_vals = np.linspace(-10, 10, 300)
        X, Y = np.meshgrid(x_vals, y_vals)
        
        contours = []
        
        for i, eq in enumerate(equations):
            try:
                expr = eq.lhs - eq.rhs
                f = sp.lambdify((x, y), expr, 'numpy')
                Z = f(X, Y)
                Z = np.clip(Z, -100, 100)
                Z = np.nan_to_num(Z, nan=0.0, posinf=100, neginf=-100)
                
                contours.append({
    'x': x_vals.tolist(),
    'y': y_vals.tolist(),
    'z': Z.tolist(),
    'name': f'Equation {i+1}'
})

            except Exception as e:
                print(f"Contour error for equation {i}: {e}")
        
        # Add solution points
        solution_points = []
        if solution and len(solution) > 0:
            for sol in solution:
                try:
                    if isinstance(sol, dict):
                        if x in sol and y in sol:
                            x_val = float(complex(sol[x]).real)
                            y_val = float(complex(sol[y]).real)
                            solution_points.append({'x': x_val, 'y': y_val})
                except Exception as e:
                    print(f"Solution point error: {e}")
        
        return {
            'type': 'system_2d_nonlinear',
            'contours': contours,
            'solution_points': solution_points
        }
    
    else:
        # Linear system - use line plotting
        x_vals = np.linspace(-10, 10, 500)
        lines_data = []
        
        for i, eq in enumerate(equations):
            try:
                # Solve for y in terms of x
                y_solutions = sp.solve(eq, y)
                if y_solutions:
                    y_expr = y_solutions[0]
                    f = sp.lambdify(x, y_expr, 'numpy')
                    y_vals = f(x_vals)
                    y_vals = np.clip(y_vals, -50, 50)
                    y_vals = np.nan_to_num(y_vals, nan=0.0, posinf=50, neginf=-50)
                    
                    lines_data.append({
                        'x': x_vals.tolist(),
                        'y': y_vals.tolist(),
                        'name': f'Equation {i+1}'
                    })
            except Exception as e:
                print(f"Line plot error for equation {i}: {e}")
        
        # Add solution point
        solution_point = None
        if solution and len(solution) > 0:
            try:
                sol_dict = solution[0] if isinstance(solution[0], dict) else {}
                if x in sol_dict and y in sol_dict:
                    solution_point = {
                        'x': float(complex(sol_dict[x]).real),
                        'y': float(complex(sol_dict[y]).real)
                    }
            except Exception as e:
                print(f"Solution point error: {e}")
        
        return {
            'type': 'system_2d',
            'lines': lines_data,
            'solution_point': solution_point
        }

def process_inequality(latex_input):
    """Process inequalities WITH INTERVAL NOTATION - FIXED"""
    x = sp.Symbol('x', real=True)
    
    # Normalize symbols
    text = latex_input.replace('≤', '<=').replace('≥', '>=')
    text = text.replace('\\leq', '<=').replace('\\geq', '>=')
    text = text.replace('\\le', '<=').replace('\\ge', '>=')
    text = text.replace('\\lt', '<').replace('\\gt', '>')
    text = normalize_latex_input(text)
    
    print(f"DEBUG INEQUALITY: Normalized text: '{text}'")
    
    # Parse inequality
    inequality_obj = None
    op = None
    
    for operator in ['<=', '>=', '<', '>']:
        if operator in text:
            op = operator
            parts = text.split(operator, 1)
            lhs = parse_expression(parts[0].strip())
            rhs = parse_expression(parts[1].strip())
            
            print(f"DEBUG INEQUALITY: LHS: {lhs}, RHS: {rhs}, Operator: {op}")
            
            expr = lhs - rhs
            
            print(f"DEBUG INEQUALITY: Expression (lhs - rhs): {expr}")
            
            # Create inequality object
            if operator == '<':
                inequality_obj = StrictLessThan(expr, 0)
            elif operator == '>':
                inequality_obj = StrictGreaterThan(expr, 0)
            elif operator == '<=':
                inequality_obj = LessThan(expr, 0)
            elif operator == '>=':
                inequality_obj = GreaterThan(expr, 0)
            
            break
    
    if inequality_obj is None:
        raise Exception("Could not parse inequality")
    
    print(f"DEBUG INEQUALITY: Inequality object: {inequality_obj}")
    
    # Check if rational inequality
    numer, denom = expr.as_numer_denom()
    is_rational = denom != 1
    
    # Solve inequality with error handling
    solution_set = sp.EmptySet
    try:
        solution_set = solve_univariate_inequality(
            inequality_obj,
            x,
            relational=False
        )
        print(f"DEBUG INEQUALITY: SymPy solution: {solution_set}")
    except Exception as e:
        print(f"DEBUG INEQUALITY: SymPy solve failed: {e}")
        # MANUAL SIGN TESTING (CORRECT FALLBACK)
        critical_pts = find_critical_points(expr, x)
        print(f"DEBUG INEQUALITY: Critical points: {critical_pts}")
        solution_set = test_inequality_regions(expr, x, critical_pts, op)
        print(f"DEBUG INEQUALITY: Manual solution: {solution_set}")
    
    # Get critical points
    critical_points = find_critical_points(expr, x)
    
    # Generate interval notation
    interval_notation = format_interval_notation(solution_set)
    
    print(f"DEBUG INEQUALITY: Final solution: {solution_set}")
    print(f"DEBUG INEQUALITY: Interval notation: {interval_notation}")
    
    # Generate sign chart
    sign_chart = generate_sign_chart(expr, x, critical_points, op)
    
    # Generate plot
    plot_data = generate_inequality_plot_advanced(expr, x, solution_set, op, critical_points, is_rational)
    
    return {
        'type': 'algebra_inequality',
        'is_rational': is_rational,
        'inequality': str(inequality_obj),
        'solution': str(solution_set),
        'interval_notation': interval_notation,
        'critical_points': [float(cp) for cp in critical_points if abs(cp) < 1e6],
        'sign_chart': sign_chart,
        'plot_data': plot_data,
        'latex': {
            'inequality': sp.latex(inequality_obj),
            'solution': sp.latex(solution_set)
        }
    }
def test_inequality_regions(expr, x, critical_points, operator):
    """Test inequality in regions defined by critical points"""
    if not critical_points:
        return sp.Reals
    
    # Sort critical points
    try:
        crit_sorted = sorted([float(cp) for cp in critical_points if cp.is_real])
    except:
        return sp.Reals
    
    f = sp.lambdify(x, expr, 'numpy')
    solution_intervals = []
    
    # Test regions
    test_points = []
    test_points.append(crit_sorted[0] - 1)  # Before first
    for i in range(len(crit_sorted) - 1):
        test_points.append((crit_sorted[i] + crit_sorted[i+1]) / 2)
    test_points.append(crit_sorted[-1] + 1)  # After last
    
    # Build solution
    for i, test_pt in enumerate(test_points):
        try:
            val = f(test_pt)
            satisfies = False
            
            if operator == '>':
                satisfies = val > 0
            elif operator == '>=':
                satisfies = val >= 0
            elif operator == '<':
                satisfies = val < 0
            elif operator == '<=':
                satisfies = val <= 0
            
            if satisfies:
                if i == 0:
                    solution_intervals.append(Interval(-sp.oo, crit_sorted[0], False, '=' in operator))
                elif i == len(test_points) - 1:
                    solution_intervals.append(Interval(crit_sorted[-1], sp.oo, '=' in operator, False))
                else:
                    solution_intervals.append(Interval(crit_sorted[i-1], crit_sorted[i], '=' in operator, '=' in operator))
        except:
            continue
    
    if solution_intervals:
        return Union(*solution_intervals)
    return sp.EmptySet

def find_critical_points(expr, x):
    """Find critical points - FIXED"""
    critical = set()
    
    try:
        numer, denom = expr.as_numer_denom()
        
        # Zeros of numerator
        try:
            zeros = solve(numer, x)
            for z in zeros:
                if z.is_real and abs(z) < 1e6:
                    critical.add(float(z))
        except:
            pass
        
        # Zeros of denominator
        try:
            discontinuities = solve(denom, x)
            for d in discontinuities:
                if d.is_real and abs(d) < 1e6:
                    critical.add(float(d))
        except:
            pass
    except:
        pass
    
    return sorted(list(critical))

def generate_sign_chart(expr, x, critical_points, operator):
    """Generate sign chart - FIXED"""
    if not critical_points:
        return []
    
    f = sp.lambdify(x, expr, 'numpy')
    chart = []
    
    # Test regions
    test_points = []
    test_points.append(critical_points[0] - 1)
    for i in range(len(critical_points) - 1):
        test_points.append((critical_points[i] + critical_points[i+1]) / 2)
    test_points.append(critical_points[-1] + 1)
    
    for i, test_pt in enumerate(test_points):
        try:
            val = f(test_pt)
            
            if np.isnan(val) or np.isinf(val):
                continue
            
            sign = '+' if val > 0 else '-' if val < 0 else '0'
            
            satisfies = False
            if operator in ['>', '>=']:
                satisfies = val > 0 or (operator == '>=' and abs(val) < 0.001)
            elif operator in ['<', '<=']:
                satisfies = val < 0 or (operator == '<=' and abs(val) < 0.001)
            
            if i == 0:
                interval = f"(-∞, {critical_points[0]:.2f})"
            elif i == len(test_points) - 1:
                interval = f"({critical_points[-1]:.2f}, ∞)"
            else:
                interval = f"({critical_points[i-1]:.2f}, {critical_points[i]:.2f})"
            
            chart.append({
                'interval': interval,
                'sign': sign,
                'satisfies': satisfies
            })
        except Exception as e:
            continue
    
    return chart

def format_interval_notation(solution_set):
    if solution_set == sp.EmptySet:
        return "∅"
    if solution_set == sp.Reals:
        return "(-∞, ∞)"
    return str(solution_set).replace('oo', '∞')


def generate_inequality_plot_advanced(expr, x, solution_set, operator, critical_points, is_rational):
    """Generate inequality plot - FIXED"""
    x_vals = np.linspace(-10, 10, 1000)
    f = sp.lambdify(x, expr, 'numpy')
    
    try:
        y_vals = f(x_vals)
        y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)
        y_vals = np.clip(y_vals, -50, 50)
    except:
        y_vals = np.full_like(x_vals, np.nan)
    
    # Shaded regions
    shaded_regions = []
    for xv, yv in zip(x_vals, y_vals):
        if not np.isnan(yv):
            in_solution = False
            if operator in ['>', '>=']:
                in_solution = yv > 0 or (operator == '>=' and abs(yv) < 0.1)
            elif operator in ['<', '<=']:
                in_solution = yv < 0 or (operator == '<=' and abs(yv) < 0.1)
            
            if in_solution:
                shaded_regions.append({'x': float(xv), 'y': float(yv)})
    
    return {
        'type': 'inequality_advanced',
        'x': x_vals.tolist(),
        'y': y_vals.tolist(),
        'shaded_regions': shaded_regions,
        'critical_points': critical_points,
        'solution': format_interval_notation(solution_set),
        'is_rational': is_rational
    }

def process_absolute_value(latex_input):
    """Process absolute value equations - COMPLETELY FIXED"""
    x = sp.Symbol('x', real=True)
    
    # STEP 1: Normalize absolute value notation FIRST
    text = latex_input.replace('\\lvert', '|')
    text = text.replace('\\rvert', '|')
    text = text.replace('\\vert', '|')
    
    # STEP 2: Apply general normalization
    text = normalize_latex_input(text)
    
    # STEP 3: Add implicit multiplication
    text = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', text)
    
    if '=' not in text:
        raise Exception("Absolute value equation must contain '='")
    
    # STEP 4: Split equation
    parts = text.split('=', 1)
    lhs = parts[0].strip()
    rhs = parts[1].strip()
    
    # STEP 5: Extract inside | | with better regex
    # This handles |expr| anywhere in the lhs
    match = re.search(r'\|([^|]+)\|', lhs)
    if not match:
        raise Exception(f"Invalid absolute value format. Input: {lhs}")
    
    inner_expr_str = match.group(1).strip()
    
    print(f"DEBUG: Extracted inner expression: '{inner_expr_str}'")
    print(f"DEBUG: RHS: '{rhs}'")
    
    # STEP 6: Parse expressions
    try:
        inner = sp.sympify(inner_expr_str)
        rhs_val = sp.sympify(rhs)
    except Exception as e:
        raise Exception(f"Could not parse expression. Inner: '{inner_expr_str}', RHS: '{rhs}'. Error: {e}")
    
    print(f"DEBUG: Parsed inner: {inner}, Parsed rhs: {rhs_val}")
    
    # STEP 7: Check if rhs is negative (no solution)
    try:
        rhs_numeric = float(rhs_val.evalf())
        if rhs_numeric < 0:
            # No solution if |A| = negative number
            return {
                'type': 'algebra_absolute',
                'equation': f"|{inner}| = {rhs_val}",
                'solutions': [],
                'plot_data': generate_plot_data_absolute(sp.Abs(inner), x, [], rhs_numeric),
                'latex': {
                    'equation': f"|{sp.latex(inner)}| = {sp.latex(rhs_val)}",
                    'solutions': []
                }
            }
    except:
        pass
    
    # STEP 8: Solve |A| = B  →  A = B OR A = -B
    eq1 = sp.Eq(inner, rhs_val)
    eq2 = sp.Eq(inner, -rhs_val)
    
    sols = []
    
    # Solve both cases
    for eq in [eq1, eq2]:
        try:
            print(f"DEBUG: Solving {eq}")
            solved = sp.solve(eq, x)
            print(f"DEBUG: Solutions: {solved}")
            
            for s in solved:
                # Ensure it's a real number
                try:
                    # Convert to float
                    s_float = float(s.evalf())
                    
                    # Check if already in list (avoid duplicates)
                    if not any(abs(s_float - existing) < 1e-10 for existing in sols):
                        sols.append(s_float)
                        print(f"DEBUG: Added solution: {s_float}")
                except (TypeError, ValueError, AttributeError) as e:
                    print(f"DEBUG: Could not convert {s} to float: {e}")
                    # Check if it's actually real
                    if hasattr(s, 'is_real') and s.is_real:
                        try:
                            s_val = complex(s)
                            if abs(s_val.imag) < 1e-10:
                                s_float = float(s_val.real)
                                if not any(abs(s_float - existing) < 1e-10 for existing in sols):
                                    sols.append(s_float)
                                    print(f"DEBUG: Added solution: {s_float}")
                        except:
                            pass
        except Exception as e:
            print(f"DEBUG: Solve error for {eq}: {e}")
            continue
    
    # STEP 9: Sort solutions
    try:
        sols = sorted(sols)
    except:
        pass
    
    print(f"DEBUG: Final solutions: {sols}")
    
    # STEP 10: Create absolute value expression for plotting
    abs_expr = sp.Abs(inner)
    
    # STEP 11: Generate plot
    try:
        rhs_float = float(rhs_val.evalf())
    except:
        rhs_float = 0
    
    plot_data = generate_plot_data_absolute(abs_expr, x, sols, rhs_float)
    
    return {
        'type': 'algebra_absolute',
        'equation': f"|{inner}| = {rhs_val}",
        'solutions': [f"{s:.4f}" if isinstance(s, (int, float)) else str(s) for s in sols],
        'plot_data': plot_data,
        'latex': {
            'equation': f"|{sp.latex(inner)}| = {sp.latex(rhs_val)}",
            'solutions': [sp.latex(s) for s in sols] if sols else []
        }
    }

def process_radical_equation(latex_input):
    """Process radical equations - FIXED"""
    x = sp.Symbol('x', real=True)
    
    text = normalize_latex_input(latex_input)
    text = text.replace('√', 'sqrt').replace('\\sqrt', 'sqrt')
    
    if '=' in text:
        parts = text.split('=', 1)
        try:
            lhs = parse_expression(parts[0].strip())
            rhs = parse_expression(parts[1].strip())
        except Exception as e:
            raise Exception(f"Could not parse radical equation: {e}")
        
        equation = Eq(lhs, rhs)
        
        try:
            solutions = solve(equation, x)
        except:
            solutions = []
        
        # Verify solutions (check for extraneous roots)
        verified_solutions = []
        for sol in solutions:
            try:
                # Substitute back
                lhs_val = lhs.subs(x, sol)
                rhs_val = rhs.subs(x, sol)
                
                # Check if both sides are real and equal
                if lhs_val.is_real and rhs_val.is_real:
                    if abs(complex(lhs_val - rhs_val)) < 1e-10:
                        verified_solutions.append(sol)
            except:
                # If can't verify, include it
                verified_solutions.append(sol)
        
        expr = lhs - rhs
    else:
        try:
            expr = parse_expression(text)
        except:
            raise Exception("Could not parse radical expression")
        verified_solutions = []
        equation = None
    
    plot_data = generate_plot_data(expr, x, verified_solutions)
    
    return {
        'type': 'algebra_radical',
        'equation': str(equation) if '=' in latex_input else str(expr),
        'solutions': [str(s) for s in verified_solutions],
        'plot_data': plot_data,
        'latex': {
            'equation': sp.latex(equation) if '=' in latex_input else sp.latex(expr),
            'solutions': [sp.latex(s) for s in verified_solutions]
        }
    }
# CONTINUATION OF algebra.py - HELPER FUNCTIONS

def generate_complex_plane_plot(solutions):
    """Generate complex plane plot - FIXED"""
    real_parts = []
    imag_parts = []
    labels = []
    
    for sol in solutions:
        try:
            sol_complex = complex(sp.sympify(sol))
            real_parts.append(float(sol_complex.real))
            imag_parts.append(float(sol_complex.imag))
            labels.append(str(sol))
        except Exception as e:
            print(f"Complex plot error for {sol}: {e}")
    
    return {
        'type': 'complex_plane',
        'real': real_parts,
        'imag': imag_parts,
        'labels': labels
    }

def perform_algebraic_analysis(expr, x, solutions):
    """Comprehensive algebraic analysis - FIXED"""
    # Factoring
    try:
        factored_expr = factor(expr)
        factored_str = str(factored_expr)
    except:
        factored_expr = expr
        factored_str = str(expr)
    
    # Expansion
    try:
        expanded_expr = expand(expr)
        expanded_str = str(expanded_expr)
    except:
        expanded_expr = expr
        expanded_str = str(expr)
    
    # Simplification
    try:
        simplified_expr = simplify(expr)
        simplified_str = str(simplified_expr)
    except:
        simplified_expr = expr
        simplified_str = str(expr)
    
    # Separate real and complex solutions
    real_solutions = []
    complex_solutions = []
    
    for sol in solutions:
        try:
            sol_sympified = sp.sympify(sol)
            
            # Check if complex
            if sol_sympified.has(sp.I):
                complex_solutions.append(str(sol))
            elif sol_sympified.is_real:
                real_solutions.append(float(sol_sympified))
            else:
                # Try to convert to complex
                sol_complex = complex(sol_sympified)
                if abs(sol_complex.imag) < 1e-10:
                    real_solutions.append(float(sol_complex.real))
                else:
                    complex_solutions.append(str(sol))
        except:
            # Default to string representation
            real_solutions.append(str(sol))
    
    # Domain restrictions
    domain_restrictions = []
    try:
        numer, denom = expr.as_numer_denom()
        if denom != 1:
            restrictions = solve(denom, x)
            domain_restrictions = [f"x ≠ {float(r):.2f}" for r in restrictions if r.is_real]
    except:
        pass
    
    # Additional info
    additional_info = {}
    try:
        poly = Poly(expr, x)
        additional_info['degree'] = int(poly.degree())
        additional_info['leading_coefficient'] = float(poly.LC())
    except:
        pass
    
    # Check for rational expression
    numer, denom = expr.as_numer_denom()
    if denom != 1:
        additional_info['type'] = 'rational_expression'
        try:
            pfd = apart(expr, x)
            additional_info['partial_fractions'] = str(pfd)
        except:
            pass
    
    return {
        'solutions': [str(s) for s in solutions],
        'real_solutions': real_solutions,
        'complex_solutions': complex_solutions,
        'factored': factored_str,
        'factored_expr': factored_expr,
        'expanded': expanded_str,
        'simplified': simplified_str,
        'domain_restrictions': domain_restrictions,
        'additional_info': additional_info
    }

def classify_equation(expr, x):
    """Classify equation type - FIXED"""
    try:
        poly = Poly(expr, x)
        deg = poly.degree()
        
        if deg == 1:
            return "Linear Equation"
        elif deg == 2:
            return "Quadratic Equation"
        elif deg == 3:
            return "Cubic Equation"
        elif deg == 4:
            return "Quartic Equation"
        elif deg >= 5:
            return f"Polynomial Equation (degree {deg})"
    except:
        pass
    
    # Check for rational
    numer, denom = expr.as_numer_denom()
    if denom != 1:
        return "Rational Equation"
    
    # Check for absolute value
    if expr.has(Abs):
        return "Absolute Value Equation"
    
    # Check for radical
    if expr.has(sqrt):
        return "Radical Equation"
    
    return "Algebraic Expression"

def generate_plot_data(expr, x, solutions):
    """Generate standard plot data - FIXED for NaN handling"""
    x_vals = np.linspace(-10, 10, 500)
    
    try:
        f = sp.lambdify(x, expr, 'numpy')
        y_vals = f(x_vals)
        y_vals = np.where(np.isfinite(y_vals), y_vals, None)
        y_vals = np.clip(y_vals, -100, 100)
        
        # CRITICAL FIX: Convert numpy array to list and replace NaN/None with null
        y_vals_list = []
        for val in y_vals:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                y_vals_list.append(None)
            else:
                y_vals_list.append(float(val))
                
    except Exception as e:
        print(f"Plot generation error: {e}")
        y_vals_list = [None] * len(x_vals)
    
    # Solution points
    solution_points = []
    for sol in solutions:
        try:
            sol_float = float(complex(sp.sympify(sol)).real)
            if -10 <= sol_float <= 10:
                solution_points.append({'x': float(sol_float), 'y': 0.0})
        except:
            pass
    
    return {
        'x': x_vals.tolist(),
        'y': y_vals_list,  # Now properly serializable
        'solution_points': solution_points
    }

def normalize_latex_input(latex_input):
    """Normalize LaTeX input - FIXED"""
    text = latex_input.strip()
    
    # Remove LaTeX commands carefully
    text = text.replace('\\cdot', '*')
    text = text.replace('\\times', '*')
    text = text.replace('\\frac', 'frac')
    
    # Handle common LaTeX patterns
    # \frac{a}{b} -> (a)/(b)
    text = re.sub(r'frac\{([^}]+)\}\{([^}]+)\}', r'((\1)/(\2))', text)
    
    
    # Remove remaining braces for simple cases
    # But keep them for nested expressions
    # This is a simplified approach
    if text.count('{') < 5:  # Simple expression
        text = text.replace('{', '').replace('}', '')
    
    return text

def parse_expression(expr_string):
    """Parse expression with implicit multiplication - FIXED"""
    expr_string = expr_string.strip()
    
    # Handle exponents
    expr_string = expr_string.replace('^', '**')
    
    # REMOVE ALL WHITESPACE FIRST (this is the key fix)
    expr_string = expr_string.replace(' ', '')
    
    # Add implicit multiplication
    # number followed by letter: 2x -> 2*x
    expr_string = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_string)
    
    # ) followed by letter: )x -> )*x
    expr_string = re.sub(r'\)([a-zA-Z])', r')*\1', expr_string)
    
    # letter followed by (: x( -> x*(
    expr_string = re.sub(r'([a-zA-Z])\(', r'\1*(', expr_string)
    
    # number followed by (: 2( -> 2*(
    expr_string = re.sub(r'(\d)\(', r'\1*(', expr_string)
    
    # Handle fractions already converted
    expr_string = expr_string.replace('((', '(').replace('))', ')')
    
    try:
        return sp.sympify(expr_string, evaluate=False)
    except Exception as e:
        try:
            return sp.sympify(expr_string)
        except:
            raise Exception(f"Could not parse: {expr_string}. Error: {str(e)}")
        
def generate_plot_data_absolute(abs_expr, x, solutions, rhs_value):
    """Special plot for absolute value: shows |f(x)| and horizontal line y=rhs"""
    x_vals = np.linspace(-10, 10, 500)
    
    # Evaluate |2x - 3|
    f = sp.lambdify(x, abs_expr, 'numpy')
    y_vals = f(x_vals)
    y_vals = np.clip(y_vals, -100, 100)
    
    # Mark solution points
    solution_points = []
    for sol in solutions:
        try:
            sol_float = float(sol)
            if -10 <= sol_float <= 10:
                solution_points.append({
                    'x': float(sol_float), 
                    'y': float(rhs_value)  # Solutions are where |f(x)| = 5
                })
        except:
            pass
    
    # Convert y_vals to JSON-safe list
    y_list = []
    for v in y_vals:
        if np.isfinite(v):
            y_list.append(float(v))
        else:
            y_list.append(None)
    
    return {
        'x': x_vals.tolist(),
        'y': y_list,
        'solution_points': solution_points,
        'horizontal_line': float(rhs_value),  # This tells frontend to draw y=5 line
        'is_absolute_value': True  # Flag for frontend
    }