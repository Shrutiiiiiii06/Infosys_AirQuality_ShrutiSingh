import pandas as pd
import numpy as np

class DataHandler:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = self._load_data()

    def _load_data(self):
        """Load and clean CSV data."""
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            raise Exception(f"Error reading CSV file: {e}")

        # Normalize column names (remove spaces and unify case)
        df.columns = [col.strip().replace(" ", "_").replace("-", "_") for col in df.columns]

        # Convert Time column to datetime if present
        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')

        # Drop rows with missing or invalid AQI
        if 'AQI' in df.columns:
            df = df.dropna(subset=['AQI'])
            df['AQI'] = pd.to_numeric(df['AQI'], errors='coerce').fillna(0)

        # Fill missing pollutants with 0 (for safety)
        for pollutant in ['PM2.5', 'PM10', 'O3']:
            if pollutant in df.columns:
                df[pollutant] = pd.to_numeric(df[pollutant], errors='coerce').fillna(0)

        return df

    # ----------------------------------------------------
    # 1️⃣ Get all available cities / stations
    # ----------------------------------------------------
    def get_available_cities(self):
        """Return a sorted list of unique cities in the dataset."""
        if 'City' in self.df.columns:
            return sorted(self.df['City'].dropna().unique().tolist())
        return []

    # ----------------------------------------------------
    # 2️⃣ Dashboard summary data for a specific city
    # ----------------------------------------------------
    def get_dashboard_data(self, city):
        """Get AQI, pollutant data, trends, and alerts for a city."""
        city_df = self.df[self.df['City'] == city]
        if city_df.empty:
            return {"error": f"No data found for city: {city}"}

        # Average AQI
        avg_aqi = city_df['AQI'].mean()
        avg_aqi = round(float(avg_aqi), 2) if not np.isnan(avg_aqi) else 0.0

        # Category classification
        if avg_aqi <= 50:
            category = "Good"
        elif avg_aqi <= 100:
            category = "Satisfactory"
        elif avg_aqi <= 200:
            category = "Moderate"
        elif avg_aqi <= 300:
            category = "Poor"
        elif avg_aqi <= 400:
            category = "Very Poor"
        else:
            category = "Severe"

        # Forecast (last 7 AQI values)
        forecast_data = []
        if 'Time' in city_df.columns:
            forecast_data = city_df.tail(7)[['Time', 'AQI']].to_dict(orient="records")

        # Pollutant data (last 24 entries)
        pollutant_data = []
        pollutant_cols = [col for col in ['PM2.5', 'PM10', 'O3'] if col in city_df.columns]
        if pollutant_cols:
            pollutant_data = city_df.tail(24)[['Time'] + pollutant_cols].to_dict(orient="records")

        # Alerts
        alerts = []
        if avg_aqi > 150:
            alerts.append({
                "title": "Unhealthy Air Quality",
                "description": "Avoid prolonged outdoor activities.",
                "type": "warning"
            })
        elif 100 < avg_aqi <= 150:
            alerts.append({
                "title": "Moderate Air Quality",
                "description": "Sensitive groups should limit outdoor exposure.",
                "type": "info"
            })
        else:
            alerts.append({
                "title": "Good Air Quality",
                "description": "Air quality is satisfactory.",
                "type": "success"
            })

        # Ozone alert
        if 'O3' in city_df.columns and city_df['O3'].iloc[-1] > 80:
            alerts.append({
                "title": "High Ozone Levels",
                "description": "Ozone levels may cause respiratory discomfort.",
                "type": "danger"
            })

        return {
            "city": city,
            "AQI": avg_aqi,
            "category": category,
            "forecast": forecast_data,
            "pollutants": pollutant_data,
            "alerts": alerts
        }

    # ----------------------------------------------------
    # 3️⃣ AQI Trends (filtered by time)
    # ----------------------------------------------------
    def get_aqi_trends(self, city, start_time=None, end_time=None):
        city_df = self.df[self.df['City'] == city]
        if city_df.empty:
            return []

        if start_time and end_time:
            mask = (city_df['Time'] >= start_time) & (city_df['Time'] <= end_time)
            city_df = city_df.loc[mask]

        return city_df[['Time', 'AQI']].dropna().to_dict(orient="records")

    # ----------------------------------------------------
    # 4️⃣ Pollutant Averages
    # ----------------------------------------------------
    def get_pollutant_averages(self, city, start_time=None, end_time=None):
        city_df = self.df[self.df['City'] == city]
        if city_df.empty:
            return {}

        if start_time and end_time:
            mask = (city_df['Time'] >= start_time) & (city_df['Time'] <= end_time)
            city_df = city_df.loc[mask]

        return {
            "PM2.5": round(city_df['PM2.5'].mean(), 2) if 'PM2.5' in city_df.columns else None,
            "PM10": round(city_df['PM10'].mean(), 2) if 'PM10' in city_df.columns else None,
            "O3": round(city_df['O3'].mean(), 2) if 'O3' in city_df.columns else None
        }

    # ----------------------------------------------------
    # 5️⃣ Map Data (optional for visualization)
    # ----------------------------------------------------
    def get_map_data(self, start_time=None, end_time=None):
        df = self.df.copy()
        if start_time and end_time:
            mask = (df['Time'] >= start_time) & (df['Time'] <= end_time)
            df = df.loc[mask]

        if {"City", "Latitude", "Longitude"}.issubset(df.columns):
            map_data = df.groupby("City").agg({
                "AQI": "mean",
                "Latitude": "first",
                "Longitude": "first"
            }).reset_index()
            return map_data.to_dict(orient="records")

        return []

