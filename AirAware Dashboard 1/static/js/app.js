document.addEventListener('DOMContentLoaded', () => {
    // 1. Determine the default city from the HTML dropdown
    const defaultCityElement = document.querySelector('#location-select option[selected]');
    const defaultCity = defaultCityElement ? defaultCityElement.value : null;

    // Use PM2.5 as the initial pollutant, matching the active button
    const defaultPollutant = 'PM2.5';

    

    // Initial data load on page ready
    if (defaultCity) {
        fetchDataAndRender(defaultCity, defaultPollutant);
    } else {
        console.error("No default city found to load data.");
        // Attempt a load without a city if necessary (Flask will try to default)
        fetchDataAndRender(null, defaultPollutant);
    }

    // 2. Add event listener to the Apply Filters button
    const applyBtn = document.getElementById('apply-filters-btn');
    applyBtn.addEventListener('click', () => {
        const location = document.getElementById('location-select').value;
        const pollutant = document.querySelector('.pollutant-btn.pm25-bg').textContent; // Get the currently active pollutant
        fetchDataAndRender(location, pollutant);
    });

    // 3. Add event listeners for Pollutant Buttons (to select the active one)
    document.querySelectorAll('.pollutant-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all
            document.querySelectorAll('.pollutant-btn').forEach(btn => {
                btn.classList.remove('pm25-bg');
                btn.classList.add('btn-light');
            });
            // Add active class to the clicked button
            this.classList.add('pm25-bg');
            this.classList.remove('btn-light');
            
             // UPDATE: Get location and pollutant to immediately fetch new data 
             const newPollutant = this.textContent;
             const location = document.getElementById('location-select').value;
             document.getElementById('time-series-title').textContent = `${newPollutant} Time Series`;

            // Fetch and render data for the new pollutant
            fetchDataAndRender(location, newPollutant);

        });
    });

    // Ensure the initial title element ID is set in the JS context (must also be set in HTML)
    document.getElementById('timeSeriesChart').closest('.card').querySelector('h5').id = 'time-series-title';
});

// Global references for Chart.js instances to allow for destruction and recreation
window.timeSeriesChartInstance = null;
window.distributionChartInstance = null;
window.correlationChartInstance = null;

function fetchDataAndRender(location, pollutant) {
    // Construct API URL with parameters
    const apiUrl = `/api/data?location=${encodeURIComponent(location)}&pollutant=${encodeURIComponent(pollutant)}`;
    
    // 1. Fetch data from the Flask API endpoint
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                // Throw error if HTTP status is not 200-299
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // JSON WORKAROUND START: Read as text first
            return response.text();
        })

        
        .then(text => {
             // JSON WORKAROUND STEP 2: Replace NaN with 'null' in the string
             const cleanedText = text.replace(/NaN/g, 'null');
             
             try {
                 // Manually parse the cleaned JSON string
                 const data = JSON.parse(cleanedText);
                 
                 console.log("Fetched Data:", data);
                 if (data.error) {
                     console.error('API Error:', data.error);
                     alert('Error loading data: ' + data.error);
                     return;
                 }
                 
                 // 2. Render all sections of the dashboard
                 renderTimeSeriesChart(data.time_series, pollutant);
                 updateStatisticalSummary(data.summary);
                 renderDistributionChart(data.distribution);
                 renderCorrelationChart(data.correlations);
                 updateDataQuality(data.data_quality);

             } catch (e) {
                 // If parsing fails even after cleanup (e.g., if there's non-JSON output)
                 console.error('Manual JSON Parsing Error:', e, 'Received Text:', text);
                 alert('Critical JSON parsing failed. Check server output.');
             }
        })
        .catch(error => {
            console.error('Error fetching or processing data:', error);
            alert('Failed to load dashboard data. Check your Flask server console.');
        });
}

// --- Function to Render Time Series Chart ---
function renderTimeSeriesChart(timeSeriesData, pollutant) {
    const ctx = document.getElementById('timeSeriesChart').getContext('2d');
    
    if (window.timeSeriesChartInstance) {
        window.timeSeriesChartInstance.destroy();
    }
    
    window.timeSeriesChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeSeriesData.x, // Time (e.g., "00:00")
            datasets: [{
                label: `${pollutant} Concentration`,
                data: timeSeriesData.y,
                borderColor: '#5cb85c', // Green color
                backgroundColor: 'rgba(92, 184, 92, 0.2)',
                fill: true,
                tension: 0.4, // Smooth line
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Concentration (μg/m³)' }
                },
                x: {
                    title: { display: false }
                }
            }
        }
    });
}

// --- Function to Render Distribution Chart (Bar Chart) ---
function renderDistributionChart(distributionData, pollutant) {
    const ctx = document.getElementById('distributionChart').getContext('2d');
    
    if (window.distributionChartInstance) {
        window.distributionChartInstance.destroy();
    }
    
    window.distributionChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: distributionData.labels, 
            datasets: [{
                label: 'Frequency',
                data: distributionData.counts,
                backgroundColor: '#34d399', 
                borderColor: '#10b981',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Frequency' }
                },
                x: {
                    type: 'category', // Ensure this is set to category if using string labels
                    // FIX: Update the X-axis title dynamically
                    title: { display: true, text: `${pollutant} Range (μg/m³)` } 
                }
            }
        }
    });
}
// --- Function to Render Pollutant Correlation Chart (Bubble/Scatter) ---
function renderCorrelationChart(correlationMatrix) {
    const ctx = document.getElementById('correlationChart').getContext('2d');
    
    const pollutantLabels = ['PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'];
    const allDataPoints = [];

    // Build data points for all unique pairs
    for (let i = 0; i < pollutantLabels.length; i++) {
        for (let j = 0; j < pollutantLabels.length; j++) {
            const p1 = pollutantLabels[i];
            const p2 = pollutantLabels[j];
            
            // Only plot the upper triangle of the matrix (where i < j) and skip self-correlation
            if (i >= j) continue; 
            
            // Get correlation value from the matrix dict (which uses P1 as row, P2 as column)
            const corrVal = correlationMatrix[p1] ? correlationMatrix[p1][p2] : 0; 
            
            if (corrVal !== null && corrVal !== undefined) {
                allDataPoints.push({
                    x: i, // Index for X-axis
                    y: j, // Index for Y-axis
                    r: Math.max(8, Math.abs(corrVal) * 40), // Radius scaled by correlation strength (min 8px)
                    corr: corrVal // Store actual value
                });
            }
        }
    }

    if (window.correlationChartInstance) {
        window.correlationChartInstance.destroy();
    }

    window.correlationChartInstance = new Chart(ctx, {
        type: 'bubble', 
        data: {
            datasets: [{
                label: 'Correlation Strength',
                data: allDataPoints,
                backgroundColor: (context) => {
                    const value = context.raw.corr;
                    // Use a color scale to visually represent the strength and direction
                    if (value > 0.6) return 'rgba(40, 167, 69, 1.0)';      // Strong Positive (Dark Green)
                    if (value > 0.3) return 'rgba(40, 167, 69, 0.7)';
                    if (value < -0.6) return 'rgba(220, 53, 69, 1.0)';     // Strong Negative (Dark Red)
                    if (value < -0.3) return 'rgba(220, 53, 69, 0.7)';
                    return 'rgba(108, 117, 125, 0.4)'; // Weak (Gray/Less prominent)
                },
                borderColor: 'rgba(0, 0, 0, 0.5)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => {
                             // Correctly map the index back to the pollutant name for the title
                            const raw = items[0].raw;
                            return `${pollutantLabels[raw.x]} vs ${pollutantLabels[raw.y]}`;
                        },
                        label: (context) => {
                            return `Correlation: ${context.raw.corr.toFixed(3)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: pollutantLabels,
                    title: { display: true, text: 'Pollutant 1' },
                    grid: { display: false }
                },
                y: {
                    type: 'category',
                    // Display labels vertically to act as row headers
                    labels: pollutantLabels, 
                    title: { display: true, text: 'Pollutant 2' },
                    grid: { display: false }
                }
            }
        }
    });
}


// --- Function to Update Statistical Summary ---
function updateStatisticalSummary(summary) {
    const safeNumber = (val) => (val !== null && !isNaN(val) ? val.toFixed(1) : 'N/A');

    document.getElementById('stat-mean').textContent = safeNumber(summary.mean);
    document.getElementById('stat-median').textContent = safeNumber(summary.median);
    document.getElementById('stat-max').textContent = safeNumber(summary.max);
    document.getElementById('stat-stddev').textContent = safeNumber(summary.std_dev);
    document.getElementById('stat-data-points').textContent = 
        summary.data_points ? summary.data_points.toLocaleString() : 'N/A';
}


// --- Function to Update Data Quality ---
function updateDataQuality(quality) {
    const completeness = quality.completeness;
    const validity = quality.validity;
    
    // Completeness
    document.getElementById('completeness-val').textContent = `${completeness}%`;
    document.getElementById('completeness-bar').style.width = `${completeness}%`;
    
    // Validity
    document.getElementById('validity-val').textContent = `${validity}%`;
    document.getElementById('validity-bar').style.width = `${validity}%`;
}