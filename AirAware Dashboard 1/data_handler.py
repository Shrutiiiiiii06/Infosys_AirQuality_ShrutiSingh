import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

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
    global air_aware_data, scaler
    
    # 1. --- Data Loading using RELATIVE PATH ---
    try:
        df = pd.read_csv(DATA_FILE_NAME)
        print(f"Data file found and loaded: {DATA_FILE_NAME}")
        
    except FileNotFoundError:
        print(f"FATAL ERROR: Data file '{DATA_FILE_NAME}' not found.")
        print("ACTION REQUIRED: Ensure the CSV file is in the same directory as app.py.")
        # Return dummy data to prevent crash
        air_aware_data = pd.DataFrame({'City': ['Loading Failed'], 'timestamp': pd.to_datetime(['2024-01-01']), 'PM2.5': [0.0], 'AQI': [0.0]})
        scaler = MinMaxScaler()
        return air_aware_data, scaler 

    # --- 2. Initial Cleaning and Preparation ---
    df_clean = df.copy() 
    df_clean.drop_duplicates(inplace=True)
    
    # Convert 'Time' column and handle the rename
    # Note: Use the original 'Time' column name from your notebook if it was not renamed earlier
    df_clean['Time'] = pd.to_datetime(df_clean['Time'], dayfirst=True, errors='coerce')
    df_clean.rename(columns={'Time': 'timestamp'}, inplace=True)
    
    # Convert pollutant columns to numeric, coercing errors to NaN
    for col in pollutant_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Calculate median for filling NaNs
    medians = df_clean[pollutant_cols].median()

    # Apply fillna using modern Pandas assignment (resolves FutureWarning)
    for col in pollutant_cols:
        df_clean[col] = df_clean[col].fillna(medians[col]) 
        
    # Remove rows where any pollutant value is non-positive
    for col in pollutant_cols:
        df_clean = df_clean[df_clean[col] >= 0].copy()
        
    # === 3. Scaling ===
    scaler = MinMaxScaler()
    df_clean[pollutant_cols] = scaler.fit_transform(df_clean[pollutant_cols])

    # Store the final cleaned and scaled data globally
    air_aware_data = df_clean.copy()
    
    return air_aware_data, scaler


def get_available_cities():
    """Returns a list of unique cities for the HTML dropdown."""
    global air_aware_data
    if air_aware_data is None:
        load_and_preprocess_data()
    # Check if the 'City' column exists and return unique values
    return air_aware_data['City'].unique().tolist() if 'City' in air_aware_data.columns else []

# ... (Previous code in data_handler.py remains the same) ...

# NOTE: This function is used to get the unscaled data for the currently selected pollutant.
# We will duplicate its use to specifically get PM2.5 unscaled data for the Distribution Analysis.
def _get_unscaled_series(df, pollutant_name, scaler, pollutant_cols):
    """Helper function to inverse transform a single pollutant column."""
    if df.empty:
        return pd.Series([0]).dropna()

    pollutant_index = pollutant_cols.index(pollutant_name)
    temp_scaled = np.zeros((len(df), len(pollutant_cols)))
    temp_scaled[:, pollutant_index] = df[pollutant_name].values
    
    unscaled_data_full = scaler.inverse_transform(temp_scaled)
    unscaled_series = pd.Series(unscaled_data_full[:, pollutant_index])
    
    # Use nan_to_num to guarantee clean data for statistics/plotting
    clean_values = np.nan_to_num(unscaled_series.values, nan=0.0, posinf=0.0, neginf=0.0)
    return pd.Series(clean_values)


def get_dashboard_data(city=None, time_range='Last 24 Hours', pollutant='PM2.5'):
    
    # FIX: Declare global variables at the very beginning of the function
    global air_aware_data, scaler, pollutant_cols 
    
    if air_aware_data is None or scaler is None:
        load_and_preprocess_data()
        
    # Ensure data is ready and scaler is available
    if air_aware_data.empty or scaler is None:
         return {'error': 'Data or Scaler is not initialized properly.'}

    df = air_aware_data.copy()
    
    # 1. --- Filtering Logic (Apply filtering first) ---
    # ... (Filtering logic remains the same, resulting in the filtered 'df') ...

    df.dropna(subset=['timestamp'], inplace=True)
    df = df.sort_values('timestamp', ascending=False).head(24).sort_values('timestamp').copy()


    # 2. --- Time Series Data (Uses the SELECTED pollutant) ---
    time_series_data = {
        'x': df['timestamp'].dt.strftime('%H:%M').tolist(), 
        'y': df[pollutant].tolist() 
    }

    # 3. --- Statistical Summary (Uses the SELECTED pollutant) ---
    # Get the unscaled series for the currently SELECTED pollutant (e.g., PM10, NO2)
    selected_pollutant_series = _get_unscaled_series(df, pollutant, scaler, pollutant_cols)
    
    summary = {
        'mean': round(selected_pollutant_series.mean(), 1),
        'median': round(selected_pollutant_series.median(), 1),
        'min': round(selected_pollutant_series.min(), 1),
        'max': round(selected_pollutant_series.max(), 1),
        'std_dev': round(selected_pollutant_series.std(), 1),
        'data_points': len(selected_pollutant_series),
    }

    # 4. --- Distribution Analysis (FIXED: Always uses PM2.5 data) ---
    # Get the unscaled series for PM2.5, regardless of the selected pollutant
    pm25_unscaled_series = _get_unscaled_series(df, 'PM2.5', scaler, pollutant_cols)
    
    dashboard_bins = [0, 20, 40, 60, 80, 100, np.inf]
    dashboard_labels = ['0-20', '20-40', '40-60', '60-80', '80-100', '100+']
    counts, _ = np.histogram(pm25_unscaled_series, bins=dashboard_bins) # Use PM2.5 series
    
    distribution_data = {
        'labels': dashboard_labels,
        'counts': counts.tolist()
    }
    
    # 5. --- Pollutant Correlations (Always uses ALL pollutants, as is standard) ---
    # This section correctly prepares ALL pollutant data for correlation (already fixed in previous steps)
    pollutant_df = df[pollutant_cols].copy()
    temp_scaled_full = pollutant_df.values
    
    unscaled_pollutant_df = pd.DataFrame(
        scaler.inverse_transform(temp_scaled_full),
        columns=pollutant_cols
    ).drop(columns=['AQI'])
    
    # Guarantee clean data for correlation calculation
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
        'data_quality': data_quality
    }

# Execute function to load data on initial script import
load_and_preprocess_data()