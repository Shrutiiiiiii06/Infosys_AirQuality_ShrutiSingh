import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from io import StringIO

# --- Global Data and Configuration ---
air_aware_data = None
scaler = None
pollutant_cols = ['AQI', 'PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO']
DATA_FILE_NAME = "Dataset_AQI4-5 - Copy.csv" 


def load_and_preprocess_data():
    """
    Loads, cleans, and scales the air quality data based on your notebook logic.
    Initializes global air_aware_data (scaled) and scaler object.
    """
    global air_aware_data, scaler, pollutant_cols
    
    # 1. --- Data Loading ---
    try:
        df = pd.read_csv(DATA_FILE_NAME)
        print(f"Data file found and loaded: {DATA_FILE_NAME}")
        
    except FileNotFoundError:
        print(f"FATAL ERROR: Data file '{DATA_FILE_NAME}' not found.")
        print("ACTION REQUIRED: Ensure the CSV file is in the same directory as app.py.")
        air_aware_data = pd.DataFrame({'City': ['Loading Failed'], 'timestamp': pd.to_datetime(['2024-01-01']), 'PM2.5': [0.0], 'AQI': [0.0]})
        scaler = MinMaxScaler()
        return air_aware_data, scaler 

    # --- 2. Cleaning and Preparation ---
    df_clean = df.copy() 
    df_clean.drop_duplicates(inplace=True)
    df_clean['Time'] = pd.to_datetime(df_clean['Time'], dayfirst=True, errors='coerce')
    df_clean.rename(columns={'Time': 'timestamp'}, inplace=True)
    
    # FIX: Convert ALL pollutant columns to numeric first
    for col in pollutant_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    medians = df_clean[pollutant_cols].median()

    # Apply fillna using modern Pandas assignment
    for col in pollutant_cols:
        df_clean[col] = df_clean[col].fillna(medians[col]) 
        
    # Remove rows where any pollutant value is non-positive
    for col in pollutant_cols:
        df_clean = df_clean[df_clean[col] >= 0].copy()
        
    # === 3. Scaling ===
    scaler = MinMaxScaler()
    df_clean[pollutant_cols] = scaler.fit_transform(df_clean[pollutant_cols])

    air_aware_data = df_clean.copy()
    return air_aware_data, scaler


def get_available_cities():
    """Returns a list of unique cities for the HTML dropdown."""
    global air_aware_data
    if air_aware_data is None:
        load_and_preprocess_data()
    return air_aware_data['City'].unique().tolist() if 'City' in air_aware_data.columns else []


def _get_unscaled_series(df, pollutant_name, scaler, pollutant_cols):
    """Helper function to inverse transform a single pollutant column and guarantee clean output."""
    if df.empty:
        return pd.Series([0])

    pollutant_index = pollutant_cols.index(pollutant_name)
    temp_scaled = np.zeros((len(df), len(pollutant_cols)))
    temp_scaled[:, pollutant_index] = df[pollutant_name].values
    
    unscaled_data_full = scaler.inverse_transform(temp_scaled)
    unscaled_series = pd.Series(unscaled_data_full[:, pollutant_index])
    
    # Use nan_to_num to guarantee clean data (converts NaN and Inf to 0.0)
    clean_values = np.nan_to_num(unscaled_series.values, nan=0.0, posinf=0.0, neginf=0.0)
    return pd.Series(clean_values)


def get_dashboard_data(city=None, time_range='Last 24 Hours', pollutant='PM2.5', model='LSTM', horizon=4):
    
    global air_aware_data, scaler, pollutant_cols 
    
    if air_aware_data is None or scaler is None:
        load_and_preprocess_data()
        
    if air_aware_data.empty or scaler is None:
         return {'error': 'Data or Scaler is not initialized properly.'}

    df = air_aware_data.copy()
    
    # 1. --- Filtering Logic ---
    if city and 'City' in df.columns:
        if city not in df['City'].unique():
            city = df['City'].iloc[0]
        df = df[df['City'] == city].copy()
    
    df.dropna(subset=['timestamp'], inplace=True)
    df = df.sort_values('timestamp', ascending=False).head(24).sort_values('timestamp').copy()


    # --- CRITICAL EMPTY CHECK ---
    pollutants_for_eval = ['PM2.5', 'PM10', 'O3', 'NO2'] 
    
    if df.empty:
        print(f"WARNING: No data found for city: {city} in the last 24 records.")
        return {
            'time_series': {'x': [], 'y': []},
            'summary': {
                'mean': 0.0, 'median': 0.0, 'min': 0.0, 'max': 0.0,
                'std_dev': 0.0, 'data_points': 0
            },
            'distribution': {'labels': ['0-20', '20-40', '40-60', '60-80', '80-100', '100+'], 'counts': [0] * 6},
            'correlations': {p: {q: 0.0 for q in pollutant_cols if q != 'AQI'} for p in pollutant_cols if p != 'AQI'},
            'data_quality': {'completeness': 0, 'validity': 0},
            'model_output': simulate_model_data(pd.DataFrame(), int(horizon)) 
        }
    # -----------------------------
    
    
    # 2. --- Time Series Data (Uses the SELECTED pollutant) ---
    time_series_data = {
        'x': df['timestamp'].dt.strftime('%H:%M').tolist(), 
        'y': df[pollutant].tolist() 
    }

    # 3. --- Statistical Summary (Uses the SELECTED pollutant) ---
    selected_pollutant_series = _get_unscaled_series(df, pollutant, scaler, pollutant_cols)
    
    summary = {
        'mean': round(selected_pollutant_series.mean(), 1),
        'median': round(selected_pollutant_series.median(), 1),
        'min': round(selected_pollutant_series.min(), 1),
        'max': round(selected_pollutant_series.max(), 1),
        'std_dev': round(selected_pollutant_series.std(), 1),
        'data_points': len(selected_pollutant_series),
    }

    # 4. --- Distribution Analysis (Uses the SELECTED pollutant) ---
    dashboard_bins = [0, 20, 40, 60, 80, 100, np.inf]
    dashboard_labels = ['0-20', '20-40', '40-60', '60-80', '80-100', '100+']
    
    counts, _ = np.histogram(selected_pollutant_series, bins=dashboard_bins) 
    
    distribution_data = {
        'labels': dashboard_labels,
        'counts': counts.tolist()
    }
    
    # 5. --- Pollutant Correlations (Always uses ALL pollutants) ---
    pollutant_df = df[pollutant_cols].copy()
    temp_scaled_full = pollutant_df.values
    
    unscaled_pollutant_df = pd.DataFrame(
        scaler.inverse_transform(temp_scaled_full),
        columns=pollutant_cols
    ).drop(columns=['AQI'])
    
    unscaled_pollutant_df.fillna(0, inplace=True) 
    
    corr_matrix = unscaled_pollutant_df.corr().abs()
    
    correlation_data = corr_matrix.to_dict()
    
    # 6. --- Data Quality (Static as per screenshot) ---
    data_quality = {'completeness': 92, 'validity': 87} 

    return {
        'time_series': time_series_data,
        'summary': summary,
        'distribution': distribution_data,
        'correlations': correlation_data, 
        'data_quality': data_quality,
        'model_output': simulate_model_data(df, int(horizon), model)
    }


def simulate_model_data(df_filtered=None, horizon=4, selected_model='LSTM'):
    """
    Generates structured model results (RMSE/MAE, Forecast) based on the filtered data.
    """
    
    pollutants_for_eval = ['PM2.5', 'PM10', 'O3', 'NO2'] 
    models_list = ['ARIMA', 'Prophet', 'LSTM', 'XGBoost']

    # --- SIMULATE MODEL EVALUATION DATA (Grouped Bar Chart) ---
    performance_data = {'labels': pollutants_for_eval}
    
    for model in models_list:
        # Generate simulated RMSE/MAE data for each pollutant
        performance_data[model] = {
            # Note: We use raw RMSE/MAE for simplicity; JS scales it by 100
            'rmse': np.random.uniform(0.01, 0.08, size=len(pollutants_for_eval)).tolist(),
            'mae': np.random.uniform(0.005, 0.05, size=len(pollutants_for_eval)).tolist(),
        }

    # --- Handle empty DataFrame input for forecast ---
    if df_filtered is None or df_filtered.empty:
        timestamps = [f"{h:02d}:00" for h in range(20)]
        forecast_hours = [f"+{h}H" for h in range(1, horizon + 1)]
        full_labels = timestamps + forecast_hours
        
        return {
            'performance': performance_data,
            'forecast': {
                'labels': full_labels,
                'actual': [0] * 20 + [None] * horizon,
                'forecast': [None] * 20 + [0] * horizon,
                'ci_lower': [None] * 20 + [0] * horizon,
                'ci_upper': [None] * 20 + [0] * horizon
            },
            'accuracy_table': [
                {'pollutant': p, 'best_model': 'N/A', 'rmse': 0, 'mae': 0} for p in pollutants_for_eval
            ]
        }


    # --- SIMULATE LIVE FORECAST ---
    
    historical_points = 20
    timestamps = df_filtered['timestamp'].head(historical_points).dt.strftime('%H:%M').tolist()
    forecast_hours = [f"+{h}H" for h in range(1, horizon + 1)]
    full_labels = timestamps + forecast_hours
    
    historical_pm25 = df_filtered['PM2.5'].head(historical_points).tolist()
    
    last_actual = historical_pm25[-1] if historical_pm25 else 0.1
    # Forecast trend uses the selected model (simulated)
    # The simulation varies slightly based on the selected model name
    trend_factor = {'LSTM': 0.05, 'Prophet': 0.04, 'ARIMA': 0.03, 'XGBoost': 0.06}[selected_model]
    
    forecast_values = [last_actual + (i * trend_factor) + np.random.uniform(-0.01, 0.01) for i in range(1, horizon + 1)] 
    
    # Simulate confidence intervals (CI) based on the forecast values
    ci_lower = [f - 0.02 * i for i, f in enumerate(forecast_values)]
    ci_upper = [f + 0.02 * i for i, f in enumerate(forecast_values)]
    
    
    forecast_line = [None] * historical_points + forecast_values
    actual_line = historical_pm25 + [None] * horizon
    
    ci_lower_line = [None] * historical_points + ci_lower
    ci_upper_line = [None] * historical_points + ci_upper
    

    # ----------------------------------------------------
    # Best Model Accuracy (Table Data)
    # ----------------------------------------------------
    accuracy_table = []
    # Simulate Best Model based on lowest RMSE from the performance_data
    best_models_by_pollutant = {}
    for i, p in enumerate(pollutants_for_eval):
        rmses = {m: performance_data[m]['rmse'][i] for m in models_list}
        best_model_name = min(rmses, key=rmses.get)
        
        accuracy_table.append({
            'pollutant': p, 
            'best_model': best_model_name, 
            'rmse': rmses[best_model_name], 
            'mae': performance_data[best_model_name]['mae'][i]
        })
    
    return {
        'performance': performance_data,
        'forecast': {
            'labels': full_labels,
            'actual': actual_line,
            'forecast': forecast_line,
            'ci_lower': ci_lower_line,
            'ci_upper': ci_upper_line
        },
        'accuracy_table': accuracy_table
    }

# Execute function to load data on initial script import
load_and_preprocess_data()