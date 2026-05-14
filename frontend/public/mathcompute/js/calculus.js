function displayCalculusResults(data, infoPanel, plotDiv) {
    // Standard calculus with comprehensive analysis
    if (data.type === 'calculus_standard') {
        displayStandardCalculus(data, infoPanel, plotDiv);
    }
    // Definite integral
    else if (data.type === 'calculus_definite_integral') {
        displayDefiniteIntegral(data, infoPanel, plotDiv);
    }
    // Limit
    else if (data.type === 'calculus_limit') {
        displayLimit(data, infoPanel, plotDiv);
    }
    // Taylor series
    else if (data.type === 'calculus_taylor_series') {
        displayTaylorSeries(data, infoPanel, plotDiv);
    }
    // Partial derivatives
    else if (data.type === 'calculus_partial_derivatives') {
        displayPartialDerivatives(data, infoPanel, plotDiv);
    }
}

function displayStandardCalculus(data, infoPanel, plotDiv) {
    // Build interval analysis table
    let intervalHTML = '';
    if (data.interval_analysis && data.interval_analysis.length > 0) {
        intervalHTML = `
            <div class="info-item">
                <div class="info-label">Interval Analysis:</div>
                <div class="info-value">
                    <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                        <tr style="background: #f0f0f0; font-weight: bold;">
                            <th style="padding: 8px; border: 1px solid #ddd;">Interval</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Increasing?</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Concave Up?</th>
                        </tr>
                        ${data.interval_analysis.map(interval => `
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd;">${interval.interval}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                                    ${interval.increasing ? '✓' : '✗'}
                                </td>
                                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                                    ${interval.concave_up ? '✓' : '✗'}
                                </td>
                            </tr>
                        `).join('')}
                    </table>
                </div>
            </div>
        `;
    }
    
    // Build classified points list
    let classifiedHTML = '';
    if (data.classified_points && data.classified_points.length > 0) {
        classifiedHTML = `
            <div class="info-item">
                <div class="info-label">Extrema:</div>
                <div class="info-value">
                    ${data.classified_points.map(pt => 
                        `<div>x = ${pt.point.toFixed(3)} → ${pt.type}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Original Function:</div>
            <div class="info-value" id="calc-function"></div>
        </div>
        <div class="info-item">
            <div class="info-label">First Derivative:</div>
            <div class="info-value" id="calc-derivative1"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Second Derivative:</div>
            <div class="info-value" id="calc-derivative2"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Indefinite Integral:</div>
            <div class="info-value" id="calc-integral"></div>
        </div>
        ${data.critical_points && data.critical_points.length > 0 ? `
        <div class="info-item">
            <div class="info-label">Critical Points:</div>
            <div class="info-value">${data.critical_points.map(cp => cp.toFixed(3)).join(', ')}</div>
        </div>
        ` : ''}
        ${classifiedHTML}
        ${data.inflection_points && data.inflection_points.length > 0 ? `
        <div class="info-item">
            <div class="info-label">Inflection Points:</div>
            <div class="info-value">${data.inflection_points.map(ip => ip.toFixed(3)).join(', ')}</div>
        </div>
        ` : ''}
        ${intervalHTML}
    `;
    
    // Render LaTeX
    katex.render(data.latex.function, document.getElementById('calc-function'));
    katex.render(data.latex.derivative_1, document.getElementById('calc-derivative1'));
    katex.render(data.latex.derivative_2, document.getElementById('calc-derivative2'));
    katex.render(data.latex.integral, document.getElementById('calc-integral'));
    
    // Plot
    plotAdvancedCalculus(data.plot_data, plotDiv);
}

function displayDefiniteIntegral(data, infoPanel, plotDiv) {
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Function:</div>
            <div class="info-value" id="def-function"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Definite Integral:</div>
            <div class="info-value" id="def-integral"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Bounds:</div>
            <div class="info-value">[${data.lower_bound}, ${data.upper_bound}]</div>
        </div>
        <div class="info-item">
            <div class="info-label">Result:</div>
            <div class="info-value" id="def-result"></div>
        </div>
        ${data.numerical_value !== null ? `
        <div class="info-item">
            <div class="info-label">Numerical Value:</div>
            <div class="info-value" style="font-size: 1.2em; font-weight: bold; color: #667eea;">
                ${data.numerical_value.toFixed(6)}
            </div>
        </div>
        ` : ''}
    `;
    
    katex.render(data.latex.function, document.getElementById('def-function'));
    katex.render(data.latex.integral, document.getElementById('def-integral'));
    katex.render(data.latex.result, document.getElementById('def-result'));
    
    // Plot with shaded area
    plotDefiniteIntegral(data.plot_data, plotDiv);
}

function displayLimit(data, infoPanel, plotDiv) {
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Function:</div>
            <div class="info-value" id="lim-function"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Limit Expression:</div>
            <div class="info-value" id="lim-expression"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Limit Value:</div>
            <div class="info-value" id="lim-result" style="font-size: 1.2em; font-weight: bold; color: #667eea;"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Left Limit:</div>
            <div class="info-value">${data.left_limit}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Right Limit:</div>
            <div class="info-value">${data.right_limit}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Limit Exists?</div>
            <div class="info-value">${data.limit_exists ? '✓ Yes' : '✗ No (discontinuity)'}</div>
        </div>
    `;
    
    katex.render(data.latex.function, document.getElementById('lim-function'));
    katex.render(data.latex.limit, document.getElementById('lim-expression'));
    katex.render(data.latex.result, document.getElementById('lim-result'));
    
    // Plot
    plotLimit(data.plot_data, plotDiv);
}

function displayTaylorSeries(data, infoPanel, plotDiv) {
    // Build terms table
    let termsHTML = '';
    if (data.terms && data.terms.length > 0) {
        termsHTML = `
            <div class="info-item">
                <div class="info-label">Series Terms:</div>
                <div class="info-value">
                    <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                        <tr style="background: #f0f0f0; font-weight: bold;">
                            <th style="padding: 8px; border: 1px solid #ddd;">Order</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Coefficient</th>
                            <th style="padding: 8px; border: 1px solid #ddd;">Term</th>
                        </tr>
                        ${data.terms.map(term => `
                            <tr>
                                <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">${term.order}</td>
                                <td style="padding: 8px; border: 1px solid #ddd;">${term.coefficient}</td>
                                <td style="padding: 8px; border: 1px solid #ddd;">${term.term}</td>
                            </tr>
                        `).join('')}
                    </table>
                </div>
            </div>
        `;
    }
    
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Type:</div>
            <div class="info-value">${data.series_name}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Original Function:</div>
            <div class="info-value" id="taylor-function"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Center:</div>
            <div class="info-value">x = ${data.center}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Order:</div>
            <div class="info-value">${data.order}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Taylor Polynomial:</div>
            <div class="info-value" id="taylor-series"></div>
        </div>
        ${termsHTML}
    `;
    
    katex.render(data.latex.function, document.getElementById('taylor-function'));
    katex.render(data.latex.series, document.getElementById('taylor-series'));
    
    // Plot comparison
    plotTaylorSeries(data.plot_data, plotDiv);
}

function displayPartialDerivatives(data, infoPanel, plotDiv) {
    // Build partials table
    let partialsHTML = '';
    if (data.partial_derivatives && Object.keys(data.partial_derivatives).length > 0) {
        partialsHTML = Object.entries(data.partial_derivatives).map(([var_name, derivs]) => `
            <div style="margin-bottom: 15px;">
                <strong>With respect to ${var_name}:</strong>
                <div style="margin-left: 20px;">
                    <div>First: ${derivs.first}</div>
                    <div>Second: ${derivs.second}</div>
                </div>
            </div>
        `).join('');
    }
    
    // Mixed partials
    let mixedHTML = '';
    if (data.mixed_partials && Object.keys(data.mixed_partials).length > 0) {
        mixedHTML = `
            <div class="info-item">
                <div class="info-label">Mixed Partials:</div>
                <div class="info-value">
                    ${Object.entries(data.mixed_partials).map(([key, val]) => 
                        `<div>${key} = ${val}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    // Critical points
    let criticalHTML = '';
    if (data.critical_points && data.critical_points.length > 0) {
        criticalHTML = `
            <div class="info-item">
                <div class="info-label">Critical Points:</div>
                <div class="info-value">
                    ${data.critical_points.map(pt => 
                        `<div>${pt.point} → ${pt.classification}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Function:</div>
            <div class="info-value" id="partial-function"></div>
        </div>
        <div class="info-item">
            <div class="info-label">Variables:</div>
            <div class="info-value">${data.variables.join(', ')}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Partial Derivatives:</div>
            <div class="info-value">${partialsHTML}</div>
        </div>
        ${mixedHTML}
        ${criticalHTML}
    `;
    
    katex.render(data.latex.function, document.getElementById('partial-function'));
    
    // 3D surface plot
    if (data.plot_data) {
        plot3DSurface(data.plot_data, plotDiv);
    }
}

// Plotting Functions

function plotAdvancedCalculus(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y_original,
            name: 'f(x)',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#667eea', width: 3 }
        },
        {
            x: plotData.x,
            y: plotData.y_derivative,
            name: "f'(x)",
            type: 'scatter',
            mode: 'lines',
            line: { color: '#f44336', width: 2, dash: 'dash' }
        },
        {
            x: plotData.x,
            y: plotData.y_second_derivative,
            name: "f''(x)",
            type: 'scatter',
            mode: 'lines',
            line: { color: '#4caf50', width: 2, dash: 'dot' }
        }
    ];
    
    // Add critical points
    if (plotData.critical_points && plotData.critical_points.length > 0) {
        traces.push({
            x: plotData.critical_points.map(p => p.x),
            y: plotData.critical_points.map(p => p.y),
            name: 'Critical Points',
            mode: 'markers',
            marker: { size: 12, color: 'red', symbol: 'circle' }
        });
    }
    
    // Add inflection points
    if (plotData.inflection_points && plotData.inflection_points.length > 0) {
        traces.push({
            x: plotData.inflection_points.map(p => p.x),
            y: plotData.inflection_points.map(p => p.y),
            name: 'Inflection Points',
            mode: 'markers',
            marker: { size: 12, color: 'orange', symbol: 'diamond' }
        });
    }
    
    const layout = {
        title: 'Function Analysis',
        xaxis: { title: 'x', zeroline: true },
        yaxis: { title: 'y', zeroline: true },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotDefiniteIntegral(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y,
            name: 'f(x)',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#667eea', width: 3 }
        },
        {
            x: plotData.x_fill,
            y: plotData.y_fill,
            name: 'Area',
            type: 'scatter',
            fill: 'tozeroy',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            line: { width: 0 }
        }
    ];
    
    const layout = {
        title: `Definite Integral [${plotData.bounds[0].toFixed(2)}, ${plotData.bounds[1].toFixed(2)}]`,
        xaxis: { title: 'x', zeroline: true },
        yaxis: { title: 'y', zeroline: true },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}
function plotLimit(plotData, plotDiv) {
    const trace = {
        x: plotData.x,
        y: plotData.y,
        name: 'f(x)',
        type: 'scatter',
        mode: 'lines',
        line: { color: '#667eea', width: 3 }
    };
    
    const traces = [trace];
    
    // Add approach point marker if applicable
    if (plotData.approach_point !== null) {
        traces.push({
            x: [plotData.approach_point],
            y: [0],
            mode: 'markers',
            name: 'Approach Point',
            marker: { size: 15, color: 'red', symbol: 'x' }
        });
    }
    
    const layout = {
        title: 'Limit Visualization',
        xaxis: { title: 'x', zeroline: true },
        yaxis: { title: 'y', zeroline: true },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotTaylorSeries(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y_original,
            name: 'Original f(x)',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#667eea', width: 3 }
        },
        {
            x: plotData.x,
            y: plotData.y_taylor,
            name: 'Taylor Approximation',
            type: 'scatter',
            mode: 'lines',
            line: { color: '#f44336', width: 2, dash: 'dash' }
        }
    ];
    
    // Add center point
    traces.push({
        x: [plotData.center],
        y: [plotData.y_original[Math.floor(plotData.x.length / 2)]],
        mode: 'markers',
        name: 'Center',
        marker: { size: 12, color: 'green', symbol: 'star' }
    });
    
    const layout = {
        title: 'Taylor Series Approximation',
        xaxis: { title: 'x', zeroline: true },
        yaxis: { title: 'y', zeroline: true },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plot3DSurface(plotData, plotDiv) {
    const trace = {
        x: plotData.x[0],
        y: plotData.y.map(row => row[0]),
        z: plotData.z,
        type: 'surface',
        colorscale: 'Viridis'
    };
    
    const layout = {
        title: '3D Surface Plot',
        scene: {
            xaxis: { title: 'x' },
            yaxis: { title: 'y' },
            zaxis: { title: 'z' }
        }
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}