/**
 * Personal Expense Tracker - Chart.js Visualizations
 * Interactive Donut, Bar, and Line charts with Dark Mode adaptation & INR formatting
 */

// Helper to check if dark mode is active
function isDarkModeActive() {
    return document.documentElement.classList.contains('dark');
}

// Chart theme colors helper
function getChartTheme() {
    const isDark = isDarkModeActive();
    return {
        textColor: isDark ? '#94a3b8' : '#64748b',
        gridColor: isDark ? 'rgba(51, 65, 85, 0.4)' : 'rgba(226, 232, 240, 0.7)',
        tooltipBg: isDark ? '#1e293b' : '#0f172a',
        tooltipText: '#ffffff'
    };
}

// Format INR currency for tooltips
function formatTooltipINR(value) {
    if (value === undefined || value === null) return '₹0.00';
    return '₹' + Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Keep track of initialized charts for theme updates
window.appCharts = {};

// --------------------------------------------------------------------
// 1. Dashboard Charts Initialization
// --------------------------------------------------------------------
function initDashboardCharts(catData, monthData, dailyData) {
    const theme = getChartTheme();

    // 1. Category Donut Chart
    const catCanvas = document.getElementById('categoryDonutChart');
    if (catCanvas && catData && catData.labels && catData.labels.length > 0) {
        if (window.appCharts.catDonut) window.appCharts.catDonut.destroy();
        window.appCharts.catDonut = new Chart(catCanvas, {
            type: 'doughnut',
            data: {
                labels: catData.labels,
                datasets: [{
                    data: catData.data,
                    backgroundColor: catData.colors,
                    borderWidth: 2,
                    borderColor: isDarkModeActive() ? '#151d30' : '#ffffff',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: theme.textColor,
                            font: { family: 'Inter', size: 12 },
                            boxWidth: 12,
                            padding: 14
                        }
                    },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.tooltipText,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(ctx) {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                const val = ctx.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${ctx.label}: ${formatTooltipINR(val)} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Monthly Spending Bar Chart
    const monthCanvas = document.getElementById('monthlyBarChart');
    if (monthCanvas && monthData && monthData.labels) {
        if (window.appCharts.monthlyBar) window.appCharts.monthlyBar.destroy();
        window.appCharts.monthlyBar = new Chart(monthCanvas, {
            type: 'bar',
            data: {
                labels: monthData.labels,
                datasets: [{
                    label: 'Monthly Expenditure',
                    data: monthData.data,
                    backgroundColor: '#6366f1',
                    borderRadius: 8,
                    borderSkipped: false,
                    maxBarThickness: 36
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Spent: ${formatTooltipINR(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.textColor, font: { family: 'Inter' } }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: {
                            color: theme.textColor,
                            font: { family: 'Inter' },
                            callback: (val) => '₹' + val.toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }

    // 3. Daily Spending Line Chart
    const dailyCanvas = document.getElementById('dailyLineChart');
    if (dailyCanvas && dailyData && dailyData.labels) {
        if (window.appCharts.dailyLine) window.appCharts.dailyLine.destroy();
        window.appCharts.dailyLine = new Chart(dailyCanvas, {
            type: 'line',
            data: {
                labels: dailyData.labels,
                datasets: [{
                    label: 'Daily Spending',
                    data: dailyData.data,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => ` Spent: ${formatTooltipINR(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.textColor, font: { family: 'Inter' } }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: {
                            color: theme.textColor,
                            font: { family: 'Inter' },
                            callback: (val) => '₹' + val.toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }
}

// --------------------------------------------------------------------
// 2. Detailed Analytics Charts
// --------------------------------------------------------------------
function initAnalyticsCharts(catData, trendData, dowData) {
    const theme = getChartTheme();

    // 1. Category Distribution
    const catCanvas = document.getElementById('analyticsCategoryChart');
    if (catCanvas && catData && catData.labels && catData.labels.length > 0) {
        if (window.appCharts.analyticsCat) window.appCharts.analyticsCat.destroy();
        window.appCharts.analyticsCat = new Chart(catCanvas, {
            type: 'pie',
            data: {
                labels: catData.labels,
                datasets: [{
                    data: catData.data,
                    backgroundColor: catData.colors,
                    borderWidth: 2,
                    borderColor: isDarkModeActive() ? '#151d30' : '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: theme.textColor,
                            font: { family: 'Inter', size: 12 },
                            padding: 12
                        }
                    },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        padding: 10,
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${formatTooltipINR(ctx.raw)}`
                        }
                    }
                }
            }
        });
    }

    // 2. Spending Trend Line
    const trendCanvas = document.getElementById('analyticsTrendChart');
    if (trendCanvas && trendData && trendData.labels) {
        if (window.appCharts.analyticsTrend) window.appCharts.analyticsTrend.destroy();
        window.appCharts.analyticsTrend = new Chart(trendCanvas, {
            type: 'line',
            data: {
                labels: trendData.labels,
                datasets: [{
                    label: 'Expenditure',
                    data: trendData.data,
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 3,
                    pointBackgroundColor: '#4f46e5',
                    pointRadius: 4,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        padding: 10,
                        callbacks: {
                            label: (ctx) => ` Spending: ${formatTooltipINR(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.textColor }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: {
                            color: theme.textColor,
                            callback: (val) => '₹' + val.toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }

    // 3. Day of Week Analysis
    const dowCanvas = document.getElementById('analyticsDowChart');
    if (dowCanvas && dowData && dowData.labels) {
        if (window.appCharts.analyticsDow) window.appCharts.analyticsDow.destroy();
        window.appCharts.analyticsDow = new Chart(dowCanvas, {
            type: 'bar',
            data: {
                labels: dowData.labels,
                datasets: [{
                    label: 'Total Spending',
                    data: dowData.data,
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        padding: 10,
                        callbacks: {
                            label: (ctx) => ` Spent: ${formatTooltipINR(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: theme.textColor }
                    },
                    y: {
                        grid: { color: theme.gridColor },
                        ticks: {
                            color: theme.textColor,
                            callback: (val) => '₹' + val.toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }
}

// --------------------------------------------------------------------
// 3. Budget Comparison Chart
// --------------------------------------------------------------------
function initBudgetChart(histData) {
    const theme = getChartTheme();
    const canvas = document.getElementById('budgetHistChart');
    if (!canvas || !histData || !histData.labels) return;

    if (window.appCharts.budgetHist) window.appCharts.budgetHist.destroy();
    window.appCharts.budgetHist = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: histData.labels,
            datasets: [
                {
                    label: 'Allocated Budget',
                    data: histData.budgets,
                    backgroundColor: 'rgba(99, 102, 241, 0.4)',
                    borderColor: '#6366f1',
                    borderWidth: 1.5,
                    borderRadius: 6
                },
                {
                    label: 'Actual Spent',
                    data: histData.spent,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: theme.textColor, font: { family: 'Inter' } }
                },
                tooltip: {
                    backgroundColor: theme.tooltipBg,
                    padding: 10,
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: ${formatTooltipINR(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: theme.textColor }
                },
                y: {
                    grid: { color: theme.gridColor },
                    ticks: {
                        color: theme.textColor,
                        callback: (val) => '₹' + val.toLocaleString('en-IN')
                    }
                }
            }
        }
    });
}
