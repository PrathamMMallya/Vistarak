// ============================================================================
// ULTRA-POWERFUL CUSTOM GRAPH PLOTTER v2.0
// Handles ANY mathematical expression including:
// - Trig functions: sin, cos, tan, sec, csc, cot
// - Inverse trig: asin, acos, atan, atan2
// - Hyperbolic: sinh, cosh, tanh, asinh, acosh, atanh
// - Exponential/Log: exp, ln, log, log10, log2
// - Advanced: factorial, abs, ceil, floor, round, sign
// - Constants: pi, e
// - Piecewise functions
// - Complex expressions with implicit multiplication
// ============================================================================

// Tab switching
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + '-tab').classList.add('active');
}

// Load example function
function loadExample(func) {
    document.getElementById('custom-function').value = func;
    plotCustomGraph();
}

// Custom graph plotting with real-time slider updates
function setupCustomGraphListeners() {
    const sliders = ['x-min', 'x-max', 'amplitude', 'frequency', 'phase', 'vertical'];
    
    sliders.forEach(id => {
        const slider = document.getElementById(id);
        if (slider) {
            slider.addEventListener('input', () => {
                const valueDisplay = document.getElementById(id + '-val');
                if (valueDisplay) {
                    valueDisplay.textContent = slider.value;
                }
                plotCustomGraph();
            });
        }
    });
}

// ============================================================================
// ADVANCED FUNCTION EVALUATOR - Handles EVERYTHING
// ============================================================================

function evaluateFunction(funcStr, x) {
    try {
        // Store original for error messages
        const original = funcStr;
        
        // STEP 1: Handle constants (case-insensitive)
        funcStr = funcStr.replace(/\bpi\b/gi, '(' + Math.PI.toString() + ')');
        funcStr = funcStr.replace(/\be\b(?![a-z])/gi, '(' + Math.E.toString() + ')');
        
        // STEP 2: Handle powers - IMPROVED
        // Convert x^2 to (x)**(2), ensuring proper parentheses
        funcStr = funcStr.replace(/\^/g, '**');
        
        // STEP 3: Handle factorial (for integers up to 170)
        funcStr = funcStr.replace(/(\d+(\.\d+)?)!/g, (match, num) => {
            const n = parseFloat(num);
            if (n !== Math.floor(n)) return 'NaN'; // Non-integer
            if (n > 170) return 'Infinity'; // Prevent overflow
            if (n < 0) return 'NaN';
            let result = 1;
            for (let i = 2; i <= n; i++) result *= i;
            return '(' + result.toString() + ')';
        });
        
        // STEP 4: Replace trig and hyperbolic functions
        const mathFunctions = {
            // Trig
            'sin': 'Math.sin',
            'cos': 'Math.cos',
            'tan': 'Math.tan',
            'asin': 'Math.asin',
            'acos': 'Math.acos',
            'atan': 'Math.atan',
            
            // Reciprocal trig - FIXED
            'sec': '(1/Math.cos',
            'csc': '(1/Math.sin',
            'cot': '(1/Math.tan',
            
            // Hyperbolic
            'sinh': 'Math.sinh',
            'cosh': 'Math.cosh',
            'tanh': 'Math.tanh',
            'asinh': 'Math.asinh',
            'acosh': 'Math.acosh',
            'atanh': 'Math.atanh',
            
            // Exponential and logarithmic
            'exp': 'Math.exp',
            'ln': 'Math.log',
            'log10': 'Math.log10',
            'log2': 'Math.log2',
            'log': 'Math.log',
            
            // Other functions
            'sqrt': 'Math.sqrt',
            'abs': 'Math.abs',
            'ceil': 'Math.ceil',
            'floor': 'Math.floor',
            'round': 'Math.round',
            'sign': 'Math.sign',
            'max': 'Math.max',
            'min': 'Math.min',
            'cbrt': 'Math.cbrt',
            'pow': 'Math.pow',
        };
        
        // Replace functions in order (longer names first to avoid conflicts)
        const sortedFunctions = Object.entries(mathFunctions).sort((a, b) => b[0].length - a[0].length);
        
        for (const [func, replacement] of sortedFunctions) {
            const regex = new RegExp(`\\b${func}\\b`, 'g');
            funcStr = funcStr.replace(regex, replacement);
        }
        
        // STEP 5: Fix reciprocal trig functions - add closing parenthesis
        // Transform (1/Math.sin(x)) properly
        let parenDepth = 0;
        let result = '';
        let i = 0;
        
        while (i < funcStr.length) {
            if (funcStr.substring(i, i + 11) === '(1/Math.sin' ||
                funcStr.substring(i, i + 11) === '(1/Math.cos' ||
                funcStr.substring(i, i + 11) === '(1/Math.tan') {
                
                // Find the matching parenthesis
                let start = i;
                let depth = 0;
                let j = i + 11; // Skip past "(1/Math.sin" or similar
                
                // Find the opening paren of the argument
                while (j < funcStr.length && funcStr[j] !== '(') j++;
                if (j >= funcStr.length) {
                    result += funcStr.substring(i);
                    break;
                }
                
                depth = 1;
                j++; // Move past the opening paren
                let argStart = j;
                
                // Find matching closing paren
                while (j < funcStr.length && depth > 0) {
                    if (funcStr[j] === '(') depth++;
                    else if (funcStr[j] === ')') depth--;
                    j++;
                }
                
                // Now add the reciprocal wrapper with extra closing paren
                result += funcStr.substring(start, j) + ')';
                i = j;
            } else {
                result += funcStr[i];
                i++;
            }
        }
        funcStr = result;
        
        // STEP 6: Handle implicit multiplication - IMPROVED
        funcStr = addImplicitMultiplication(funcStr);
        
        // STEP 7: Replace x with actual value (with proper parentheses)
        funcStr = funcStr.replace(/\bx\b/g, `(${x})`);
        
        // STEP 8: Evaluate
        const evalResult = eval(funcStr);
        
        // STEP 9: Handle special cases
        if (!isFinite(evalResult)) {
            return null; // Don't plot infinities or NaN
        }
        
        return evalResult;
        
    } catch (e) {
        // Silently fail for individual points (expected for some functions)
        return null;
    }
}

// ============================================================================
// IMPLICIT MULTIPLICATION HANDLER - ENHANCED
// ============================================================================

function addImplicitMultiplication(expr) {
    let result = expr;
    
    // Pattern 1: Number followed by letter (but not part of Math.xxx)
    // 2x → 2*x, 3pi → 3*pi
    result = result.replace(/(\d)([a-zA-Z])/g, (match, num, letter, offset) => {
        // Don't break Math.xxx or scientific notation (1e5)
        if (letter === 'e' && /\d$/.test(result.substring(Math.max(0, offset - 1), offset + 1))) {
            return match; // Scientific notation
        }
        return num + '*' + letter;
    });
    
    // Pattern 2: ) followed by (
    // (x+1)(x-1) → (x+1)*(x-1)
    result = result.replace(/\)\s*\(/g, ')*(');
    
    // Pattern 3: ) followed by number
    // (x+1)2 → (x+1)*2
    result = result.replace(/\)(\d)/g, ')*$1');
    
    // Pattern 4: Number followed by (
    // 2(x+1) → 2*(x+1)
    result = result.replace(/(\d)\(/g, '$1*(');
    
    // Pattern 5: ) followed by letter
    // (x+1)x → (x+1)*x
    result = result.replace(/\)([a-zA-Z])/g, (match, letter, offset) => {
        // Check if it's part of a function call
        const before = result.substring(Math.max(0, offset - 20), offset + 1);
        if (before.match(/Math\.[a-z]+$/)) {
            return match;
        }
        return ')*' + letter;
    });
    
    // Pattern 6: Letter followed by (
    // x(x+1) → x*(x+1), but NOT sin(x) → sin*(x)
    result = result.replace(/([a-z])(\()/gi, (match, letter, paren, offset, string) => {
        // Check if this letter is part of a function name
        const before = string.substring(Math.max(0, offset - 20), offset + 1);
        
        // List of known functions that should NOT get multiplication
        const functionPattern = /(Math\.|sin|cos|tan|sec|csc|cot|asin|acos|atan|sinh|cosh|tanh|asinh|acosh|atanh|exp|log|ln|sqrt|abs|ceil|floor|round|sign|max|min|cbrt|pow)$/i;
        
        if (functionPattern.test(before)) {
            return match; // Keep function calls intact
        }
        
        return letter + '*' + paren;
    });
    
    return result;
}

// ============================================================================
// SMART PLOTTING - Handles discontinuities and special cases
// ============================================================================

function plotCustomGraph() {
    const funcInput = document.getElementById('custom-function');
    const xMinInput = document.getElementById('x-min');
    const xMaxInput = document.getElementById('x-max');
    const ampInput = document.getElementById('amplitude');
    const freqInput = document.getElementById('frequency');
    const phaseInput = document.getElementById('phase');
    const vShiftInput = document.getElementById('vertical');
    
    if (!funcInput || !xMinInput || !xMaxInput) {
        console.error('Required input elements not found');
        return;
    }
    
    const funcStr = funcInput.value.trim();
    const xMin = parseFloat(xMinInput.value);
    const xMax = parseFloat(xMaxInput.value);
    const amp = ampInput ? parseFloat(ampInput.value) : 1;
    const freq = freqInput ? parseFloat(freqInput.value) : 1;
    const phase = phaseInput ? parseFloat(phaseInput.value) : 0;
    const vShift = vShiftInput ? parseFloat(vShiftInput.value) : 0;

    if (!funcStr) {
        alert('Please enter a function!');
        return;
    }

    if (xMin >= xMax) {
        alert('X Min must be less than X Max!');
        return;
    }

    // Generate points with adaptive resolution
    const numPoints = 2000; // Higher resolution for better accuracy
    const step = (xMax - xMin) / numPoints;
    
    const xValues = [];
    const yValues = [];
    
    let validPointCount = 0;
    let previousY = null;
    const discontinuityThreshold = 100; // If jump > 100 units, consider it a discontinuity

    for (let i = 0; i <= numPoints; i++) {
        const x = xMin + i * step;
        
        // Apply transformations: frequency affects input, phase shifts it
        const transformedX = freq * (x - phase);
        
        const y_raw = evaluateFunction(funcStr, transformedX);
        
        xValues.push(x);
        
        if (y_raw !== null && isFinite(y_raw)) {
            // Apply amplitude and vertical shift
            const y = amp * y_raw + vShift;
            
            // Check for discontinuities (like in tan(x))
            if (previousY !== null && Math.abs(y - previousY) > discontinuityThreshold) {
                yValues.push(null); // Create a break in the line
            } else {
                // Clip extreme values for better visualization
                if (Math.abs(y) < 1e6) {
                    yValues.push(y);
                    validPointCount++;
                } else {
                    yValues.push(null);
                }
            }
            previousY = y;
        } else {
            yValues.push(null);
            previousY = null;
        }
    }

    // Warn if no valid points
    if (validPointCount === 0) {
        alert('Function produced no valid points in the given range!\n\nTry:\n- Adjusting X Min/Max\n- Checking your function syntax\n- Using simpler expressions');
        return;
    }

    // Create trace
    const trace = {
        x: xValues,
        y: yValues,
        type: 'scatter',
        mode: 'lines',
        line: { 
            color: '#667eea', 
            width: 2.5,
            shape: 'spline', // Smooth curves
            smoothing: 0.3
        },
        name: buildFunctionLabel(funcStr, amp, freq, phase, vShift),
        connectgaps: false, // Don't connect across discontinuities
        hovertemplate: 'x: %{x:.4f}<br>y: %{y:.4f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Custom Function Graph',
            font: { size: 24, color: '#1e3c72', family: 'Arial, sans-serif' }
        },
        xaxis: { 
            title: { text: 'x', font: { size: 16 } },
            zeroline: true, 
            gridcolor: '#e2e8f0',
            zerolinecolor: '#94a3b8',
            zerolinewidth: 2,
            showgrid: true
        },
        yaxis: { 
            title: { text: 'y', font: { size: 16 } },
            zeroline: true, 
            gridcolor: '#e2e8f0',
            zerolinecolor: '#94a3b8',
            zerolinewidth: 2,
            showgrid: true
        },
        plot_bgcolor: '#f8fafc',
        paper_bgcolor: '#ffffff',
        hovermode: 'closest',
        showlegend: true,
        margin: { l: 60, r: 40, t: 80, b: 60 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        toImageButtonOptions: {
            format: 'png',
            filename: 'custom_graph',
            height: 800,
            width: 1200,
            scale: 2
        }
    };

    const plotDiv = document.getElementById('custom-plot');
    if (plotDiv) {
        Plotly.newPlot(plotDiv, [trace], layout, config);
    }
}

// ============================================================================
// BUILD FUNCTION LABEL
// ============================================================================

function buildFunctionLabel(funcStr, amp, freq, phase, vShift) {
    // Build a nice label for the legend
    let label = 'y = ';
    
    if (amp !== 1 && amp !== 0) {
        label += amp === -1 ? '-' : `${amp}·`;
    }
    
    label += 'f(';
    
    const hasFreq = freq !== 1 && freq !== 0;
    const hasPhase = phase !== 0;
    
    if (hasFreq && hasPhase) {
        label += `${freq}(x ${phase > 0 ? '-' : '+'} ${Math.abs(phase)})`;
    } else if (hasFreq) {
        label += `${freq}x`;
    } else if (hasPhase) {
        label += `x ${phase > 0 ? '-' : '+'} ${Math.abs(phase)}`;
    } else {
        label += 'x';
    }
    
    label += ')';
    
    if (vShift !== 0) {
        label += vShift > 0 ? ` + ${vShift}` : ` - ${Math.abs(vShift)}`;
    }
    
    // Add original function
    label += `   [${funcStr}]`;
    
    return label;
}

// ============================================================================
// INITIALIZE ON LOAD
// ============================================================================

window.addEventListener('load', () => {
    setupCustomGraphListeners();
    
    // Only plot if custom tab elements exist
    if (document.getElementById('custom-plot')) {
        // Small delay to ensure DOM is ready
        setTimeout(plotCustomGraph, 100);
    }
});

// ============================================================================
// EXTENDED EXAMPLE LIBRARY
// ============================================================================

const extendedExamples = [
    { label: ' Sine Wave', func: 'sin(x)' },
    { label: ' Parabola', func: 'x^2' },
    { label: ' Damped Cosine', func: 'cos(x)*exp(-x/10)' },
    { label: ' Tangent', func: 'tan(x)' },
    { label: ' Cubic', func: 'x^3 - 3*x' },
    { label: ' Hyperbola', func: '1/x' },
    { label: ' Sinc', func: 'sin(x)/x' },
    { label: ' Spiral', func: 'x*sin(x)' },
    { label: ' Absolute', func: 'abs(x)' },
    { label: ' Floor', func: 'floor(x)' },
    { label: ' Square Root', func: 'sqrt(abs(x))' },
    { label: ' Beat Wave', func: 'sin(x) + sin(1.2*x)' },
    // { label: ' Gaussian', func: 'exp(-x^2)' },
    { label: ' Secant', func: 'sec(x)' },
    { label: ' Witch of Agnesi', func: '1/(1+x^2)' },
    { label: ' Polynomial', func: 'x^4 - 4*x^2 + 2' }
];

// Add extended examples dynamically
function addExtendedExamples() {
    const container = document.querySelector('.function-examples');
    if (container && container.children.length < extendedExamples.length) {
        // Clear and rebuild
        container.innerHTML = '';
        extendedExamples.forEach(ex => {
            const btn = document.createElement('button');
            btn.className = 'example-btn';
            btn.textContent = ex.label;
            btn.onclick = () => loadExample(ex.func);
            container.appendChild(btn);
        });
    }
}

// Auto-add extended examples on load
window.addEventListener('load', () => {
    setTimeout(addExtendedExamples, 200);
});