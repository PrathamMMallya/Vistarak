// Backend URL
const BACKEND_URL = 'http://localhost:8000/mathcompute';

// Check backend status on load
window.addEventListener('load', () => {
    checkBackendStatus();
    setupLatexPreview();
});

async function checkBackendStatus() {
    const statusDot = document.getElementById('backend-status');
    const statusText = document.getElementById('status-text');
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/health`);
        const data = await response.json();
        
        if (data.status === 'healthy') {
            statusDot.classList.remove('offline');
            statusDot.classList.add('online');
            statusText.textContent = 'Backend Online ✓';
        }
    } catch (error) {
        statusDot.classList.remove('online');
        statusDot.classList.add('offline');
        statusText.textContent = 'Backend Offline - Please start Flask server';
    }
}

function setupLatexPreview() {
    const input = document.getElementById('latex-input');
    const display = document.getElementById('latex-display');
    const moduleSelect = document.getElementById('module-select');
    const badge = document.getElementById('auto-detect-badge');
    
    input.addEventListener('input', () => {
        const latex = input.value.trim();
        
        if (latex) {
            // Try to render LaTeX
            try {
                // For function-style inputs, show them as code
                // For function-style inputs, show them as code
                if (latex.includes('(') && !latex.includes('\\') && !latex.includes('sqrt') && !latex.includes('vert')) {
                    display.textContent = latex;
                    display.style.fontFamily = 'monospace';
                    display.style.fontSize = '16px';
                    display.style.color = '#667eea';
                } else {
                    // Clean for preview
                    let previewLatex = latex;
                    // Keep LaTeX delimiters for preview
                    previewLatex = previewLatex.replace(/\\\[/g, '').replace(/\\\]/g, '');
                    
                    katex.render(previewLatex, display, {
                        throwOnError: false,
                        displayMode: true
                    });
                    display.style.fontFamily = '';
                    display.style.fontSize = '';
                    display.style.color = '';
                }
            } catch (e) {
                display.textContent = latex;
                display.style.fontFamily = 'monospace';
            }
            
            // Auto-detect module
            const detectedModule = detectModuleType(latex);
            if (moduleSelect.value === 'auto') {
                moduleSelect.value = detectedModule;
                badge.classList.add('show');
                badge.textContent = `Auto-detected: ${getModuleName(detectedModule)}`;
                
                // Add helpful hint
                addInputHint(latex, detectedModule);
            }
        } else {
            display.textContent = 'Type to preview...';
            display.style.fontFamily = '';
            display.style.color = '';
            badge.classList.remove('show');
            removeInputHint();
        }
    });
    
    moduleSelect.addEventListener('change', () => {
        if (moduleSelect.value !== 'auto') {
            badge.classList.remove('show');
            removeInputHint();
        } else {
            const latex = input.value.trim();
            if (latex) {
                const detectedModule = detectModuleType(latex);
                badge.classList.add('show');
                badge.textContent = `Auto-detected: ${getModuleName(detectedModule)}`;
                addInputHint(latex, detectedModule);
            }
        }
    });
}

function addInputHint(latex, moduleType) {
    removeInputHint(); // Remove existing hint
    
    const hintDiv = document.createElement('div');
    hintDiv.id = 'input-hint';
    hintDiv.style.cssText = `
        margin-top: 10px;
        padding: 10px;
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        border-radius: 4px;
        font-size: 14px;
        color: #2e7d32;
    `;
    
    let hintText = '';
    const lower = latex.toLowerCase();
    
    if (moduleType === 'geometry') {
        if (lower.includes('distance(')) {
            hintText = '💡 Distance formula: √[(x₂-x₁)² + (y₂-y₁)²]';
        } else if (lower.includes('midpoint(')) {
            hintText = '💡 Midpoint formula: ((x₁+x₂)/2, (y₁+y₂)/2)';
        } else if (lower.includes('circle(')) {
            hintText = '💡 Circle: Center-radius form';
        } else if (lower.includes('pythagoras(')) {
            hintText = '💡 Pythagoras: a² + b² = c²';
        } else if (lower.includes('triangle(')) {
            hintText = '💡 Triangle analysis: Type, area, perimeter';
        } else if (lower.includes('cube(') || lower.includes('sphere(')) {
            hintText = '💡 3D visualization with surface area & volume';
        } else if (lower.includes('x^2') && lower.includes('y^2') && lower.includes('=')) {
            hintText = '💡 Conic section: Likely a circle or ellipse';
        }
    }
    
    if (hintText) {
        hintDiv.textContent = hintText;
        const display = document.getElementById('latex-display');
        display.parentNode.insertBefore(hintDiv, display.nextSibling);
    }
}

function removeInputHint() {
    const existingHint = document.getElementById('input-hint');
    if (existingHint) {
        existingHint.remove();
    }
}

function detectModuleType(latex) {
    const lower = latex.toLowerCase();
    
    // ============================================
    // 1. VECTORS (Highest priority - most specific)
    // ============================================
    if (lower.includes('\\hat{i}') || lower.includes('\\hat{j}') || lower.includes('\\hat{k}') ||
        lower.includes('\\vec') || 
        (/\bi\b/.test(lower) && /\bj\b/.test(lower)) || 
        (/\bi\b/.test(lower) && /\bk\b/.test(lower))) {
        return 'vectors';
    }
    
    // ============================================
    // 2. GEOMETRY FUNCTIONS (Check before equations)
    // ============================================
    
    // 3D Solids
    if (/\b(cube|cuboid|cylinder|cone|sphere|hemisphere)\s*\(/.test(lower)) {
        return 'geometry';
    }
    
    // 2D Mensuration
    if (/\b(rectangle|square|circle_area|circle_circumference)\s*\(/.test(lower)) {
        return 'geometry';
    }
    
    // Circle operations
    if (/\b(circle|tangent_length|chord)\s*\(/.test(lower)) {
        return 'geometry';
    }
    
    // Triangle operations
    if (/\b(triangle|pythagoras|centroid|circumcenter|incenter|orthocenter)\s*\(/.test(lower)) {
        return 'geometry';
    }
    
    // Coordinate geometry operations
    if (/\b(distance|midpoint|slope|line|area_triangle|collinear)\s*\(/.test(lower)) {
        return 'geometry';
    }
    
    // ============================================
    // 3. GEOMETRY EQUATIONS (x^2 + y^2 = 25)
    // ============================================
    if ((lower.includes('x') && lower.includes('y')) && lower.includes('=')) {
        // Check if it's a geometry equation (both x and y present)
        if (lower.includes('x^2') || lower.includes('y^2') || 
            lower.includes('x^{2}') || lower.includes('y^{2}')) {
            return 'geometry';
        }
        // Simple line equation like y = 2x + 3
        if (/y\s*=.*x/.test(lower) && !lower.includes('^')) {
            return 'geometry';
        }
    }
    
    // ============================================
    // 4. CALCULUS (Check after geometry)
    // ============================================
    if (lower.includes('sin(') || lower.includes('cos(') || lower.includes('tan(') ||
        lower.includes('\\sin') || lower.includes('\\cos') || lower.includes('\\tan') ||
        lower.includes('\\frac{d') || lower.includes('\\int') || 
        lower.includes('\\ln') || lower.includes('\\log') || lower.includes('ln(') || lower.includes('log(') ||
        lower.includes('e^') || lower.includes('exp(')) {
        return 'calculus';
    }
    
    // ============================================
    // 5. ALGEBRA (Default for equations)
    // ============================================
    if (lower.includes('=') || /x\^[\d{]/.test(lower) || /[a-z]\^/.test(lower)) {
        return 'algebra';
    }
    
    // Default to calculus for single variable functions
    return 'calculus';
}

function getModuleName(moduleType) {
    const names = {
        'calculus': 'Calculus',
        'algebra': 'Algebra',
        'geometry': 'Geometry',
        'vectors': '3D Vectors'
    };
    return names[moduleType] || moduleType;
}

async function visualize() {
    const latexInput = document.getElementById('latex-input').value.trim();
    let moduleType = document.getElementById('module-select').value;
    const errorDiv = document.getElementById('error-message');
    const resultsSection = document.getElementById('results-section');
    const visualizeBtn = document.getElementById('visualize-btn');
    
    errorDiv.classList.remove('show');
    errorDiv.textContent = '';
    
    if (!latexInput) {
        showError('Please enter a LaTeX expression');
        return;
    }
    
    if (moduleType === 'auto') {
        moduleType = detectModuleType(latexInput);
    }
    
    visualizeBtn.disabled = true;
    visualizeBtn.textContent = '⏳ Processing...';
    
    try {
        const response = await fetch(`${BACKEND_URL}/api/visualize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latex: latexInput,
                module: moduleType
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Unknown error occurred');
        }
        
        displayResults(result.data, moduleType);
        resultsSection.classList.add('show');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        showError(`Error: ${error.message}`);
        console.error('Visualization error:', error);
    } finally {
        visualizeBtn.disabled = false;
        visualizeBtn.textContent = '🚀 Visualize';
    }
}

function displayResults(data, moduleType) {
    const infoPanel = document.getElementById('info-panel');
    const plotDiv = document.getElementById('plot');
    
    infoPanel.innerHTML = '';
    
    if (moduleType === 'calculus') {
        displayCalculusResults(data, infoPanel, plotDiv);
    } else if (moduleType === 'algebra') {
        displayAlgebraResults(data, infoPanel, plotDiv);
    } else if (moduleType === 'geometry') {
        displayGeometryResults(data, infoPanel, plotDiv);
    } else if (moduleType === 'vectors') {
        displayVectorResults(data, infoPanel, plotDiv);
    }
}

// Keep other display functions

function displayVectorResults(data, infoPanel, plotDiv) {
    let infoHTML = '';
    
    if (data.type === 'vector_single') {
        infoHTML = `
            <div class="info-item">
                <div class="info-label">Vector:</div>
                <div class="info-value">${formatVector(data.vector)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Magnitude:</div>
                <div class="info-value">${data.magnitude.toFixed(3)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Unit Vector:</div>
                <div class="info-value">${formatVector(data.unit_vector)}</div>
            </div>
        `;
    } else if (data.type === 'vector_pair') {
        infoHTML = `
            <div class="info-item">
                <div class="info-label">Vector 1:</div>
                <div class="info-value">${formatVector(data.vector1)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Vector 2:</div>
                <div class="info-value">${formatVector(data.vector2)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Dot Product:</div>
                <div class="info-value">${data.dot_product.toFixed(3)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Cross Product:</div>
                <div class="info-value">${formatVector(data.cross_product)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Angle:</div>
                <div class="info-value">${data.angle_degrees.toFixed(2)}° (${data.angle_radians.toFixed(3)} rad)</div>
            </div>
        `;
    }
    
    infoPanel.innerHTML = infoHTML;
    
    const traces = data.plot_data.vectors.map(vec => {
        return {
            type: 'scatter3d',
            mode: 'lines+markers',
            x: [vec.origin[0], vec.origin[0] + vec.vector[0]],
            y: [vec.origin[1], vec.origin[1] + vec.vector[1]],
            z: [vec.origin[2], vec.origin[2] + vec.vector[2]],
            name: vec.label,
            line: { width: 6, color: vec.color || '#667eea' },
            marker: { size: 8 }
        };
    });
    
    const layout = {
        title: '3D Vector Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'cube'
        },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function formatVector(vec) {
    return `[${vec.map(v => v.toFixed(2)).join(', ')}]`;
}

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}




// STATISTICS

// ============================================================================
// STATISTICS CALCULATION HANDLER
// Add this to your app.js or create a separate stats-handler.js
// ============================================================================

async function calculateStatistics() {
    const errorDiv = document.getElementById('stats-error-message');
    const resultsSection = document.getElementById('stats-results-section');
    const calculateBtn = document.getElementById('stats-calculate-btn');
    
    errorDiv.classList.remove('show');
    errorDiv.textContent = '';
    
    if (!currentStatsOperation) {
        showStatsError('Please select an operation');
        return;
    }
    
    calculateBtn.disabled = true;
    calculateBtn.textContent = '⏳ Calculating...';
    
    try {
        const requestData = buildStatsRequest();
        
        const response = await fetch(`${BACKEND_URL}/api/statistics`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Calculation failed');
        }
        
        // Display results
        const infoPanel = document.getElementById('stats-info-panel');
        const plotDiv = document.getElementById('stats-plot');
        
        displayStatisticsResults(result.data, infoPanel, plotDiv);
        
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        showStatsError(`Error: ${error.message}`);
        console.error('Statistics calculation error:', error);
    } finally {
        calculateBtn.disabled = false;
        calculateBtn.textContent = '🚀 Calculate';
    }
}

function buildStatsRequest() {
    switch(currentStatsOperation) {
        case 'descriptive':
            return {
                operation: 'descriptive',
                data: document.getElementById('stats-data').value.trim()
            };
            
        case 'normal':
            const normalData = {
                operation: 'normal_distribution',
                params: {
                    mean: parseFloat(document.getElementById('normal-mean').value),
                    std: parseFloat(document.getElementById('normal-std').value)
                }
            };
            const xValue = document.getElementById('normal-x').value.trim();
            if (xValue) {
                normalData.params.x_value = parseFloat(xValue);
            }
            return normalData;
            
        case 'binomial':
            return {
                operation: 'binomial_distribution',
                params: {
                    n: parseInt(document.getElementById('binomial-n').value),
                    p: parseFloat(document.getElementById('binomial-p').value)
                }
            };
            
        case 'poisson':
            return {
                operation: 'poisson_distribution',
                params: {
                    lambda: parseFloat(document.getElementById('poisson-lambda').value)
                }
            };
            
        case 'hypothesis':
            const testType = document.getElementById('hypothesis-type').value;
            const hypothesisData = {
                operation: 'hypothesis_test',
                params: {
                    test_type: testType,
                    alpha: parseFloat(document.getElementById('hypothesis-alpha').value)
                }
            };
            
            if (testType === 'two_sample_t') {
                hypothesisData.params.data1 = document.getElementById('hypothesis-data1').value.trim();
                hypothesisData.params.data2 = document.getElementById('hypothesis-data2').value.trim();
            } else {
                hypothesisData.params.data = document.getElementById('hypothesis-data').value.trim();
                hypothesisData.params.mu_0 = parseFloat(document.getElementById('hypothesis-mu0').value);
                
                if (testType === 'z_test') {
                    hypothesisData.params.sigma = parseFloat(document.getElementById('hypothesis-sigma').value);
                }
            }
            
            return hypothesisData;
            
        case 'regression':
            const regressionType = document.getElementById('regression-type').value;
            const regressionData = {
                operation: 'regression',
                params: {
                    regression_type: regressionType,
                    x_data: document.getElementById('regression-x').value.trim(),
                    y_data: document.getElementById('regression-y').value.trim()
                }
            };
            
            if (regressionType === 'polynomial') {
                regressionData.params.degree = parseInt(document.getElementById('poly-degree').value);
            }
            
            return regressionData;
            
        case 'correlation':
            return {
                operation: 'correlation',
                params: {
                    x_data: document.getElementById('correlation-x').value.trim(),
                    y_data: document.getElementById('correlation-y').value.trim()
                }
            };
            
        default:
            throw new Error('Unknown operation');
    }
}

function showStatsError(message) {
    const errorDiv = document.getElementById('stats-error-message');
    errorDiv.textContent = message;
    errorDiv.classList.add('show');
}

// Update your existing switchTab function to handle statistics tab
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tab + '-tab').classList.add('active');
    
    // Reset statistics state when switching tabs
    if (tab !== 'statistics') {
        currentStatsOperation = null;
        document.querySelectorAll('.operation-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.getElementById('stats-input-section').style.display = 'none';
        document.getElementById('stats-calculate-btn').style.display = 'none';
        document.getElementById('stats-results-section').style.display = 'none';
    }
}