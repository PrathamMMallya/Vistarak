import numpy as np
import scipy.stats as stats
from scipy.stats import norm, binom, poisson, t as t_dist
import json

def process_statistics(data_input, operation_type):
    """
    COMPREHENSIVE Statistics & Probability Module
    
    Handles:
    ✅ Descriptive Statistics (mean, median, mode, std, variance, quartiles)
    ✅ Probability Distributions (normal, binomial, Poisson)
    ✅ Hypothesis Testing (t-test, z-test)
    ✅ Regression Analysis (linear, polynomial)
    ✅ Correlation Analysis
    ✅ Box plots, histograms, scatter plots
    """
    try:
        operation = operation_type.lower()
        
        if operation == 'descriptive':
            return calculate_descriptive_statistics(data_input)
        elif operation == 'normal_distribution':
            return calculate_normal_distribution(data_input)
        elif operation == 'binomial_distribution':
            return calculate_binomial_distribution(data_input)
        elif operation == 'poisson_distribution':
            return calculate_poisson_distribution(data_input)
        elif operation == 'hypothesis_test':
            return perform_hypothesis_test(data_input)
        elif operation == 'regression':
            return perform_regression_analysis(data_input)
        elif operation == 'correlation':
            return calculate_correlation(data_input)
        else:
            raise Exception(f"Unknown operation: {operation_type}")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Statistics processing error: {str(e)}")


# ============================================================================
# DESCRIPTIVE STATISTICS
# ============================================================================

def calculate_descriptive_statistics(data_input):
    """Calculate comprehensive descriptive statistics"""
    # Parse data
    if isinstance(data_input, str):
        # Handle CSV-like input: "1,2,3,4,5" or "1 2 3 4 5"
        data = [float(x.strip()) for x in data_input.replace(',', ' ').split()]
    elif isinstance(data_input, list):
        data = [float(x) for x in data_input]
    else:
        raise Exception("Invalid data format")
    
    if len(data) == 0:
        raise Exception("No data provided")
    
    data_array = np.array(data)
    
    # Calculate statistics
    mean_val = float(np.mean(data_array))
    median_val = float(np.median(data_array))
    
    # Mode (handle multiple modes)
    from scipy import stats as sp_stats
    mode_result = sp_stats.mode(data_array, keepdims=True)
    mode_val = float(mode_result.mode[0]) if len(mode_result.mode) > 0 else None
    
    std_val = float(np.std(data_array, ddof=1))  # Sample std
    variance_val = float(np.var(data_array, ddof=1))  # Sample variance
    
    # Quartiles
    q1 = float(np.percentile(data_array, 25))
    q2 = float(np.percentile(data_array, 50))  # Same as median
    q3 = float(np.percentile(data_array, 75))
    iqr = q3 - q1
    
    min_val = float(np.min(data_array))
    max_val = float(np.max(data_array))
    range_val = max_val - min_val
    
    # Skewness and Kurtosis
    skewness = float(sp_stats.skew(data_array))
    kurtosis = float(sp_stats.kurtosis(data_array))
    
    # Five number summary
    five_number_summary = {
        'minimum': min_val,
        'q1': q1,
        'median': median_val,
        'q3': q3,
        'maximum': max_val
    }
    
    # Generate visualizations data
    histogram_data = generate_histogram_data(data_array)
    boxplot_data = generate_boxplot_data(data_array, five_number_summary)
    
    return {
        'type': 'descriptive_statistics',
        'n': len(data),
        'statistics': {
            'mean': mean_val,
            'median': median_val,
            'mode': mode_val,
            'std_dev': std_val,
            'variance': variance_val,
            'min': min_val,
            'max': max_val,
            'range': range_val,
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'iqr': iqr,
            'skewness': skewness,
            'kurtosis': kurtosis
        },
        'five_number_summary': five_number_summary,
        'plot_data': {
            'histogram': histogram_data,
            'boxplot': boxplot_data,
            'raw_data': data
        }
    }


def generate_histogram_data(data):
    """Generate histogram data"""
    counts, bins = np.histogram(data, bins='auto')
    
    return {
        'counts': counts.tolist(),
        'bins': bins.tolist(),
        'bin_centers': [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
    }


def generate_boxplot_data(data, five_num_summary):
    """Generate boxplot data"""
    q1 = five_num_summary['q1']
    q3 = five_num_summary['q3']
    iqr = q3 - q1
    
    # Outliers (values beyond 1.5*IQR from quartiles)
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    outliers = [float(x) for x in data if x < lower_fence or x > upper_fence]
    
    return {
        'min': five_num_summary['minimum'],
        'q1': five_num_summary['q1'],
        'median': five_num_summary['median'],
        'q3': five_num_summary['q3'],
        'max': five_num_summary['maximum'],
        'outliers': outliers,
        'lower_fence': float(lower_fence),
        'upper_fence': float(upper_fence)
    }


# ============================================================================
# PROBABILITY DISTRIBUTIONS
# ============================================================================

def calculate_normal_distribution(params):
    """Calculate normal distribution"""
    # Params: {'mean': 0, 'std': 1, 'x_value': None}
    mean = float(params.get('mean', 0))
    std = float(params.get('std', 1))
    
    # Generate PDF curve
    x = np.linspace(mean - 4*std, mean + 4*std, 500)
    pdf = norm.pdf(x, mean, std)
    cdf = norm.cdf(x, mean, std)
    
    # Calculate probabilities if x_value provided
    probabilities = {}
    if 'x_value' in params and params['x_value'] is not None:
        x_val = float(params['x_value'])
        probabilities = {
            'p_less_than': float(norm.cdf(x_val, mean, std)),
            'p_greater_than': float(1 - norm.cdf(x_val, mean, std)),
            'pdf_at_x': float(norm.pdf(x_val, mean, std)),
            'z_score': float((x_val - mean) / std)
        }
    
    # Confidence intervals
    ci_95 = {
        'lower': float(norm.ppf(0.025, mean, std)),
        'upper': float(norm.ppf(0.975, mean, std))
    }
    ci_99 = {
        'lower': float(norm.ppf(0.005, mean, std)),
        'upper': float(norm.ppf(0.995, mean, std))
    }
    
    return {
        'type': 'normal_distribution',
        'parameters': {
            'mean': mean,
            'std_dev': std,
            'variance': std**2
        },
        'probabilities': probabilities,
        'confidence_intervals': {
            '95%': ci_95,
            '99%': ci_99
        },
        'plot_data': {
            'x': x.tolist(),
            'pdf': pdf.tolist(),
            'cdf': cdf.tolist(),
            'mean_line': mean,
            'std_lines': [mean - std, mean, mean + std, mean + 2*std, mean - 2*std]
        }
    }


def calculate_binomial_distribution(params):
    """Calculate binomial distribution"""
    # Params: {'n': 10, 'p': 0.5}
    n = int(params.get('n', 10))
    p = float(params.get('p', 0.5))
    
    if not (0 <= p <= 1):
        raise Exception("Probability p must be between 0 and 1")
    
    # Generate PMF
    x = np.arange(0, n + 1)
    pmf = binom.pmf(x, n, p)
    cdf = binom.cdf(x, n, p)
    
    # Statistics
    mean_val = n * p
    variance = n * p * (1 - p)
    std = np.sqrt(variance)
    
    return {
        'type': 'binomial_distribution',
        'parameters': {
            'n': n,
            'p': p,
            'q': 1 - p
        },
        'statistics': {
            'mean': float(mean_val),
            'variance': float(variance),
            'std_dev': float(std)
        },
        'plot_data': {
            'x': x.tolist(),
            'pmf': pmf.tolist(),
            'cdf': cdf.tolist()
        }
    }


def calculate_poisson_distribution(params):
    """Calculate Poisson distribution"""
    # Params: {'lambda': 3}
    lambda_val = float(params.get('lambda', 3))
    
    if lambda_val <= 0:
        raise Exception("Lambda must be positive")
    
    # Generate PMF (up to reasonable range)
    x_max = int(lambda_val + 5 * np.sqrt(lambda_val))
    x = np.arange(0, x_max + 1)
    pmf = poisson.pmf(x, lambda_val)
    cdf = poisson.cdf(x, lambda_val)
    
    # Statistics
    mean_val = lambda_val
    variance = lambda_val
    std = np.sqrt(variance)
    
    return {
        'type': 'poisson_distribution',
        'parameters': {
            'lambda': lambda_val
        },
        'statistics': {
            'mean': float(mean_val),
            'variance': float(variance),
            'std_dev': float(std)
        },
        'plot_data': {
            'x': x.tolist(),
            'pmf': pmf.tolist(),
            'cdf': cdf.tolist()
        }
    }


# ============================================================================
# HYPOTHESIS TESTING
# ============================================================================

def perform_hypothesis_test(params):
    """Perform hypothesis testing (t-test or z-test)"""
    test_type = params.get('test_type', 'one_sample_t')
    
    if test_type == 'one_sample_t':
        return one_sample_t_test(params)
    elif test_type == 'two_sample_t':
        return two_sample_t_test(params)
    elif test_type == 'z_test':
        return z_test(params)
    else:
        raise Exception(f"Unknown test type: {test_type}")


def one_sample_t_test(params):
    """One-sample t-test"""
    # Parse data
    data = parse_data_input(params.get('data'))
    mu_0 = float(params.get('mu_0', 0))  # Null hypothesis mean
    alpha = float(params.get('alpha', 0.05))  # Significance level
    
    # Perform t-test
    t_statistic, p_value = stats.ttest_1samp(data, mu_0)
    
    df = len(data) - 1
    critical_value_two_tail = t_dist.ppf(1 - alpha/2, df)
    critical_value_left = t_dist.ppf(alpha, df)
    critical_value_right = t_dist.ppf(1 - alpha, df)
    
    # Decision
    reject_null = bool(p_value < alpha)
    
    # Sample statistics
    sample_mean = float(np.mean(data))
    sample_std = float(np.std(data, ddof=1))
    
    # Generate t-distribution plot
    x = np.linspace(-4, 4, 500)
    pdf = t_dist.pdf(x, df)
    
    return {
        'type': 'one_sample_t_test',
        'test_statistic': float(t_statistic),
        'p_value': float(p_value),
        'degrees_of_freedom': df,
        'critical_values': {
            'two_tailed': float(critical_value_two_tail),
            'left_tailed': float(critical_value_left),
            'right_tailed': float(critical_value_right)
        },
        'decision': {
            'reject_null': reject_null,
            'alpha': alpha,
            'conclusion': f"{'Reject' if reject_null else 'Fail to reject'} null hypothesis at α={alpha}"
        },
        'sample_statistics': {
            'mean': sample_mean,
            'std_dev': sample_std,
            'n': len(data)
        },
        'null_hypothesis': f"μ = {mu_0}",
        'plot_data': {
            'x': x.tolist(),
            'pdf': pdf.tolist(),
            't_statistic': float(t_statistic),
            'critical_values': [float(-critical_value_two_tail), float(critical_value_two_tail)]
        }
    }


def two_sample_t_test(params):
    """Two-sample t-test"""
    data1 = parse_data_input(params.get('data1'))
    data2 = parse_data_input(params.get('data2'))
    alpha = float(params.get('alpha', 0.05))
    
    # Perform t-test
    t_statistic, p_value = stats.ttest_ind(data1, data2)
    
    df = len(data1) + len(data2) - 2
    critical_value = t_dist.ppf(1 - alpha/2, df)
    
    reject_null = bool(p_value < alpha)
    
    return {
        'type': 'two_sample_t_test',
        'test_statistic': float(t_statistic),
        'p_value': float(p_value),
        'degrees_of_freedom': df,
        'critical_value': float(critical_value),
        'decision': {
            'reject_null': reject_null,
            'alpha': alpha,
            'conclusion': f"{'Reject' if reject_null else 'Fail to reject'} null hypothesis"
        },
        'sample_statistics': {
            'mean1': float(np.mean(data1)),
            'mean2': float(np.mean(data2)),
            'std1': float(np.std(data1, ddof=1)),
            'std2': float(np.std(data2, ddof=1)),
            'n1': len(data1),
            'n2': len(data2)
        }
    }


def z_test(params):
    """Z-test for population mean"""
    data = parse_data_input(params.get('data'))
    mu_0 = float(params.get('mu_0', 0))
    sigma = float(params.get('sigma'))  # Population std (known)
    alpha = float(params.get('alpha', 0.05))
    
    n = len(data)
    sample_mean = np.mean(data)
    
    # Z-statistic
    z_statistic = (sample_mean - mu_0) / (sigma / np.sqrt(n))
    
    # P-value (two-tailed)
    p_value = 2 * (1 - norm.cdf(abs(z_statistic)))
    
    critical_value = norm.ppf(1 - alpha/2)
    reject_null = bool(abs(z_statistic) > critical_value)
    
    # Generate plot
    x = np.linspace(-4, 4, 500)
    pdf = norm.pdf(x, 0, 1)
    
    return {
        'type': 'z_test',
        'test_statistic': float(z_statistic),
        'p_value': float(p_value),
        'critical_value': float(critical_value),
        'decision': {
            'reject_null': reject_null,
            'alpha': alpha,
            'conclusion': f"{'Reject' if reject_null else 'Fail to reject'} null hypothesis"
        },
        'plot_data': {
            'x': x.tolist(),
            'pdf': pdf.tolist(),
            'z_statistic': float(z_statistic),
            'critical_values': [float(-critical_value), float(critical_value)]
        }
    }


# ============================================================================
# REGRESSION ANALYSIS
# ============================================================================

def perform_regression_analysis(params):
    """Perform regression analysis"""
    regression_type = params.get('regression_type', 'linear')
    
    x_data = parse_data_input(params.get('x_data'))
    y_data = parse_data_input(params.get('y_data'))
    
    if len(x_data) != len(y_data):
        raise Exception("X and Y data must have same length")
    
    if regression_type == 'linear':
        return linear_regression(x_data, y_data)
    elif regression_type == 'polynomial':
        degree = int(params.get('degree', 2))
        return polynomial_regression(x_data, y_data, degree)
    else:
        raise Exception(f"Unknown regression type: {regression_type}")


def linear_regression(x_data, y_data):
    """Linear regression analysis"""
    x = np.array(x_data)
    y = np.array(y_data)
    
    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Predictions
    y_pred = slope * x + intercept
    
    # Residuals
    residuals = y - y_pred
    
    # R-squared
    r_squared = r_value ** 2
    
    # Mean squared error
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)
    
    # Generate regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    
    return {
        'type': 'linear_regression',
        'equation': f"y = {slope:.4f}x + {intercept:.4f}",
        'coefficients': {
            'slope': float(slope),
            'intercept': float(intercept)
        },
        'statistics': {
            'r': float(r_value),
            'r_squared': float(r_squared),
            'p_value': float(p_value),
            'std_err': float(std_err),
            'mse': float(mse),
            'rmse': float(rmse)
        },
        'plot_data': {
            'x_original': x.tolist(),
            'y_original': y.tolist(),
            'x_line': x_line.tolist(),
            'y_line': y_line.tolist(),
            'residuals': residuals.tolist()
        }
    }


def polynomial_regression(x_data, y_data, degree):
    """Polynomial regression analysis"""
    x = np.array(x_data)
    y = np.array(y_data)
    
    # Fit polynomial
    coefficients = np.polyfit(x, y, degree)
    polynomial = np.poly1d(coefficients)
    
    # Predictions
    y_pred = polynomial(x)
    
    # Residuals
    residuals = y - y_pred
    
    # R-squared
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Generate curve
    x_line = np.linspace(x.min(), x.max(), 200)
    y_line = polynomial(x_line)
    
    # Build equation string
    equation_terms = []
    for i, coef in enumerate(coefficients):
        power = degree - i
        if power == 0:
            equation_terms.append(f"{coef:.4f}")
        elif power == 1:
            equation_terms.append(f"{coef:.4f}x")
        else:
            equation_terms.append(f"{coef:.4f}x^{power}")
    
    equation = "y = " + " + ".join(equation_terms)
    
    return {
        'type': 'polynomial_regression',
        'degree': degree,
        'equation': equation,
        'coefficients': coefficients.tolist(),
        'statistics': {
            'r_squared': float(r_squared),
            'mse': float(np.mean(residuals ** 2)),
            'rmse': float(np.sqrt(np.mean(residuals ** 2)))
        },
        'plot_data': {
            'x_original': x.tolist(),
            'y_original': y.tolist(),
            'x_line': x_line.tolist(),
            'y_line': y_line.tolist(),
            'residuals': residuals.tolist()
        }
    }


# ============================================================================
# CORRELATION ANALYSIS
# ============================================================================

def calculate_correlation(params):
    """Calculate correlation between two variables"""
    x_data = parse_data_input(params.get('x_data'))
    y_data = parse_data_input(params.get('y_data'))
    
    if len(x_data) != len(y_data):
        raise Exception("X and Y data must have same length")
    
    x = np.array(x_data)
    y = np.array(y_data)
    
    # Pearson correlation
    pearson_r, pearson_p = stats.pearsonr(x, y)
    
    # Spearman correlation
    spearman_r, spearman_p = stats.spearmanr(x, y)
    
    # Covariance
    covariance = np.cov(x, y)[0, 1]
    
    return {
        'type': 'correlation_analysis',
        'pearson': {
            'r': float(pearson_r),
            'p_value': float(pearson_p),
            'interpretation': interpret_correlation(pearson_r)
        },
        'spearman': {
            'r': float(spearman_r),
            'p_value': float(spearman_p)
        },
        'covariance': float(covariance),
        'plot_data': {
            'x': x.tolist(),
            'y': y.tolist()
        }
    }


def interpret_correlation(r):
    """Interpret correlation strength"""
    abs_r = abs(r)
    if abs_r >= 0.9:
        return "Very strong"
    elif abs_r >= 0.7:
        return "Strong"
    elif abs_r >= 0.5:
        return "Moderate"
    elif abs_r >= 0.3:
        return "Weak"
    else:
        return "Very weak"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_data_input(data):
    """Parse various data input formats"""
    if isinstance(data, str):
        # CSV format: "1,2,3,4,5" or space-separated
        return [float(x.strip()) for x in data.replace(',', ' ').split()]
    elif isinstance(data, list):
        return [float(x) for x in data]
    else:
        raise Exception("Invalid data format")