// ============================================================================
// STATISTICS MODULE - FRONTEND VISUALIZATION
// ============================================================================

function displayStatisticsResults(data, infoPanel, plotDiv) {
    const type = data.type;
    
    if (type === 'descriptive_statistics') {
        displayDescriptiveStats(data, infoPanel, plotDiv);
    } else if (type === 'normal_distribution') {
        displayNormalDistribution(data, infoPanel, plotDiv);
    } else if (type === 'binomial_distribution') {
        displayBinomialDistribution(data, infoPanel, plotDiv);
    } else if (type === 'poisson_distribution') {
        displayPoissonDistribution(data, infoPanel, plotDiv);
    } else if (type === 'one_sample_t_test' || type === 'two_sample_t_test' || type === 'z_test') {
        displayHypothesisTest(data, infoPanel, plotDiv);
    } else if (type === 'linear_regression' || type === 'polynomial_regression') {
        displayRegressionAnalysis(data, infoPanel, plotDiv);
    } else if (type === 'correlation_analysis') {
        displayCorrelationAnalysis(data, infoPanel, plotDiv);
    }
}

// ============================================================================
// DESCRIPTIVE STATISTICS
// ============================================================================

function displayDescriptiveStats(data, infoPanel, plotDiv) {
    const stats = data.statistics;
    
    infoPanel.innerHTML = `
        <div class="stats-summary-section">
            <h3 style="color: #1e3c72; margin-bottom: 20px; font-size: 1.2em;">📊 Summary Statistics</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Mean (μ)</div>
                    <div class="stat-value">${stats.mean.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Median</div>
                    <div class="stat-value">${stats.median.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Mode</div>
                    <div class="stat-value">${stats.mode ? stats.mode.toFixed(4) : 'N/A'}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Std Dev (σ)</div>
                    <div class="stat-value">${stats.std_dev.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Variance (σ²)</div>
                    <div class="stat-value">${stats.variance.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Range</div>
                    <div class="stat-value">${stats.range.toFixed(4)}</div>
                </div>
            </div>
        </div>
        
        <div class="stats-summary-section" style="margin-top: 30px;">
            <h3 style="color: #1e3c72; margin-bottom: 20px; font-size: 1.2em;">📈 Five Number Summary</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Minimum</div>
                    <div class="stat-value">${stats.min.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Q1</div>
                    <div class="stat-value">${stats.q1.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Q2 (Median)</div>
                    <div class="stat-value">${stats.q2.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Q3</div>
                    <div class="stat-value">${stats.q3.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Maximum</div>
                    <div class="stat-value">${stats.max.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">IQR</div>
                    <div class="stat-value">${stats.iqr.toFixed(4)}</div>
                </div>
            </div>
        </div>
        
        <div class="stat-info" style="margin-top: 25px;">
            <strong>Sample Size:</strong> n = ${data.n}<br>
            <strong>Skewness:</strong> ${stats.skewness.toFixed(4)} 
            ${stats.skewness > 0 ? '(Right-skewed)' : stats.skewness < 0 ? '(Left-skewed)' : '(Symmetric)'}<br>
            <strong>Kurtosis:</strong> ${stats.kurtosis.toFixed(4)}
        </div>
    `;
    
    // Create subplot with histogram and boxplot
    plotDescriptiveStats(data, plotDiv);
}

function plotDescriptiveStats(data, plotDiv) {
    const histData = data.plot_data.histogram;
    const boxData = data.plot_data.boxplot;
    
    // Histogram trace
    const histTrace = {
        x: histData.bin_centers,
        y: histData.counts,
        type: 'bar',
        name: 'Frequency',
        marker: { color: '#667eea' },
        xaxis: 'x',
        yaxis: 'y'
    };
    
    // Box plot trace
    const boxTrace = {
        y: data.plot_data.raw_data,
        type: 'box',
        name: 'Box Plot',
        marker: { color: '#f44336' },
        boxmean: 'sd',
        xaxis: 'x2',
        yaxis: 'y2'
    };
    
    const layout = {
        title: 'Descriptive Statistics Visualization',
        grid: { rows: 1, columns: 2, pattern: 'independent' },
        xaxis: { title: 'Value', domain: [0, 0.48] },
        yaxis: { title: 'Frequency' },
        xaxis2: { title: 'Dataset', domain: [0.52, 1] },
        yaxis2: { title: 'Value', anchor: 'x2' },
        showlegend: false,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, [histTrace, boxTrace], layout, { responsive: true });
}

// ============================================================================
// NORMAL DISTRIBUTION
// ============================================================================

function displayNormalDistribution(data, infoPanel, plotDiv) {
    const params = data.parameters;
    const probs = data.probabilities;
    
    let probHTML = '';
    if (Object.keys(probs).length > 0) {
        probHTML = `
            <div style="margin-top: 20px;">
                <h3>Probabilities at x = ${probs.z_score ? ((params.mean + probs.z_score * params.std_dev).toFixed(4)) : 'N/A'}</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">P(X < x)</div>
                        <div class="stat-value">${probs.p_less_than.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">P(X > x)</div>
                        <div class="stat-value">${probs.p_greater_than.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Z-Score</div>
                        <div class="stat-value">${probs.z_score.toFixed(4)}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    infoPanel.innerHTML = `
        <h2>Normal Distribution: N(μ=${params.mean}, σ²=${params.variance.toFixed(4)})</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Mean (μ)</div>
                <div class="stat-value">${params.mean.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Std Dev (σ)</div>
                <div class="stat-value">${params.std_dev.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Variance (σ²)</div>
                <div class="stat-value">${params.variance.toFixed(4)}</div>
            </div>
        </div>
        
        ${probHTML}
        
        <div style="margin-top: 20px;">
            <h3>Confidence Intervals</h3>
            <div class="stat-info">
                <strong>95% CI:</strong> [${data.confidence_intervals['95%'].lower.toFixed(4)}, ${data.confidence_intervals['95%'].upper.toFixed(4)}]<br>
                <strong>99% CI:</strong> [${data.confidence_intervals['99%'].lower.toFixed(4)}, ${data.confidence_intervals['99%'].upper.toFixed(4)}]
            </div>
        </div>
    `;
    
    plotNormalDistribution(data, plotDiv);
}

function plotNormalDistribution(data, plotDiv) {
    const plotData = data.plot_data;
    
    // PDF trace
    const pdfTrace = {
        x: plotData.x,
        y: plotData.pdf,
        type: 'scatter',
        mode: 'lines',
        name: 'PDF',
        line: { color: '#667eea', width: 3 },
        fill: 'tozeroy',
        fillcolor: 'rgba(102, 126, 234, 0.2)'
    };
    
    // Mean line
    const meanTrace = {
        x: [plotData.mean_line, plotData.mean_line],
        y: [0, Math.max(...plotData.pdf)],
        type: 'scatter',
        mode: 'lines',
        name: 'Mean',
        line: { color: 'red', width: 2, dash: 'dash' }
    };
    
    const traces = [pdfTrace, meanTrace];
    
    const layout = {
        title: 'Normal Distribution - Probability Density Function',
        xaxis: { title: 'x' },
        yaxis: { title: 'Probability Density' },
        showlegend: true,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

// ============================================================================
// BINOMIAL DISTRIBUTION
// ============================================================================

function displayBinomialDistribution(data, infoPanel, plotDiv) {
    const params = data.parameters;
    const stats = data.statistics;
    
    infoPanel.innerHTML = `
        <h2>Binomial Distribution: B(n=${params.n}, p=${params.p})</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Trials (n)</div>
                <div class="stat-value">${params.n}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Success Prob (p)</div>
                <div class="stat-value">${params.p.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Failure Prob (q)</div>
                <div class="stat-value">${params.q.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Mean (μ)</div>
                <div class="stat-value">${stats.mean.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Std Dev (σ)</div>
                <div class="stat-value">${stats.std_dev.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Variance (σ²)</div>
                <div class="stat-value">${stats.variance.toFixed(4)}</div>
            </div>
        </div>
    `;
    
    plotBinomialDistribution(data, plotDiv);
}

function plotBinomialDistribution(data, plotDiv) {
    const plotData = data.plot_data;
    
    const pmfTrace = {
        x: plotData.x,
        y: plotData.pmf,
        type: 'bar',
        name: 'PMF',
        marker: { color: '#667eea' }
    };
    
    const layout = {
        title: 'Binomial Distribution - Probability Mass Function',
        xaxis: { title: 'Number of Successes (k)' },
        yaxis: { title: 'Probability P(X = k)' },
        showlegend: false,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, [pmfTrace], layout, { responsive: true });
}

// ============================================================================
// POISSON DISTRIBUTION
// ============================================================================

function displayPoissonDistribution(data, infoPanel, plotDiv) {
    const params = data.parameters;
    const stats = data.statistics;
    
    infoPanel.innerHTML = `
        <h2>Poisson Distribution: P(λ=${params.lambda})</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Lambda (λ)</div>
                <div class="stat-value">${params.lambda.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Mean (μ)</div>
                <div class="stat-value">${stats.mean.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Std Dev (σ)</div>
                <div class="stat-value">${stats.std_dev.toFixed(4)}</div>
            </div>
        </div>
    `;
    
    plotPoissonDistribution(data, plotDiv);
}

function plotPoissonDistribution(data, plotDiv) {
    const plotData = data.plot_data;
    
    const pmfTrace = {
        x: plotData.x,
        y: plotData.pmf,
        type: 'bar',
        name: 'PMF',
        marker: { color: '#4caf50' }
    };
    
    const layout = {
        title: 'Poisson Distribution - Probability Mass Function',
        xaxis: { title: 'Number of Events (k)' },
        yaxis: { title: 'Probability P(X = k)' },
        showlegend: false,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, [pmfTrace], layout, { responsive: true });
}

// ============================================================================
// HYPOTHESIS TESTING
// ============================================================================

function displayHypothesisTest(data, infoPanel, plotDiv) {
    const decision = data.decision;
    const decisionColor = decision.reject_null ? '#f44336' : '#4caf50';
    
    let sampleStatsHTML = '';
    if (data.sample_statistics) {
        const ss = data.sample_statistics;
        if (data.type === 'one_sample_t_test') {
            sampleStatsHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Sample Mean</div>
                        <div class="stat-value">${ss.mean.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Sample Std Dev</div>
                        <div class="stat-value">${ss.std_dev.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Sample Size</div>
                        <div class="stat-value">${ss.n}</div>
                    </div>
                </div>
            `;
        } else if (data.type === 'two_sample_t_test') {
            sampleStatsHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Mean 1</div>
                        <div class="stat-value">${ss.mean1.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Mean 2</div>
                        <div class="stat-value">${ss.mean2.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Std Dev 1</div>
                        <div class="stat-value">${ss.std1.toFixed(4)}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Std Dev 2</div>
                        <div class="stat-value">${ss.std2.toFixed(4)}</div>
                    </div>
                </div>
            `;
        }
    }
    
    infoPanel.innerHTML = `
        <h2>${data.type.replace(/_/g, ' ').toUpperCase()}</h2>
        
        ${data.null_hypothesis ? `<div class="stat-info"><strong>H₀:</strong> ${data.null_hypothesis}</div>` : ''}
        
        <div class="stats-grid" style="margin-top: 20px;">
            <div class="stat-card">
                <div class="stat-label">Test Statistic</div>
                <div class="stat-value">${data.test_statistic.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">P-Value</div>
                <div class="stat-value">${data.p_value.toFixed(6)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Significance Level</div>
                <div class="stat-value">α = ${decision.alpha}</div>
            </div>
        </div>
        
        <div style="margin-top: 20px; padding: 15px; background: ${decisionColor}22; border-left: 4px solid ${decisionColor}; border-radius: 4px;">
            <strong style="color: ${decisionColor};">Decision:</strong> ${decision.conclusion}
        </div>
        
        ${sampleStatsHTML ? `<div style="margin-top: 20px;"><h3>Sample Statistics</h3>${sampleStatsHTML}</div>` : ''}
    `;
    
    if (data.plot_data) {
        plotHypothesisTest(data, plotDiv);
    }
}

function plotHypothesisTest(data, plotDiv) {
    const plotData = data.plot_data;
    
    // Distribution curve
    const distTrace = {
        x: plotData.x,
        y: plotData.pdf,
        type: 'scatter',
        mode: 'lines',
        name: 'Distribution',
        line: { color: '#667eea', width: 3 },
        fill: 'tozeroy',
        fillcolor: 'rgba(102, 126, 234, 0.1)'
    };
    
    // Test statistic line
    const testStatTrace = {
        x: [plotData.t_statistic || plotData.z_statistic, plotData.t_statistic || plotData.z_statistic],
        y: [0, Math.max(...plotData.pdf)],
        type: 'scatter',
        mode: 'lines',
        name: 'Test Statistic',
        line: { color: 'red', width: 2, dash: 'dash' }
    };
    
    // Critical value lines
    const criticalTraces = plotData.critical_values.map((cv, i) => ({
        x: [cv, cv],
        y: [0, Math.max(...plotData.pdf)],
        type: 'scatter',
        mode: 'lines',
        name: `Critical Value ${i + 1}`,
        line: { color: 'orange', width: 2, dash: 'dot' }
    }));
    
    const traces = [distTrace, testStatTrace, ...criticalTraces];
    
    const layout = {
        title: 'Hypothesis Test Visualization',
        xaxis: { title: data.type.includes('z') ? 'Z-Score' : 'T-Score' },
        yaxis: { title: 'Probability Density' },
        showlegend: true,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, traces, layout, { responsive: true });
}

// ============================================================================
// REGRESSION ANALYSIS
// ============================================================================

function displayRegressionAnalysis(data, infoPanel, plotDiv) {
    const stats = data.statistics;
    
    infoPanel.innerHTML = `
        <h2>${data.type === 'linear_regression' ? 'Linear' : `Polynomial (degree ${data.degree})`} Regression</h2>
        
        <div class="stat-info" style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong>Equation:</strong> ${data.equation}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">R² (Coefficient of Determination)</div>
                <div class="stat-value">${stats.r_squared.toFixed(4)}</div>
            </div>
            ${stats.r ? `
            <div class="stat-card">
                <div class="stat-label">R (Correlation)</div>
                <div class="stat-value">${stats.r.toFixed(4)}</div>
            </div>
            ` : ''}
            <div class="stat-card">
                <div class="stat-label">RMSE</div>
                <div class="stat-value">${stats.rmse.toFixed(4)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">MSE</div>
                <div class="stat-value">${stats.mse.toFixed(4)}</div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <div class="stat-info">
                <strong>Interpretation:</strong> ${(stats.r_squared * 100).toFixed(2)}% of variance in Y is explained by X
            </div>
        </div>
    `;
    
    plotRegressionAnalysis(data, plotDiv);
}

function plotRegressionAnalysis(data, plotDiv) {
    const plotData = data.plot_data;
    
    // Scatter plot of original data
    const scatterTrace = {
        x: plotData.x_original,
        y: plotData.y_original,
        type: 'scatter',
        mode: 'markers',
        name: 'Data Points',
        marker: { size: 8, color: '#667eea' }
    };
    
    // Regression line/curve
    const lineTrace = {
        x: plotData.x_line,
        y: plotData.y_line,
        type: 'scatter',
        mode: 'lines',
        name: 'Regression Line',
        line: { color: '#f44336', width: 3 }
    };
    
    const layout = {
        title: 'Regression Analysis',
        xaxis: { title: 'X' },
        yaxis: { title: 'Y' },
        showlegend: true,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, [scatterTrace, lineTrace], layout, { responsive: true });
}

// ============================================================================
// CORRELATION ANALYSIS
// ============================================================================

function displayCorrelationAnalysis(data, infoPanel, plotDiv) {
    const pearson = data.pearson;
    const spearman = data.spearman;
    
    infoPanel.innerHTML = `
        <h2>Correlation Analysis</h2>
        
        <div style="margin-bottom: 20px;">
            <h3>Pearson Correlation</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Correlation (r)</div>
                    <div class="stat-value">${pearson.r.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">P-Value</div>
                    <div class="stat-value">${pearson.p_value.toFixed(6)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Strength</div>
                    <div class="stat-value">${pearson.interpretation}</div>
                </div>
            </div>
        </div>
        
        <div>
            <h3>Spearman Correlation (Rank)</h3>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Correlation (ρ)</div>
                    <div class="stat-value">${spearman.r.toFixed(4)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">P-Value</div>
                    <div class="stat-value">${spearman.p_value.toFixed(6)}</div>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <div class="stat-card">
                <div class="stat-label">Covariance</div>
                <div class="stat-value">${data.covariance.toFixed(4)}</div>
            </div>
        </div>
    `;
    
    plotCorrelationAnalysis(data, plotDiv);
}

function plotCorrelationAnalysis(data, plotDiv) {
    const plotData = data.plot_data;
    
    const scatterTrace = {
        x: plotData.x,
        y: plotData.y,
        type: 'scatter',
        mode: 'markers',
        name: 'Data Points',
        marker: { 
            size: 10, 
            color: '#667eea',
            line: { color: '#fff', width: 1 }
        }
    };
    
    const layout = {
        title: `Scatter Plot (r = ${data.pearson.r.toFixed(4)})`,
        xaxis: { title: 'X' },
        yaxis: { title: 'Y' },
        showlegend: false,
        height: 500
    };
    
    Plotly.newPlot(plotDiv, [scatterTrace], layout, { responsive: true });
}