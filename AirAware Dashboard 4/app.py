import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# -----------------------------
# Page Config & Styling
# -----------------------------
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")

st.markdown("""
    <style>
    .main {
        background: linear-gradient(180deg, #f7f3ff 0%, #fefeff 100%);
        color: #2e2961;
    }
    h2 {
        color: #4B0082;
        text-align: center;
        font-weight: 700;
    }
    h5 {
        color: #6c63ff;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Helper Functions
# -----------------------------
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip().str.replace(" ", "_")

    # Rename city/station column
    if "City" not in df.columns:
        for alt in ["station", "Station", "city", "location", "Site"]:
            if alt in df.columns:
                df.rename(columns={alt: "City"}, inplace=True)
                break

    # Convert time/date
    for col in ["Time", "Date", "datetime", "date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df.rename(columns={col: "Time"}, inplace=True)
            break

    # Convert pollutant columns
    for col in ["AQI", "PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["City"], inplace=True)
    return df


def get_alert(aqi):
    if pd.isna(aqi):
        return ("No AQI Data", "⚪")
    if aqi <= 50:
        return ("Good air quality expected. Enjoy the outdoors!", "🟢")
    elif aqi <= 100:
        return ("Moderate air quality. Sensitive groups be cautious.", "🟡")
    elif aqi <= 150:
        return ("Unhealthy for sensitive groups.", "🟠")
    elif aqi <= 200:
        return ("Unhealthy air quality. Limit outdoor activity.", "🔴")
    else:
        return ("Hazardous air quality! Stay indoors.", "🟣")


def get_aqi_color(aqi):
    if aqi <= 50:
        return "#50f05c", "Good"
    elif aqi <= 100:
        return "#f0d050", "Moderate"
    elif aqi <= 150:
        return "#f0a550", "Unhealthy (SG)"
    elif aqi <= 200:
        return "#f05050", "Unhealthy"
    else:
        return "#c040c0", "Hazardous"

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.title("⚙️ Controls")
uploaded_file = st.sidebar.file_uploader("Upload Air Quality Dataset (CSV)", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    st.sidebar.info("Upload a dataset to begin.")
    st.stop()

stations = sorted(df["City"].unique().tolist())
pollutants = [p for p in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"] if p in df.columns]

selected_station = st.sidebar.selectbox("Monitoring Station", stations)
time_range = st.sidebar.selectbox("Time Range", ["Last 24 Hours", "Last 7 Days"])
selected_pollutant = st.sidebar.selectbox("Pollutant", pollutants)
forecast_horizon = st.sidebar.slider("Forecast Horizon (hours)", 6, 48, 24)
st.sidebar.button("Update Dashboard")

# -----------------------------
# Data Filtering
# -----------------------------
city_df = df[df["City"] == selected_station].copy()
if "Time" in city_df.columns:
    city_df = city_df.sort_values("Time")

if "Time" in city_df.columns:
    if time_range == "Last 24 Hours":
        city_df = city_df[city_df["Time"] >= city_df["Time"].max() - timedelta(hours=24)]
    elif time_range == "Last 7 Days":
        city_df = city_df[city_df["Time"] >= city_df["Time"].max() - timedelta(days=7)]

latest_aqi = city_df["AQI"].iloc[-1] if not city_df.empty else np.nan
alert_msg, alert_icon = get_alert(latest_aqi)

# -----------------------------
# Header
# -----------------------------
st.markdown("<h2>🌤️ Streamlit Air Quality Dashboard</h2>", unsafe_allow_html=True)
st.markdown("<h5>Dynamic AQI & Pollutant Visualization</h5>", unsafe_allow_html=True)
st.write("---")

col1, col2, col3 = st.columns([1.5, 2, 2])

# -----------------------------
# Current AQI (Full Donut)
# -----------------------------
with col1:
    st.subheader("Current Air Quality")
    if not pd.isna(latest_aqi):
        color, status = get_aqi_color(latest_aqi)
        fig_donut = go.Figure(go.Pie(
            values=[latest_aqi, 500 - latest_aqi],
            hole=0.8,
            marker_colors=[color, "#ececec"],
            textinfo="none"
        ))
        fig_donut.update_layout(
            annotations=[{
                'text': f"<b>{int(latest_aqi)}</b><br>{status}",
                'x': 0.5, 'y': 0.5, 'font_size': 22, 'showarrow': False
            }],
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            height=260,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("No AQI data available for this station.")

# -----------------------------
# Pollutant Forecast (Fixed)
# -----------------------------
with col2:
    st.subheader(f"{selected_pollutant} Forecast")
    if selected_pollutant in city_df.columns and not city_df.empty:
        recent_vals = city_df[selected_pollutant].dropna().tail(10)
        base = recent_vals.mean() if not recent_vals.empty else 0

        future_times = [city_df["Time"].max() + timedelta(hours=i) for i in range(1, forecast_horizon + 1)]
        forecast_vals = [max(0, base + random.uniform(-5, 5)) for _ in future_times]

        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(
            x=city_df["Time"], y=city_df[selected_pollutant],
            mode="lines+markers", name="Historical", line=dict(color="#3A5FFF")
        ))
        fig_forecast.add_trace(go.Scatter(
            x=future_times, y=forecast_vals,
            mode="lines+markers", name="Forecast",
            line=dict(dash="dot", color="#FF7A00")
        ))
        fig_forecast.update_layout(
            yaxis_title=f"{selected_pollutant} (µg/m³)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.warning("No data for selected pollutant.")

# -----------------------------
# Pollutant Trends (Clean)
# -----------------------------
with col3:
    st.subheader("Weekly Pollutant Trends")
    if "Time" in city_df.columns and not city_df.empty:
        city_df["Weekday"] = city_df["Time"].dt.day_name()

        pollutant_colors = {
            "PM2.5": "#6A0DAD", "PM10": "#1E90FF", "O3": "#32CD32",
            "NO2": "#FFA500", "SO2": "#FF69B4", "CO": "#A52A2A"
        }

        fig_trend = go.Figure()
        for p in pollutants:
            daily_avg = city_df.groupby("Weekday")[p].mean().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            )
            fig_trend.add_trace(go.Scatter(
                x=daily_avg.index, y=daily_avg.values,
                mode="lines+markers",
                name=p,
                line=dict(width=3, color=pollutant_colors.get(p, "#333")),
                fill='tozeroy'
            ))

        fig_trend.update_layout(
            yaxis_title="Concentration (µg/m³)",
            xaxis_title="Day of Week",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
            margin=dict(t=40, b=60)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Not enough data to display trends.")

# -----------------------------
# Alerts
# -----------------------------
st.subheader("⚠️ Alert Notifications")
alert_col1, alert_col2, alert_col3 = st.columns(3)

with alert_col1:
    st.info(f"{alert_icon} {alert_msg}")
with alert_col2:
    st.success("✅ Model update completed successfully.")
with alert_col3:
    st.warning("⚠️ Forecast is simulated data.")
