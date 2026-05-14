function displayGeometryResults(data, infoPanel, plotDiv) {
    const geomType = data.type;
    
    if (geomType === 'coordinate_geometry') {
        displayCoordinateGeometry(data, infoPanel, plotDiv);
    } else if (geomType === 'circle') {
        displayCircle(data, infoPanel, plotDiv);
    } else if (geomType === 'triangle') {
        displayTriangle(data, infoPanel, plotDiv);
    } else if (geomType === 'mensuration_2d') {
        displayMensuration2D(data, infoPanel, plotDiv);
    } else if (geomType === 'solid_3d') {
        displaySolid3D(data, infoPanel, plotDiv);
    } else if (geomType === 'geometry_equation') {
        displayGeometryEquation(data, infoPanel, plotDiv);
    }
}

// ============================================
// COORDINATE GEOMETRY DISPLAY
// ============================================

function displayCoordinateGeometry(data, infoPanel, plotDiv) {
    const op = data.operation;
    
    let infoHTML = `
        <div class="info-item">
            <div class="info-label">Operation:</div>
            <div class="info-value">${op.replace('_', ' ').toUpperCase()}</div>
        </div>
    `;
    
    if (op === 'distance') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Point 1:</div>
                <div class="info-value">(${data.point1[0]}, ${data.point1[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Point 2:</div>
                <div class="info-value">(${data.point2[0]}, ${data.point2[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Distance:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    ${data.distance}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="coord-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('coord-formula'));
        
        // Plot
        plotCoordinateDistance(data.plot_data, plotDiv);
        
    } else if (op === 'midpoint') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Point 1:</div>
                <div class="info-value">(${data.point1[0]}, ${data.point1[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Point 2:</div>
                <div class="info-value">(${data.point2[0]}, ${data.point2[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Midpoint:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    (${data.midpoint[0]}, ${data.midpoint[1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="coord-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('coord-formula'));
        
        plotCoordinateMidpoint(data.plot_data, plotDiv);
        
    } else if (op === 'slope') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Point 1:</div>
                <div class="info-value">(${data.point1[0]}, ${data.point1[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Point 2:</div>
                <div class="info-value">(${data.point2[0]}, ${data.point2[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Slope:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    ${data.slope}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="coord-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('coord-formula'));
        
        plotCoordinateLine(data.plot_data, plotDiv, 'Slope Calculation');
        
    } else if (op === 'line_equation') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Point 1:</div>
                <div class="info-value">(${data.point1[0]}, ${data.point1[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Point 2:</div>
                <div class="info-value">(${data.point2[0]}, ${data.point2[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Equation:</div>
                <div class="info-value" style="font-size: 1.1em; color: #667eea; font-weight: bold;" id="line-eq"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.equation, document.getElementById('line-eq'));
        
        plotLineEquation(data.plot_data, plotDiv);
        
    } else if (op === 'triangle_area') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Vertices:</div>
                <div class="info-value">
                    A(${data.vertices[0][0]}, ${data.vertices[0][1]})<br>
                    B(${data.vertices[1][0]}, ${data.vertices[1][1]})<br>
                    C(${data.vertices[2][0]}, ${data.vertices[2][1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Area:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    ${data.area}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="coord-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('coord-formula'));
        
        plotTriangleCoords(data.plot_data, plotDiv);
        
    } else if (op === 'collinearity') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Points:</div>
                <div class="info-value">
                    P1(${data.points[0][0]}, ${data.points[0][1]})<br>
                    P2(${data.points[1][0]}, ${data.points[1][1]})<br>
                    P3(${data.points[2][0]}, ${data.points[2][1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Result:</div>
                <div class="info-value" style="font-size: 1.1em; color: ${data.is_collinear ? '#4caf50' : '#f44336'}; font-weight: bold;">
                    ${data.result}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Area (should be 0):</div>
                <div class="info-value">${data.area}</div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        plotCollinear(data.plot_data, plotDiv);
    }
}

function plotCoordinateDistance(plotData, plotDiv) {
    const [p1, p2] = plotData.points;
    
    const traces = [
        {
            x: [p1[0], p2[0]],
            y: [p1[1], p2[1]],
            mode: 'lines+markers',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            marker: { size: 10, color: 'red' },
            name: 'Distance'
        }
    ];
    
    const layout = {
        title: 'Distance Between Points',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'x' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCoordinateMidpoint(plotData, plotDiv) {
    const [p1, p2] = plotData.points;
    const [mx, my] = plotData.midpoint;
    
    const traces = [
        {
            x: [p1[0], p2[0]],
            y: [p1[1], p2[1]],
            mode: 'lines+markers',
            type: 'scatter',
            line: { color: '#667eea', width: 2 },
            marker: { size: 8, color: '#667eea' },
            name: 'Line'
        },
        {
            x: [mx],
            y: [my],
            mode: 'markers',
            type: 'scatter',
            marker: { size: 15, color: 'red', symbol: 'star' },
            name: 'Midpoint'
        }
    ];
    
    const layout = {
        title: 'Midpoint of Line Segment',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'x' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCoordinateLine(plotData, plotDiv, title) {
    const [p1, p2] = plotData.points;
    
    const traces = [
        {
            x: [p1[0], p2[0]],
            y: [p1[1], p2[1]],
            mode: 'lines+markers',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            marker: { size: 10, color: 'red' },
            name: 'Line'
        }
    ];
    
    const layout = {
        title: title,
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'x' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotLineEquation(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y,
            mode: 'lines',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            name: 'Line'
        },
        {
            x: plotData.points.map(p => p[0]),
            y: plotData.points.map(p => p[1]),
            mode: 'markers',
            type: 'scatter',
            marker: { size: 10, color: 'red' },
            name: 'Points'
        }
    ];
    
    const layout = {
        title: 'Line Equation',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotTriangleCoords(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.polygon[0],
            y: plotData.polygon[1],
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            line: { color: '#667eea', width: 3 },
            name: 'Triangle'
        },
        {
            x: plotData.vertices.map(v => v[0]),
            y: plotData.vertices.map(v => v[1]),
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 10, color: 'red' },
            text: ['A', 'B', 'C'],
            textposition: 'top center',
            name: 'Vertices'
        }
    ];
    
    const layout = {
        title: 'Triangle Area',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'x' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCollinear(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.points.map(p => p[0]),
            y: plotData.points.map(p => p[1]),
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 12, color: 'red' },
            text: ['P1', 'P2', 'P3'],
            textposition: 'top center',
            name: 'Points'
        }
    ];
    
    if (plotData.line) {
        traces.unshift({
            x: plotData.line[0],
            y: plotData.line[1],
            mode: 'lines',
            type: 'scatter',
            line: { color: '#667eea', width: 2, dash: 'dash' },
            name: 'Line'
        });
    }
    
    const layout = {
        title: 'Collinearity Check',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'x' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}



function displayCircle(data, infoPanel, plotDiv) {
    const op = data.operation;
    
    let infoHTML = `
        <div class="info-item">
            <div class="info-label">Shape:</div>
            <div class="info-value">CIRCLE</div>
        </div>
        <div class="info-item">
            <div class="info-label">Center:</div>
            <div class="info-value">(${data.center[0]}, ${data.center[1]})</div>
        </div>
        <div class="info-item">
            <div class="info-label">Radius:</div>
            <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                ${data.radius}
            </div>
        </div>
    `;
    
    if (op === 'circle_construction') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Area:</div>
                <div class="info-value" id="circle-area"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Circumference:</div>
                <div class="info-value" id="circle-circ"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Equation:</div>
                <div class="info-value" id="circle-eq"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.area, document.getElementById('circle-area'));
        katex.render(data.latex.circumference, document.getElementById('circle-circ'));
        katex.render(data.latex.equation, document.getElementById('circle-eq'));
        
        plotCircle(data.plot_data, plotDiv, 'Circle');
        
    } else if (op === 'tangent_length') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">External Point:</div>
                <div class="info-value">(${data.external_point[0]}, ${data.external_point[1]})</div>
            </div>
            <div class="info-item">
                <div class="info-label">Tangent Length:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    ${data.tangent_length}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="tangent-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('tangent-formula'));
        
        plotCircleTangent(data.plot_data, plotDiv);
    }
}

function plotCircle(plotData, plotDiv, title) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y,
            mode: 'lines',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.2)',
            name: 'Circle'
        },
        {
            x: [plotData.center[0]],
            y: [plotData.center[1]],
            mode: 'markers',
            type: 'scatter',
            marker: { size: 10, color: 'red', symbol: 'x' },
            name: 'Center'
        }
    ];
    
    const layout = {
        title: title,
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCircleTangent(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.circle.x,
            y: plotData.circle.y,
            mode: 'lines',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            name: 'Circle'
        },
        {
            x: [plotData.center[0]],
            y: [plotData.center[1]],
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 10, color: 'red' },
            text: ['Center'],
            textposition: 'top center',
            name: 'Center'
        },
        {
            x: [plotData.point[0]],
            y: [plotData.point[1]],
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 10, color: 'green' },
            text: ['External Point'],
            textposition: 'top center',
            name: 'Point'
        }
    ];
    
    const layout = {
        title: 'Tangent from External Point',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

// ============================================
// TRIANGLE DISPLAY
// ============================================

function displayTriangle(data, infoPanel, plotDiv) {
    const op = data.operation;
    
    let infoHTML = `
        <div class="info-item">
            <div class="info-label">Operation:</div>
            <div class="info-value">${op.replace('_', ' ').toUpperCase()}</div>
        </div>
    `;
    
    if (op === 'pythagoras') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Sides:</div>
                <div class="info-value">
                    a = ${data.sides.a}<br>
                    b = ${data.sides.b}<br>
                    c = ${data.sides.c} (hypotenuse)
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Unknown Side:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    ${data.unknown} = ${data.sides[data.unknown]}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Theorem:</div>
                <div class="info-value" id="pyth-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('pyth-formula'));
        
        plotRightTriangle(data.plot_data, plotDiv);
        
    } else if (op === 'triangle_analysis') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Type:</div>
                <div class="info-value" style="font-size: 1.1em; color: #667eea; font-weight: bold;">
                    ${data.triangle_type}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Sides:</div>
                <div class="info-value">
                    a = ${data.sides.a}<br>
                    b = ${data.sides.b}<br>
                    c = ${data.sides.c}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Area:</div>
                <div class="info-value" id="tri-area"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Perimeter:</div>
                <div class="info-value" id="tri-perim"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.area, document.getElementById('tri-area'));
        katex.render(data.latex.perimeter, document.getElementById('tri-perim'));
        
        plotTriangleCoords(data.plot_data, plotDiv);
        
    } else if (op === 'centroid') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Vertices:</div>
                <div class="info-value">
                    A(${data.vertices[0][0]}, ${data.vertices[0][1]})<br>
                    B(${data.vertices[1][0]}, ${data.vertices[1][1]})<br>
                    C(${data.vertices[2][0]}, ${data.vertices[2][1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Centroid:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    G(${data.centroid[0]}, ${data.centroid[1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Formula:</div>
                <div class="info-value" id="centroid-formula"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.formula, document.getElementById('centroid-formula'));
        
        plotTriangleCentroid(data.plot_data, plotDiv);
        
    } else if (op === 'circumcenter') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Vertices:</div>
                <div class="info-value">
                    A(${data.vertices[0][0]}, ${data.vertices[0][1]})<br>
                    B(${data.vertices[1][0]}, ${data.vertices[1][1]})<br>
                    C(${data.vertices[2][0]}, ${data.vertices[2][1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Circumcenter:</div>
                <div class="info-value" style="font-size: 1.2em; color: #667eea; font-weight: bold;">
                    O(${data.circumcenter[0]}, ${data.circumcenter[1]})
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Circumradius:</div>
                <div class="info-value">${data.circumradius}</div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        plotCircumcircle(data.plot_data, plotDiv);
    }
}

function plotRightTriangle(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.polygon[0],
            y: plotData.polygon[1],
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.3)',
            line: { color: '#667eea', width: 3 },
            name: 'Triangle'
        }
    ];
    
    const layout = {
        title: 'Right Triangle - Pythagoras Theorem',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotTriangleCentroid(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.polygon[0],
            y: plotData.polygon[1],
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.2)',
            line: { color: '#667eea', width: 3 },
            name: 'Triangle'
        },
        {
            x: [plotData.centroid[0]],
            y: [plotData.centroid[1]],
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 15, color: 'red', symbol: 'star' },
            text: ['Centroid'],
            textposition: 'top center',
            name: 'Centroid'
        }
    ];
    
    const layout = {
        title: 'Triangle Centroid',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCircumcircle(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.circle.x,
            y: plotData.circle.y,
            mode: 'lines',
            type: 'scatter',
            line: { color: '#f44336', width: 2, dash: 'dash' },
            name: 'Circumcircle'
        },
        {
            x: plotData.polygon[0],
            y: plotData.polygon[1],
            mode: 'lines',
            type: 'scatter',
            line: { color: '#667eea', width: 3 },
            name: 'Triangle'
        },
        {
            x: [plotData.circumcenter[0]],
            y: [plotData.circumcenter[1]],
            mode: 'markers+text',
            type: 'scatter',
            marker: { size: 12, color: 'green', symbol: 'x' },
            text: ['Circumcenter'],
            textposition: 'top center',
            name: 'Circumcenter'
        }
    ];
    
    const layout = {
        title: 'Triangle Circumcircle',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: true
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

// ============================================
// MENSURATION 2D DISPLAY
// ============================================

function displayMensuration2D(data, infoPanel, plotDiv) {
    const shape = data.shape;
    
    let infoHTML = `
        <div class="info-item">
            <div class="info-label">Shape:</div>
            <div class="info-value">${shape.toUpperCase()}</div>
        </div>
    `;
    
    if (shape === 'rectangle') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Dimensions:</div>
                <div class="info-value">
                    Length = ${data.length}<br>
                    Width = ${data.width}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Area:</div>
                <div class="info-value" id="area-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Perimeter:</div>
                <div class="info-value" id="perimeter-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.area, document.getElementById('area-latex'));
        katex.render(data.latex.perimeter, document.getElementById('perimeter-latex'));
        
        plotRectangle(data.plot_data, plotDiv);
        
    } else if (shape === 'square') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Side:</div>
                <div class="info-value">${data.side}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Area:</div>
                <div class="info-value" id="area-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Perimeter:</div>
                <div class="info-value" id="perimeter-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.area, document.getElementById('area-latex'));
        katex.render(data.latex.perimeter, document.getElementById('perimeter-latex'));
        
        plotSquare(data.plot_data, plotDiv);
        
    } else if (shape === 'circle') {
        if (data.area !== undefined) {
            infoHTML += `
                <div class="info-item">
                    <div class="info-label">Radius:</div>
                    <div class="info-value">${data.radius}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Area:</div>
                    <div class="info-value" id="area-latex"></div>
                </div>
            `;
            
            infoPanel.innerHTML = infoHTML;
            katex.render(data.latex.area, document.getElementById('area-latex'));
        } else if (data.circumference !== undefined) {
            infoHTML += `
                <div class="info-item">
                    <div class="info-label">Radius:</div>
                    <div class="info-value">${data.radius}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Circumference:</div>
                    <div class="info-value" id="circ-latex"></div>
                </div>
            `;
            
            infoPanel.innerHTML = infoHTML;
            katex.render(data.latex.circumference, document.getElementById('circ-latex'));
        }
        
        plotCircle2D(data.plot_data, plotDiv);
    }
}

function plotRectangle(plotData, plotDiv) {
    const vertices = plotData.vertices;
    const x = vertices.map(v => v[0]);
    const y = vertices.map(v => v[1]);
    x.push(vertices[0][0]);
    y.push(vertices[0][1]);
    
    const traces = [
        {
            x: x,
            y: y,
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.4)',
            line: { color: '#667eea', width: 3 },
            name: 'Rectangle'
        }
    ];
    
    const layout = {
        title: 'Rectangle',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotSquare(plotData, plotDiv) {
    const vertices = plotData.vertices;
    const x = vertices.map(v => v[0]);
    const y = vertices.map(v => v[1]);
    x.push(vertices[0][0]);
    y.push(vertices[0][1]);
    
    const traces = [
        {
            x: x,
            y: y,
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.4)',
            line: { color: '#667eea', width: 3 },
            name: 'Square'
        }
    ];
    
    const layout = {
        title: 'Square',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plotCircle2D(plotData, plotDiv) {
    const traces = [
        {
            x: plotData.x,
            y: plotData.y,
            mode: 'lines',
            type: 'scatter',
            fill: 'toself',
            fillcolor: 'rgba(102, 126, 234, 0.4)',
            line: { color: '#667eea', width: 3 },
            name: 'Circle'
        }
    ];
    
    const layout = {
        title: 'Circle',
        xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0', scaleanchor: 'y' },
        yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
        showlegend: false
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

// ============================================
// 3D SOLIDS DISPLAY
// ============================================

function displaySolid3D(data, infoPanel, plotDiv) {
    const shape = data.shape;
    
    let infoHTML = `
        <div class="info-item">
            <div class="info-label">3D Shape:</div>
            <div class="info-value">${shape.toUpperCase()}</div>
        </div>
    `;
    
    if (shape === 'cube') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Side:</div>
                <div class="info-value">${data.side}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Surface Area:</div>
                <div class="info-value" id="sa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.surface_area, document.getElementById('sa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DCube(data.plot_data, plotDiv);
        
    } else if (shape === 'cuboid') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Dimensions:</div>
                <div class="info-value">
                    L = ${data.dimensions.length}<br>
                    W = ${data.dimensions.width}<br>
                    H = ${data.dimensions.height}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Surface Area:</div>
                <div class="info-value" id="sa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.surface_area, document.getElementById('sa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DCuboid(data.plot_data, plotDiv);
        
    } else if (shape === 'cylinder') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Dimensions:</div>
                <div class="info-value">
                    Radius = ${data.radius}<br>
                    Height = ${data.height}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Curved Surface Area:</div>
                <div class="info-value" id="csa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Surface Area:</div>
                <div class="info-value" id="tsa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.curved_surface, document.getElementById('csa-latex'));
        katex.render(data.latex.total_surface, document.getElementById('tsa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DCylinder(data.plot_data, plotDiv);
        
    } else if (shape === 'cone') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Dimensions:</div>
                <div class="info-value">
                    Radius = ${data.radius}<br>
                    Height = ${data.height}<br>
                    Slant Height = ${data.slant_height}
                </div>
            </div>
            <div class="info-item">
                <div class="info-label">Curved Surface Area:</div>
                <div class="info-value" id="csa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Surface Area:</div>
                <div class="info-value" id="tsa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.curved_surface, document.getElementById('csa-latex'));
        katex.render(data.latex.total_surface, document.getElementById('tsa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DCone(data.plot_data, plotDiv);
        
    } else if (shape === 'sphere') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Radius:</div>
                <div class="info-value">${data.radius}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Surface Area:</div>
                <div class="info-value" id="sa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.surface_area, document.getElementById('sa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DSphere(data.plot_data, plotDiv);
        
    } else if (shape === 'hemisphere') {
        infoHTML += `
            <div class="info-item">
                <div class="info-label">Radius:</div>
                <div class="info-value">${data.radius}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Curved Surface Area:</div>
                <div class="info-value" id="csa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Total Surface Area:</div>
                <div class="info-value" id="tsa-latex"></div>
            </div>
            <div class="info-item">
                <div class="info-label">Volume:</div>
                <div class="info-value" id="vol-latex"></div>
            </div>
        `;
        
        infoPanel.innerHTML = infoHTML;
        katex.render(data.latex.curved_surface, document.getElementById('csa-latex'));
        katex.render(data.latex.total_surface, document.getElementById('tsa-latex'));
        katex.render(data.latex.volume, document.getElementById('vol-latex'));
        
        plot3DHemisphere(data.plot_data, plotDiv);
    }
}

function plot3DCube(plotData, plotDiv) {
    const vertices = plotData.vertices;
    
    // Define edges
    const edges = [
        [0,1], [1,2], [2,3], [3,0],  // bottom
        [4,5], [5,6], [6,7], [7,4],  // top
        [0,4], [1,5], [2,6], [3,7]   // vertical
    ];
    
    const traces = edges.map(edge => ({
        x: [vertices[edge[0]][0], vertices[edge[1]][0]],
        y: [vertices[edge[0]][1], vertices[edge[1]][1]],
        z: [vertices[edge[0]][2], vertices[edge[1]][2]],
        mode: 'lines',
        type: 'scatter3d',
        line: { color: '#667eea', width: 5 },
        showlegend: false
    }));
    
    const layout = {
        title: 'Cube - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'cube'
        }
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plot3DCuboid(plotData, plotDiv) {
    const vertices = plotData.vertices;
    
    const edges = [
        [0,1], [1,2], [2,3], [3,0],
        [4,5], [5,6], [6,7], [7,4],
        [0,4], [1,5], [2,6], [3,7]
    ];
    
    const traces = edges.map(edge => ({
        x: [vertices[edge[0]][0], vertices[edge[1]][0]],
        y: [vertices[edge[0]][1], vertices[edge[1]][1]],
        z: [vertices[edge[0]][2], vertices[edge[1]][2]],
        mode: 'lines',
        type: 'scatter3d',
        line: { color: '#667eea', width: 5 },
        showlegend: false
    }));
    
    const layout = {
        title: 'Cuboid - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' }
        }
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

function plot3DCylinder(plotData, plotDiv) {
    const trace = {
        x: plotData.x,
        y: plotData.y,
        z: plotData.z,
        type: 'surface',
        colorscale: 'Viridis',
        showscale: false
    };
    
    const layout = {
        title: 'Cylinder - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'data'
        }
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}

function plot3DCone(plotData, plotDiv) {
    const trace = {
        x: plotData.x,
        y: plotData.y,
        z: plotData.z,
        type: 'surface',
        colorscale: 'Plasma',
        showscale: false
    };
    
    const layout = {
        title: 'Cone - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'data'
        }
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}

function plot3DSphere(plotData, plotDiv) {
    const trace = {
        x: plotData.x,
        y: plotData.y,
        z: plotData.z,
        type: 'surface',
        colorscale: 'Blues',
        showscale: false
    };
    
    const layout = {
        title: 'Sphere - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'cube'
        }
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}

function plot3DHemisphere(plotData, plotDiv) {
    const trace = {
        x: plotData.x,
        y: plotData.y,
        z: plotData.z,
        type: 'surface',
        colorscale: 'RdYlBu',
        showscale: false
    };
    
    const layout = {
        title: 'Hemisphere - 3D Visualization',
        scene: {
            xaxis: { title: 'X' },
            yaxis: { title: 'Y' },
            zaxis: { title: 'Z' },
            aspectmode: 'cube'
        }
    };
    
    Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
}
// ============================================
// GEOMETRY EQUATION DISPLAY
// ============================================

function displayGeometryEquation(data, infoPanel, plotDiv) {
    let propsHTML = '';
    if (data.properties && Object.keys(data.properties).length > 0) {
        propsHTML = Object.entries(data.properties).map(([key, value]) => {
            let displayValue = value;
            if (Array.isArray(value)) {
                displayValue = `(${value.join(', ')})`;
            } else if (typeof value === 'number') {
                displayValue = value.toFixed(2);
            }
            return `<div><strong>${key.replace('_', ' ')}:</strong> ${displayValue}</div>`;
        }).join('');
    }
    
    infoPanel.innerHTML = `
        <div class="info-item">
            <div class="info-label">Shape Type:</div>
            <div class="info-value">${data.shape_type.toUpperCase()}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Equation:</div>
            <div class="info-value" id="geom-eq"></div>
        </div>
        ${propsHTML ? `<div class="info-item"><div class="info-label">Properties:</div><div class="info-value">${propsHTML}</div></div>` : ''}
    `;
    
    katex.render(data.latex.equation, document.getElementById('geom-eq'));
    
    // Plot based on type
    if (data.plot_data.type === 'circle') {
        plotCircle(data.plot_data, plotDiv, data.shape_type.toUpperCase());
    } else if (data.plot_data.type === 'line') {
        const traces = [{
            x: data.plot_data.x,
            y: data.plot_data.y,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#667eea', width: 3 }
        }];
        
        const layout = {
            title: 'Line',
            xaxis: { title: 'x', zeroline: true, gridcolor: '#e0e0e0' },
            yaxis: { title: 'y', zeroline: true, gridcolor: '#e0e0e0' },
            showlegend: false
        };
        
        Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
    } else if (data.plot_data.type === 'contour') {
        const trace = {
            x: data.plot_data.x[0],
            y: data.plot_data.y.map(row => row[0]),
            z: data.plot_data.z,
            type: 'contour',
            colorscale: 'Viridis',
            contours: {
                start: -5,
                end: 5,
                size: 0.5,
                coloring: 'lines'
            }
        };
        
        const layout = {
            title: data.shape_type.toUpperCase(),
            xaxis: { title: 'x' },
            yaxis: { title: 'y', scaleanchor: 'x' },
            showlegend: false
        };
        
        Plotly.newPlot(plotDiv, [trace], layout, { responsive: true });
    }
}


