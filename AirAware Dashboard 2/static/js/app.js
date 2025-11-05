document.addEventListener('DOMContentLoaded', () => {
    // 1. Determine the default city and pollutant
    // NOTE: Location selector is removed in HTML, so we default to the first available city (Flask handles this).
    
    // Default pollutant is PM2.5, matching the active button (initial setup)
    const defaultPollutant = 'PM2.5'; 
    
    // Initial data load on page ready
    // We pass null for location, allowing Flask to use the first available city from the data handler.
    fetchDataAndRender(null, defaultPollutant);

    // 3. Event listeners for Pollutant Buttons (Updates Charts)
    document.querySelectorAll('.pollutant-btn').forEach(button => {
        button.addEventListener('click', function() {
            const newPollutant = this.dataset.pollutant;
            
            // --- Visual State Update ---
            document.querySelectorAll('.pollutant-btn').forEach(btn => {
                btn.classList.remove('bg-air-green', 'text-white', 'shadow');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            this.classList.add('bg-air-green', 'text-white', 'shadow');
            this.classList.remove('bg-gray-200', 'text-gray-700');

            // --- Dynamic Fetch and Title Update ---
            document.getElementById('forecast-chart-title').textContent = `${newPollutant} Forecast`;
            fetchDataAndRender(null, newPollutant); // Pass null for location
        });
    });
    
    // 4. Event listener for Metric Toggles (RMSE/MAE Switch)
    document.querySelectorAll('.metric-toggle-btn').forEach(button => {
        button.addEventListener('click', function() {
            const metric = this.dataset.metric;
            
            // Visual Update
            document.querySelectorAll('.metric-toggle-btn').forEach(btn => {
                btn.classList.remove('bg-air-blue', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700');
            });
            this.classList.add('bg-air-blue', 'text-white');
            this.classList.remove('bg-gray-200', 'text-gray-700');

            // Re-render chart with new metric (data is globally cached via 'chartData')
            if (window.performanceChartData) {
                // Update the card header title dynamically
                const metricLabel = metric.toUpperCase();
                document.querySelector('#modelPerformanceChart').closest('.card').querySelector('h3').textContent = `Models Performance (${metricLabel})`;
                
                renderModelPerformanceChart(window.performanceChartData, metric);
            }
        });
    });
});

// --- GLOBAL VARIABLES ---
window.performanceChartData = null;
window.modelPerformanceChartInstance = null;
window.pm25ForecastChartInstance = null;
window.forecastAccuracyChartInstance = null;
window.defaultPollutantLabels = ['PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'];

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
  const defaultPollutant = 'PM2.5';
  fetchDataAndRender(null, defaultPollutant);

  // --- Pollutant Buttons ---
  document.querySelectorAll('.pollutant-btn').forEach(button => {
    button.addEventListener('click', function () {
      const newPollutant = this.dataset.pollutant;

      // Visual updates
      document.querySelectorAll('.pollutant-btn').forEach(btn => {
        btn.classList.remove('bg-air-green', 'text-white', 'shadow');
        btn.classList.add('bg-gray-200', 'text-gray-700');
      });
      this.classList.add('bg-air-green', 'text-white', 'shadow');
      this.classList.remove('bg-gray-200', 'text-gray-700');

      // Update chart title and re-fetch
      document.getElementById('forecast-chart-title').textContent = `${newPollutant} Forecast`;
      fetchDataAndRender(null, newPollutant);
    });
  });

  // --- Metric Toggle Buttons (RMSE/MAE) ---
  document.querySelectorAll('.metric-toggle-btn').forEach(button => {
    button.addEventListener('click', function () {
      const metric = this.dataset.metric;
      document.querySelectorAll('.metric-toggle-btn').forEach(btn => {
        btn.classList.remove('bg-air-blue', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
      });
      this.classList.add('bg-air-blue', 'text-white');
      this.classList.remove('bg-gray-200', 'text-gray-700');

      // Re-render bar chart with new metric
      if (window.performanceChartData) {
        const metricLabel = metric.toUpperCase();
        document.querySelector('#modelPerformanceChart')
          .closest('.card')
          .querySelector('h3').textContent = `Models Performance (${metricLabel})`;
        renderModelPerformanceChart(window.performanceChartData, metric);
      }
    });
  });

  // --- Forecast Dropdowns (INSIDE Forecast Card) ---
  const modelSelect = document.getElementById("modelSelect");
  const horizonSelect = document.getElementById("horizonSelect");
  if (modelSelect && horizonSelect) {
    modelSelect.addEventListener("change", updateForecastGraph);
    horizonSelect.addEventListener("change", updateForecastGraph);
  }

  // Initialize with default forecast
  updateForecastGraph();
});

// --- FETCH AND RENDER DASHBOARD ---
function fetchDataAndRender(location, pollutant) {
  const locationParam = location || '';
  const apiUrl = `/api/data?location=${encodeURIComponent(locationParam)}&pollutant=${encodeURIComponent(pollutant)}`;

  fetch(apiUrl)
    .then(response => response.text())
    .then(text => {
      const cleanedText = text.replace(/NaN/g, 'null').replace(/Infinity/g, 'null');
      try {
        const data = JSON.parse(cleanedText);
        if (data.error) {
          console.error('API Error:', data.error);
          renderPlaceholderCharts();
          return;
        }

        // Cache performance data for metric toggling
        window.performanceChartData = data.model_output.performance;

        const activeMetricButton = document.querySelector('.metric-toggle-btn.bg-air-blue');
        const initialMetric = activeMetricButton ? activeMetricButton.dataset.metric : 'rmse';
        const metricLabel = initialMetric.toUpperCase();

        document.querySelector('#modelPerformanceChart')
          .closest('.card')
          .querySelector('h3').textContent = `Models Performance (${metricLabel})`;

        // Render all charts
        renderModelPerformanceChart(data.model_output.performance, initialMetric);
        renderForecastGraph(data.model_output.forecast, "LSTM", "24h", pollutant);
        updateAccuracyTable(data.model_output.accuracy_table);
        renderForecastAccuracyChart();
        updateDataQuality(data.data_quality);

      } catch (e) {
        console.error('Critical JSON Parsing Error:', e, 'Received Text:', text.substring(0, 500) + '...');
        renderPlaceholderCharts();
        alert('Critical JSON parsing failed. Check server console.');
      }
    })
    .catch(error => {
      console.error('Error fetching data:', error);
      renderPlaceholderCharts();
      alert('Failed to load dashboard data. Check Flask server console.');
    });
}

// --- PLACEHOLDER CHARTS ---
function renderPlaceholderCharts() {
  const destroyAndRedraw = (id, type) => {
    const ctx = document.getElementById(id).getContext('2d');
    const instanceName = id + 'Instance';
    if (window[instanceName]) window[instanceName].destroy();
    window[instanceName] = new Chart(ctx, {
      type: type,
      data: { labels: ['No Data'], datasets: [{ data: [0], label: 'Error', backgroundColor: '#ccc' }] },
      options: { plugins: { legend: { display: false } }, title: { display: true, text: 'Data Loading Failed' } }
    });
  };
  destroyAndRedraw('modelPerformanceChart', 'bar');
  destroyAndRedraw('pm25ForecastChart', 'line');
  destroyAndRedraw('forecastAccuracyChart', 'line');
  document.getElementById('accuracy-table-body').innerHTML =
    `<tr><td colspan="4" class="text-center py-4 text-red-500">Data retrieval failed.</td></tr>`;
}

// --- MODEL PERFORMANCE CHART ---
function renderModelPerformanceChart(performanceData, metric) {
  const ctx = document.getElementById('modelPerformanceChart').getContext('2d');
  if (window.modelPerformanceChartInstance) window.modelPerformanceChartInstance.destroy();

  const scaleFactor = 100;
  const models = ['ARIMA', 'Prophet', 'LSTM', 'XGBoost'];
  const pollutants = performanceData.labels || [];
  const currentMetricKey = metric;

  const modelColors = {
    ARIMA: '#4a90e2',
    Prophet: '#5cb85c',
    LSTM: '#f8d210',
    XGBoost: '#d0021b',
  };

  const datasets = models.map(model => ({
    label: model,
    data: (performanceData[model]?.[currentMetricKey] || []).map(v => v * scaleFactor),
    backgroundColor: modelColors[model],
  }));

  window.modelPerformanceChartInstance = new Chart(ctx, {
    type: 'bar',
    data: { labels: pollutants, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: context => {
              const modelName = context.dataset.label;
              const originalValue = context.raw / scaleFactor;
              return `${modelName}: ${originalValue.toFixed(4)} ${metric.toUpperCase()}`;
            }
          }
        }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: `${metric.toUpperCase()} (x100)` } },
        x: { title: { display: true, text: 'Pollutant' } }
      }
    }
  });
}

// --- FORECAST GRAPH ---
let pm25ForecastChartInstance = null;

function renderForecastGraph(forecastData, selectedModel, horizon, pollutant = "PM2.5") {
  const ctx = document.getElementById("pm25ForecastChart").getContext("2d");
  if (pm25ForecastChartInstance) pm25ForecastChartInstance.destroy();

  const times = forecastData.time || [];
  const actual = forecastData.actual || [];
  const forecast = forecastData.forecast || [];

  pm25ForecastChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: times,
      datasets: [
        {
          label: "Actual",
          data: actual,
          borderColor: "#4a90e2",
          borderWidth: 2,
          fill: false,
          tension: 0.3
        },
        {
          label: `${selectedModel} Forecast`,
          data: forecast,
          borderColor: "#e94e77",
          borderDash: [5, 5],
          borderWidth: 2,
          fill: false,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
        title: {
          display: true,
          text: `${pollutant} Forecast (${selectedModel}, ${horizon})`
        }
      },
      scales: {
        x: { title: { display: true, text: "Time (hours)" } },
        y: { title: { display: true, text: `${pollutant} (µg/m³)` } }
      }
    }
  });
}

// --- UPDATE FORECAST GRAPH ---
function updateForecastGraph() {
  const model = document.getElementById("modelSelect").value;
  const horizon = document.getElementById("horizonSelect").value;
  const pollutant = document.querySelector(".pollutant-btn.bg-air-green")?.dataset.pollutant || "PM2.5";

  // Example simulated forecast data (replace with backend if available)
  const simulatedData = {
    time: ["00h", "03h", "06h", "09h", "12h", "15h", "18h", "21h"],
    actual: [35, 38, 42, 45, 40, 37, 39, 41],
    forecast: [34, 37, 43, 47, 44, 39, 42, 45]
  };

  renderForecastGraph(simulatedData, model, horizon, pollutant);
}

// --- FORECAST ACCURACY CHART ---
function renderForecastAccuracyChart() {
  const ctx = document.getElementById("forecastAccuracyChart").getContext("2d");
  if (window.forecastAccuracyChartInstance) window.forecastAccuracyChartInstance.destroy();

  const horizons = ["3h", "6h", "12h", "24h", "48h"];
  const models = ["ARIMA", "Prophet", "LSTM", "XGBoost"];
  const colors = {
    ARIMA: "#4a90e2",
    Prophet: "#5cb85c",
    LSTM: "#f8d210",
    XGBoost: "#d0021b"
  };

  const datasets = models.map(model => ({
    label: model,
    data: Array.from({ length: horizons.length }, () => Math.random() * 10 + 2),
    borderColor: colors[model],
    fill: false,
    tension: 0.4
  }));

  window.forecastAccuracyChartInstance = new Chart(ctx, {
    type: "line",
    data: { labels: horizons, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
        title: { display: true, text: "Forecast Accuracy vs Horizon" }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: "Accuracy (RMSE ↓)" } },
        x: { title: { display: true, text: "Forecast Horizon" } }
      }
    }
  });
}

// --- ACCURACY TABLE ---
function updateAccuracyTable(accuracyTableData) {
  const tbody = document.getElementById('accuracy-table-body');
  tbody.innerHTML = '';
  if (accuracyTableData && accuracyTableData.length > 0) {
    accuracyTableData.slice(0, 4).forEach(row => {
      const tr = document.createElement('tr');
      tr.className = 'bg-white border-b hover:bg-gray-50';
      tr.innerHTML = `
        <td class="px-3 py-2 font-semibold text-air-green">${row.pollutant}</td>
        <td class="px-3 py-2">${row.best_model}</td>
        <td class="px-3 py-2">${row.rmse.toFixed(4)}</td>
        <td class="px-3 py-2">${row.mae.toFixed(4)}</td>
      `;
      tbody.appendChild(tr);
    });
  } else {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4">No model accuracy data available.</td></tr>`;
  }
}

// --- DATA QUALITY ---
function updateDataQuality(quality) {
  const completeness = quality?.completeness ?? 0;
  const validity = quality?.validity ?? 0;

  const compVal = document.getElementById('completeness-val');
  const compBar = document.getElementById('completeness-bar');
  const valVal = document.getElementById('validity-val');
  const valBar = document.getElementById('validity-bar');

  if (compVal) compVal.textContent = `${completeness}%`;
  if (compBar) compBar.style.width = `${completeness}%`;
  if (valVal) valVal.textContent = `${validity}%`;
  if (valBar) valBar.style.width = `${validity}%`;
}
