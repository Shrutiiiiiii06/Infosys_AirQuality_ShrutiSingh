import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# -------------------------------
# Utility functions
# -------------------------------
def get_forecast(df, city, pollutant):
    city_df = df[df['City'] == city].sort_values('Date')
    if city_df.empty:
        return pd.DataFrame(), None

    recent = city_df.tail(24)
    forecast_values = np.linspace(
        recent[pollutant].iloc[-1] if not recent.empty else 0,
        (recent[pollutant].iloc[-1] if not recent.empty else 0) * 1.05,
        7
    )
    forecast_dates = [city_df['Date'].max() + timedelta(days=i) for i in range(1, 8)]
    forecast_df = pd.DataFrame({'Date': forecast_dates, pollutant: forecast_values})
    return forecast_df, city_df


def generate_alert(aqi_value):
    if aqi_value <= 50:
        return "Good air quality today", "success"
    elif aqi_value <= 100:
        return "Moderate air quality expected", "warning"
    elif aqi_value <= 150:
        return "Unhealthy for sensitive groups", "warning"
    else:
        return "Hazardous air quality!", "error"


# -------------------------------
# Main Function
# -------------------------------
def run(df):
    st.set_page_config(page_title="AirAware Dashboard", layout="wide")

    # --- Ensure Date/Time Column Exists ---
    time_col = None
    for col in ['Date', 'Datetime', 'Time', 'Timestamp']:
        if col in df.columns:
            time_col = col
            break

    if not time_col:
        st.error("❌ No Date/Time column found in the dataset.")
        return

    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    df.rename(columns={time_col: 'Date'}, inplace=True)

    # -------------------------------
    # Page Title
    # -------------------------------
    st.markdown(
        "<h2 style='text-align:center; color:#4C52AD;'>Streamlit Web Dashboard</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h5 style='text-align:center; color:gray;'>Milestone 4: Working Application (Weeks 7–8)</h5>",
        unsafe_allow_html=True,
    )

    # -------------------------------
    # Sidebar Controls
    # -------------------------------
    st.sidebar.header("⚙️ Controls")
    city = st.sidebar.selectbox("Monitoring Station", sorted(df["City"].unique()))
    time_range = st.sidebar.selectbox("Time Range", ["All Data", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
    pollutant = st.sidebar.selectbox("Pollutant", ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO", "AQI"])
    horizon = st.sidebar.selectbox("Forecast Horizon", ["24 Hours", "7 Days"])
    admin_mode = st.sidebar.toggle("Admin Mode")

    update_clicked = st.sidebar.button("🔄 Update Dashboard")

    if not update_clicked:
        st.stop()

    # -------------------------------
    # Data Filtering
    # -------------------------------
    city_df = df[df["City"] == city].sort_values("Date")

    # Dynamic date filtering
    if time_range == "Last 24 Hours":
        recent_cutoff = df['Date'].max() - timedelta(hours=24)
        city_df = city_df[city_df["Date"] >= recent_cutoff]
    elif time_range == "Last 7 Days":
        recent_cutoff = df['Date'].max() - timedelta(days=7)
        city_df = city_df[city_df["Date"] >= recent_cutoff]
    elif time_range == "Last 30 Days":
        recent_cutoff = df['Date'].max() - timedelta(days=30)
        city_df = city_df[city_df["Date"] >= recent_cutoff]

    # Fallback: ensure we always have some data
    if city_df.empty:
        city_df = df[df["City"] == city].tail(50)

    forecast_df, city_df = get_forecast(df, city, pollutant)

    # -------------------------------
    # Current AQI Donut
    # -------------------------------
    aqi_value = int(city_df["AQI"].iloc[-1]) if "AQI" in city_df else 0
    label, alert_type = generate_alert(aqi_value)

    # Define AQI zones
    zones = [
        ("Good", 50, "#00E400"),
        ("Moderate", 100, "#FFFF00"),
        ("Unhealthy SG", 150, "#FF7E00"),
        ("Unhealthy", 200, "#FF0000"),
        ("Very Unhealthy", 300, "#8F3F97"),
        ("Hazardous", 500, "#7E0023"),
    ]

    # Create donut chart
    labels = [z[0] for z in zones]
    values = [z[1] - (zones[i - 1][1] if i > 0 else 0) for i, z in enumerate(zones)]
    colors = [z[2] for z in zones]

    fig_donut = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.7,
            marker=dict(colors=colors),
            textinfo='none'
        )
    ])

    # Add AQI value in the center
    fig_donut.add_annotation(
        x=0.5, y=0.5,
        text=f"<b>{aqi_value}</b><br>{label}",
        showarrow=False,
        font=dict(size=16)
    )
    fig_donut.update_layout(
        title_text="Current Air Quality Index (AQI)",
        showlegend=True,
        height=300,
        margin=dict(t=40, b=40, l=40, r=40)
    )
    # -------------------------------
    # Forecast Chart
    # -------------------------------
    fig_forecast = go.Figure()
    fig_forecast.add_trace(go.Scatter(
        x=city_df["Date"],
        y=city_df[pollutant],
        mode="lines+markers",
        name="Historical",
        line=dict(color="#4C52AD"),
    ))
    if not forecast_df.empty:
        fig_forecast.add_trace(go.Scatter(
            x=forecast_df["Date"],
            y=forecast_df[pollutant],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#FF7043", dash="dash")
        ))
    fig_forecast.update_layout(
        title=f"{pollutant} Forecast ({horizon})",
        xaxis_title="Date",
        yaxis_title=f"{pollutant} (µg/m³)",
        height=300,
    )

    # -------------------------------
    # Weekly Pollutant Trends
    # -------------------------------
    pollutants = [p for p in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"] if p in df.columns]
    fig_trend = go.Figure()
    for pol in pollutants:
        fig_trend.add_trace(go.Scatter(
            x=city_df["Date"],
            y=city_df[pol],
            mode="lines+markers",
            name=pol,
            fill='tonexty'
        ))
    fig_trend.update_layout(
        title="Weekly Pollutant Trends",
        xaxis_title="Date",
        yaxis_title="Concentration (µg/m³)",
        height=300,
    )

    # -------------------------------
    # Alerts Section
    # -------------------------------
    st.markdown("### 🚨 Alert Notifications")
    st.info(f"{label} — based on current readings from {city}")

    # -------------------------------
    # Layout Columns
    # -------------------------------
    col1, col2, col3 = st.columns([1, 1, 1.2])
    with col1:
        st.plotly_chart(fig_donut, use_container_width=True)
    with col2:
        st.plotly_chart(fig_forecast, use_container_width=True)
    with col3:
        st.plotly_chart(fig_trend, use_container_width=True)

    # -------------------------------
    # Admin Mode
    # -------------------------------
    if admin_mode:
        st.sidebar.markdown("---")
        st.sidebar.subheader("👩‍💻 Admin Panel")
        st.sidebar.text("View and manage AQI data.")
        st.dataframe(city_df.tail(20))




