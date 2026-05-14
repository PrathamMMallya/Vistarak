function displayAlgebraResults(data, infoPanel, plotDiv) {
    // System of equations (both linear and nonlinear)
    if (data.type === 'algebra_system') {
        let solutionHTML = '';
        if (Array.isArray(data.solution) && data.solution.length > 0) {
            solutionHTML = data.solution.map((sol, idx) => {
                if (typeof sol === 'object' && sol !== null) {
                    const entries = Object.entries(sol).map(([k, v]) => {
                        const varName = k.toString();
                        const value = typeof v === 'number' ? v.toFixed(4) : v;
                        return `${varName} = ${value}`;
                    }).join(', ');
                    return `<div>Solution ${idx + 1}: ${entries}</div>`;
                }
                return `<div>Solution ${idx + 1}: ${JSON.stringify(sol)}</div>`;
            }).join('');
        } else {
            solutionHTML = '<div style="color: #f44336;">No solution found</div>';
        }
        
        infoPanel.innerHTML = `
            <div class="info-item">
                <div class="info-label">System Type:</div>
                <div class="info-value">${data.system_size} System ${data.is_nonlinear ? '(Nonlinear)' : '(Linear)'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Solution Method:</div>
                <div class="info-value">${data.solution_method}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Equations:</div>
                <div class="info-value" id="sys-equations"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Solution:</div>
                <div class="info-value">${solutionHTML}</div>
            </div>
        `;
        
        const eqDiv = document.getElementById('sys-equations');
        if (eqDiv && data.latex && data.latex.equations) {
            data.latex.equations.forEach(eq => {
                const div = document.createElement('div');
                try {
                    katex.render(eq, div, { throwOnError: false });
                } catch (e) {
                    div.textContent = eq;
                }
                eqDiv.appendChild(div);
            });
        }
        
        // Plot system
        if (data.plot_data) {
            if (data.plot_data.type === 'system_2d_nonlinear') {
                plotNonlinearSystem(data.plot_data, plotDiv);
            } else if (data.plot_data.type === 'system_2d') {
                plotLinearSystem(data.plot_data, plotDiv);
            }
        } else {
            plotDiv.innerHTML = '<p style="text-align:center; padding:50px; color:#666;">System solved (3+ variables - no visualization)</p>';
        }
        return;
    }
    
    // UPDATED: Inequality - REMOVED interval solution and sign chart
    if (data.type === 'algebra_inequality') {
        infoPanel.innerHTML = `
            <div class="info-item">
                <div class="info-label">Type:</div>
                <div class="info-value">${data.is_rational ? 'Rational Inequality' : 'Polynomial Inequality'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Inequality:</div>
                <div class="info-value" id="ineq-expr"></div>
            </div>
            ${data.critical_points && data.critical_points.length > 0 ? `
            <div class="info-item">
                <div class="info-label">Critical Points:</div>
                <div class="info-value" style="font-family: monospace; font-size: 16px;">${data.critical_points.map(cp => cp.toFixed(2)).join(', ')}</div>
            </div>
            ` : ''}
        `;
        
        const ineqDiv = document.getElementById('ineq-expr');
        if (ineqDiv && data.latex && data.latex.inequality) {
            try {
                katex.render(data.latex.inequality, ineqDiv, { throwOnError: false });
            } catch (e) {
                ineqDiv.textContent = data.inequality;
            }
        }
        
        plotInequalityAdvanced(data.plot_data, plotDiv);
        return;
    }
    
    // UPDATED: Absolute value / Radical - REMOVED solutions text
    if (data.type === 'algebra_absolute' || data.type === 'algebra_radical') {
        const typeLabel = data.type === 'algebra_absolute' ? 'Absolute Value' : 'Radical';
        
        infoPanel.innerHTML = `
            <div class="info-item">
                <div class="info-label">Type:</div>
                <div class="info-value">${typeLabel} Equation</div>
            </div>
            <div class="info-item">
                <div class="info-label">Equation:</div>
                <div class="info-value" id="special-eq"></div>
            </div>
        `;
        
        const eqDiv = document.getElementById('special-eq');
        if (eqDiv && data.latex && data.latex.equation) {
            try {
                katex.render(data.latex.equation, eqDiv, { throwOnError: false });
            } catch (e) {
                eqDiv.textContent = data.equation || '';
            }
        }
        
        plotStandardAlgebra(data.plot_data, plotDiv, typeLabel);
        return;
    }
    
    // Regular algebra
    let additionalInfo = '';
    if (data.analysis && typeof data.analysis === 'object' && Object.keys(data.analysis).length > 0) {
        if (data.analysis.degree) {
            additionalInfo += `<div><strong>Degree:</strong> ${data.analysis.degree}</div>`;
        }
        if (data.analysis.partial_fractions) {
            additionalInfo += `<div><strong>Partial Fractions:</strong> ${data.analysis.partial_fractions}</div>`;
        }
    }
    
    const realSolutions = Array.isArray(data.real_solutions) && data.real_solutions.length > 0 
        ? data.real_solutions.map(s => typeof s === 'number' ? s.toFixed(4) : s).join(', ')
        : '';
    
    const complexSolutions = Array.isArray(data.complex_solutions) && data.complex_solutions.length > 0
        ? data.complex_solutions.join(', ')
        : '';
    
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Equation Type:</div>
            <div class="info-value">${data.equation_type || 'Expression'}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Expression:</div>
            <div class="info-value" id="alg-expression"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Factored Form:</div>
            <div class="info-value" id="alg-factored"></div>
        </div>
        ${realSolutions ? `
        <div class="info-item">
            <div class="info-label">Real Solutions:</div>
            <div class="info-value">${realSolutions}</div>
        </div>
        ` : ''}
        ${complexSolutions ? `
        <div class="info-item">
            <div class="info-label">Complex Solutions:</div>
            <div class="info-value">${complexSolutions}</div>
        </div>
        ` : ''}
        ${additionalInfo ? `<div class="info-item"><div class="info-label">Additional:</div><div class="info-value">${additionalInfo}</div></div>` : ''}
    `;
    
    const exprDiv = document.getElementById('alg-expression');
    if (exprDiv && data.latex && data.latex.expression) {
        try {
            katex.render(data.latex.expression, exprDiv, { throwOnError: false });
        } catch (e) {
            exprDiv.textContent = data.original_expression || '';
        }
    }
    
    const factDiv = document.getElementById('alg-factored');
    if (factDiv && data.latex && data.latex.factored) {
        try {
            katex.render(data.latex.factored, factDiv, { throwOnError: false });
        } catch (e) {
            factDiv.textContent = data.factored || '';
        }
    }
    
    // Plot
    if (data.plot_data && data.plot_data.plot_type === 'complex_plane') {
        plotComplexPlane(data.plot_data, plotDiv);
    } else if (data.plot_data) {
        plotStandardAlgebra(data.plot_data, plotDiv, data.equation_type || 'Expression');
    }
}

function plotLinearSystem(plotData, plotDiv) {
    if (!plotData || !plotData.lines) {
        plotDiv.innerHTML = '<p style="text-align:center; padding:50px;">No plot data available</p>';
        return;
    }
    
    const traces = plotData.lines.map(line => ({
        x: line.x || [],
        y: line.y || [],
        name: line.name || 'Line',
        type: 'scatter',
        mode: 'lines',
        line: { width: 3 }
    }));
    
    if (plotData.solution_point && plotData.solution_point.x !== undefined) {
        traces.push({
            x: [plotData.solution_point.x],
            y: [plotData.solution_point.y],
            mode: 'markers',
            name: 'Solution',
            marker: { size: 15, color: 'red', symbol: 'x' }
        });
    }
    
    const layout = {
        title: 'Linear System of Equations',
        xaxis: { title: 'x', zeroline: true },
        yaxis: { title: 'y', zeroline: true },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotNonlinearSystem(plotData, plotDiv) {
    if (!plotData || !plotData.contours) {
        plotDiv.innerHTML = '<p style="text-align:center; padding:50px;">No plot data available</p>';
        return;
    }
    
    const traces = [];
    
    // Add contour plots for each equation
    plotData.contours.forEach((contour, idx) => {
        if (contour.x && contour.y && contour.z) {
            traces.push({
                x: contour.x[0] || [],
                y: (contour.y[0] || []).map((_, i) => contour.y[i] ? contour.y[i][0] : 0),
                z: contour.z || [],
                type: 'contour',
                name: contour.name || `Equation ${idx + 1}`,
                contours: {
                    start: -5,
                    end: 5,
                    size: 0.5,
                    coloring: 'lines'
                },
                line: { width: 2 },
                showscale: false
            });
        }
    });
    
    // Add solution points
    if (plotData.solution_points && Array.isArray(plotData.solution_points) && plotData.solution_points.length > 0) {
        traces.push({
            x: plotData.solution_points.map(p => p.x),
            y: plotData.solution_points.map(p => p.y),
            mode: 'markers',
            name: 'Solutions',
            marker: { size: 12, color: 'red', symbol: 'x' },
            type: 'scatter'
        });
    }
    
    const layout = {
        title: 'Nonlinear System of Equations',
        xaxis: { title: 'x' },
        yaxis: { title: 'y', scaleanchor: 'x' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotInequalityAdvanced(plotData, plotDiv) {
    if (!plotData) {
        plotDiv.innerHTML = '<p style="text-align:center; padding:50px;">No plot data available</p>';
        return;
    }
    
    const traces = [];
    
    // Main function curve
    traces.push({
        x: plotData.x || [],
        y: plotData.y || [],
        type: 'scatter',
        mode: 'lines',
        name: 'f(x)',
        line: { color: '#667eea', width: 3 }
    });
    
    // NEW: Create filled area for solution regions
    if (plotData.shaded_regions && Array.isArray(plotData.shaded_regions) && plotData.shaded_regions.length > 0) {
        const shadeX = plotData.shaded_regions.map(p => p.x);
        const shadeY = plotData.shaded_regions.map(p => p.y);
        
        traces.push({
            x: shadeX,
            y: shadeY,
            fill: 'tozeroy',
            type: 'scatter',
            mode: 'none',
            name: 'Solution Region',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            showlegend: true
        });
    }
    
    // Add zero line (x-axis reference)
    traces.push({
        x: plotData.x,
        y: Array(plotData.x.length).fill(0),
        type: 'scatter',
        mode: 'lines',
        name: 'y = 0',
        line: { color: 'black', width: 1, dash: 'dot' },
        showlegend: false
    });
    
    // Highlight critical points with larger markers
    if (plotData.critical_points && Array.isArray(plotData.critical_points) && plotData.critical_points.length > 0) {
        traces.push({
            x: plotData.critical_points,
            y: Array(plotData.critical_points.length).fill(0),
            mode: 'markers',
            name: 'Critical Points',
            marker: { 
                size: 14, 
                color: '#f44336',
                symbol: 'circle',
                line: { color: 'white', width: 2 }
            },
            hovertemplate: 'x = %{x:.2f}<extra></extra>'
        });
    }
    
    const layout = {
        title: {
            text: `Solution: ${plotData.solution || 'See graph'}`,
            font: { size: 16, color: '#667eea', weight: 'bold' }
        },
        xaxis: { 
            title: 'x', 
            zeroline: true,
            gridcolor: '#e0e0e0'
        },
        yaxis: { 
            title: 'f(x)', 
            zeroline: true,
            gridcolor: '#e0e0e0'
        },
        showlegend: true,
        hovermode: 'closest',
        plot_bgcolor: '#f9f9f9'
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotStandardAlgebra(plotData, plotDiv, title) {
    if (!plotData) {
        plotDiv.innerHTML = '<p style="text-align:center; padding:50px;">No plot data available</p>';
        return;
    }
    
    const traces = [];
    
    // Main function curve
    traces.push({
        x: plotData.x || [],
        y: plotData.y || [],
        type: 'scatter',
        mode: 'lines',
        line: { color: '#667eea', width: 3 },
        name: plotData.is_absolute_value ? '|f(x)|' : 'f(x)'
    });
    
    // For absolute value: Add horizontal line with enhanced styling
    if (plotData.horizontal_line !== undefined) {
        const xMin = plotData.x[0];
        const xMax = plotData.x[plotData.x.length - 1];
        
        traces.push({
            x: [xMin, xMax],
            y: [plotData.horizontal_line, plotData.horizontal_line],
            type: 'scatter',
            mode: 'lines',
            line: { color: '#ff6b6b', width: 2, dash: 'dash' },
            name: `y = ${plotData.horizontal_line}`
        });
    }
    
    // Highlight solution points with larger, more visible markers
    if (plotData.solution_points && Array.isArray(plotData.solution_points) && plotData.solution_points.length > 0) {
        traces.push({
            x: plotData.solution_points.map(p => p.x),
            y: plotData.solution_points.map(p => p.y),
            mode: 'markers',
            name: 'Solutions',
            marker: { 
                size: 16, 
                color: '#f44336', 
                symbol: 'x',
                line: { color: 'white', width: 2 }
            },
            hovertemplate: 'Solution: x = %{x:.3f}<extra></extra>'
        });
        
        // NEW: Add vertical lines from solutions to x-axis for clarity
        plotData.solution_points.forEach((pt, idx) => {
            traces.push({
                x: [pt.x, pt.x],
                y: [0, pt.y],
                type: 'scatter',
                mode: 'lines',
                line: { color: '#f44336', width: 1, dash: 'dot' },
                showlegend: false,
                hoverinfo: 'skip'
            });
        });
    }
    
    const layout = {
        title: {
            text: title || 'Graph',
            font: { size: 16 }
        },
        xaxis: { 
            title: 'x', 
            zeroline: true,
            gridcolor: '#e0e0e0'
        },
        yaxis: { 
            title: 'y', 
            zeroline: true,
            gridcolor: '#e0e0e0'
        },
        showlegend: true,
        hovermode: 'closest',
        plot_bgcolor: '#f9f9f9'
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotComplexPlane(plotData, plotDiv) {
    if (!plotData || !plotData.real || !plotData.imag) {
        plotDiv.innerHTML = '<p style="text-align:center; padding:50px;">No complex solutions to plot</p>';
        return;
    }
    
    const trace = {
        x: plotData.real,
        y: plotData.imag,
        mode: 'markers+text',
        type: 'scatter',
        marker: { size: 12, color: '#667eea' },
        text: plotData.labels || [],
        textposition: 'top center'
    };
    
    const layout = {
        title: 'Complex Plane - Solutions',
        xaxis: { title: 'Real Part', zeroline: true },
        yaxis: { title: 'Imaginary Part', zeroline: true },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}