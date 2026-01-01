// Chart.js setup and update logic
let chart;

function initChart() {
    const ctx = document.getElementById('chartCanvas');
    if (ctx) {
        if (chart) {
            chart.destroy();
        }
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Closing Price',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(0,0,0,0)',
                    pointBorderColor: 'rgba(0,0,0,0)',
                    pointBorderWidth: 0,
                    pointRadius: 0,
                    pointHoverRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const originalData = chart.originalData;
                                if (originalData && originalData[index]) {
                                    const point = originalData[index];
                                    return `Close: Rs.${point.price?.toFixed(2) || 'N/A'}`;
                                }
                                return `Close: Rs.${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return 'Rs.' + value.toFixed(2);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
}

function updateChart(symbol, data) {
    const chartArea = document.getElementById('chartArea');
    if (data.length === 0) {
        chartArea.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">📊</div>
                <p>No data available for ${symbol}. Click "Add Sample Data" to generate some test data.</p>
            </div>
        `;
        return;
    }

    // Filter to only last 2 years of data
    const now = new Date();
    const twoYearsAgo = new Date(now.getFullYear() - 2, now.getMonth(), now.getDate());
    const filteredData = data.filter(d => {
        if (d.timestamp) {
            return d.timestamp >= twoYearsAgo.getTime();
        } else if (d.date) {
            const dt = new Date(d.date);
            return !isNaN(dt) && dt >= twoYearsAgo;
        }
        return false;
    });

    if (filteredData.length === 0) {
        chartArea.innerHTML = `
            <div class="no-data">
                <div class="no-data-icon">📊</div>
                <p>No data available for ${symbol} in the last 2 years.</p>
            </div>
        `;
        return;
    }

    if (!document.getElementById('chartCanvas')) {
        chartArea.innerHTML = '<canvas id="chartCanvas"></canvas>';
        initChart();
    }

    // Always show predicted data at the end (future dates) as yellow line

    const labels = filteredData.map(d => d.date);
    let predictedStartIdx = null;
    const today = new Date();
    for (let i = 0; i < filteredData.length; i++) {
        const d = filteredData[i];
        if (d.date) {
            const dt = new Date(d.date);
            if (dt > today) {
                predictedStartIdx = i;
                break;
            }
        }
    }
    if (predictedStartIdx === null) predictedStartIdx = filteredData.length;

    // Build historical (blue) and predicted (yellow) lines with seamless transition
    // The predicted line starts at the last historical price, so it connects smoothly
    const realPrices = filteredData.map((d, i) => (i < predictedStartIdx ? d.price : null));
    let predictedPrices = filteredData.map((d, i) => (i >= predictedStartIdx ? d.price : null));
    // If there is at least one predicted point, set the first predicted point to the last historical price
    if (predictedStartIdx < filteredData.length && predictedStartIdx > 0) {
        predictedPrices[predictedStartIdx - 1] = filteredData[predictedStartIdx - 1].price;
    }

    chart.originalData = filteredData;
    chart.data.labels = labels;
    chart.data.datasets = [
        {
            label: `${symbol} Closing Price`,
            data: realPrices,
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: 'rgba(0,0,0,0)',
            pointBorderColor: 'rgba(0,0,0,0)',
            pointBorderWidth: 0,
            pointRadius: 0,
            pointHoverRadius: 0
        },
        {
            label: `${symbol} Predicted`,
            data: predictedPrices,
            borderColor: '#ffeb3b',
            backgroundColor: 'rgba(255, 235, 59, 0.1)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointBackgroundColor: 'rgba(0,0,0,0)',
            pointBorderColor: 'rgba(0,0,0,0)',
            pointBorderWidth: 0,
            pointRadius: 0,
            pointHoverRadius: 0,
            spanGaps: true
        }
    ];
    chart.update();

    const firstDate = filteredData[0]?.date;
    const lastDate = filteredData[filteredData.length - 1]?.date;
    const dataPoints = filteredData.length;
    document.getElementById('chartTitle').innerHTML = `
        <div style="text-align: center;">
            <h2 style="margin: 0; color: #333;">${symbol} Stock Price Chart</h2>
            <p style="margin: 5px 0; color: #666; font-size: 14px;">
                ${dataPoints} data points • ${firstDate} to ${lastDate} (last 2 years)
            </p>
        </div>
    `;
}
