from flask import Flask, jsonify, request
from flask_cors import CORS
from datahandler import DataHandler
from datetime import datetime, timedelta
import numpy as np


app = Flask(__name__)
CORS(app)

# -----------------------------
# Initialize Data Handler
# -----------------------------
CSV_PATH = "Dataset_AQI4-5 - Copy.csv"

data_handler = DataHandler(CSV_PATH)


# -----------------------------
# Utility Function
# -----------------------------
def categorize_aqi(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


# -----------------------------
# API Routes
# -----------------------------
@app.route("/api/cities")
def api_cities():
    try:
        cities = data_handler.get_available_cities()
        return jsonify({"cities": cities})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/dashboard/<city>')
def api_dashboard(city):
    """Return dashboard data for the selected city"""
    data = data_handler.get_dashboard_data(city)
    return jsonify(data)


@app.route('/api/aqi_trends', methods=['GET'])
def get_aqi_trends():
    """Return last 7 time entries of AQI trend"""
    city = request.args.get('city')
    data = data_handler.get_aqi_trends(city)
    return jsonify(data)


@app.route('/api/pollutant_averages', methods=['GET'])
def get_pollutant_averages():
    """Return average pollutant concentrations for a city"""
    city = request.args.get('city')
    data = data_handler.get_pollutant_averages(city)
    return jsonify(data)


@app.route("/api/current_aqi")
def api_current_aqi():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "City parameter missing"}), 400

    try:
        data = data_handler.get_dashboard_data(city)
        # If data_handler returns {"error": "..."} directly
        if "error" in data:
            return jsonify(data), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    """Return 7-day AQI forecast for a city (Mon–Sun)"""
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "City parameter missing"}), 400

    try:
        # Get city data from DataHandler
        city_df = data_handler.df[data_handler.df["City"].str.lower() == city.lower()]

        # Use last AQI as baseline, else random
        latest_aqi = (
            float(city_df["AQI"].iloc[-1])
            if not city_df.empty and "AQI" in city_df.columns
            else np.random.randint(50, 150)
        )

        # Generate forecast for 7 days (Mon–Sun)
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        forecast_data = []
        for day in weekdays:
            variation = np.random.uniform(0.85, 1.15)
            aqi_val = round(latest_aqi * variation, 1)
            forecast_data.append({
                "day": day,
                "AQI": aqi_val
            })

        return jsonify(forecast_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pollutant_concentrations")
def pollutant_concentrations():
    """Return recent pollutant concentrations (e.g., 24 latest hours)"""
    city = request.args.get("city")
    df = data_handler.df
    city_data = df[df["City"].str.lower() == city.lower()].tail(24)

    if city_data.empty:
        return jsonify([])

    # Extract pollutants dynamically if columns exist
    pollutants = [col for col in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"] if col in df.columns]
    pollutant_records = city_data[["Time"] + pollutants].to_dict(orient="records")
    return jsonify(pollutant_records)


@app.route("/api/alerts")
def alerts():
    """Generate AQI and pollutant-based alerts for the selected city"""
    city = request.args.get("city")
    df = data_handler.df
    city_data = df[df["City"].str.lower() == city.lower()].tail(1)

    if city_data.empty:
        return jsonify([])

    latest = city_data.iloc[0]
    aqi = float(latest["AQI"])
    alerts = []

    # AQI-based alerts
    if aqi > 150:
        alerts.append({
            "title": "Unhealthy for Sensitive Groups",
            "description": "Avoid prolonged outdoor activities.",
            "type": "warning"
        })
    elif 100 < aqi <= 150:
        alerts.append({
            "title": "Moderate Air Quality",
            "description": "Air quality is acceptable but may affect sensitive groups.",
            "type": "info"
        })
    else:
        alerts.append({
            "title": "Good Air Quality",
            "description": "Air quality is considered satisfactory.",
            "type": "success"
        })

    # Pollutant-specific alerts
    if "O3" in latest and latest["O3"] > 80:
        alerts.append({
            "title": "High Ozone Levels Expected",
            "description": "Ozone levels may cause respiratory discomfort.",
            "type": "danger"
        })
    if "PM2.5" in latest and latest["PM2.5"] > 90:
        alerts.append({
            "title": "High PM2.5 Detected",
            "description": "Fine particulate matter concentration is high.",
            "type": "warning"
        })

    return jsonify(alerts)


# -----------------------------
# Run Flask App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
