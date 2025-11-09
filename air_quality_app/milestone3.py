import streamlit as st
import plotly.graph_objects as go
import random
import pandas as pd

def run(df):
    # ---------------- Header ----------------
    st.markdown("""
    <div style="background-color:#FFF3E0;padding:20px;border-radius:10px;margin-bottom:10px;">
        <h2 style="color:#D84315;">Air Quality Alert System</h2>
        <h4 style="color:#BF360C;">Milestone 3: Working Application (Weeks 5–6)</h4>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- Station Selection ----------------
    st.markdown("### 🏙️ Select Monitoring Station")

    if 'Station' in df.columns:
        station_list = sorted(df['Station'].dropna().unique())
    elif 'City' in df.columns:
        station_list = sorted(df['City'].dropna().unique())
    else:
        station_list = ["Downtown", "Industrial", "Suburban", "Uptown"]

    selected_station = st.selectbox("Choose a monitoring station:", station_list)
    st.markdown(f"#### 📍 Current Station: **{selected_station}**")

    # ---------------- Layout ----------------
    left_col, right_col = st.columns([1.2, 1])

    # ---------------- Current Air Quality (Donut) ----------------
    with left_col:
        st.markdown("### 🌫️ Current Air Quality")
        latest_aqi = random.randint(30, 200)
        status = (
            "Good" if latest_aqi <= 50 else
            "Moderate" if latest_aqi <= 100 else
            "Unhealthy for Sensitive" if latest_aqi <= 150 else
            "Unhealthy"
        )
        color_map = {
            "Good": "#4CAF50",
            "Moderate": "#FFC107",
            "Unhealthy for Sensitive": "#FF9800",
            "Unhealthy": "#F44336"
        }

        # Donut Chart (AQI)
        fig_aqi = go.Figure()

        # Background ring
        fig_aqi.add_trace(go.Pie(
            values=[1],
            hole=0.8,
            marker_colors=["#E0E0E0"],
            textinfo="none"
        ))

        # Foreground AQI ring
        fig_aqi.add_trace(go.Pie(
            values=[1],
            hole=0.8,
            marker_colors=[color_map[status]],
            textinfo="none"
        ))

        fig_aqi.update_layout(
            annotations=[{
                'text': f"<b>{latest_aqi}</b><br><span style='font-size:16px'>{status}</span>",
                'x': 0.5, 'y': 0.5, 'showarrow': False
            }],
            showlegend=False,
            margin=dict(t=0, b=0, l=0, r=0),
            height=280
        )
        st.plotly_chart(fig_aqi, use_container_width=True)

    # ---------------- 7-Day Forecast ----------------
    with right_col:
        st.markdown("### 📅 7-Day Forecast")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        aqis = [random.randint(40, 150) for _ in range(7)]
        statuses = ["Good" if a <= 50 else "Moderate" if a <= 100 else "Unhealthy for Sensitive" for a in aqis]
        colors = ["#4CAF50" if s == "Good" else "#FFC107" if s == "Moderate" else "#FF9800" for s in statuses]

        for i in range(7):
            st.markdown(f"""
            <div style='display:inline-block;background-color:{colors[i]};padding:10px 20px;
                        border-radius:10px;margin:5px;text-align:center;color:white;'>
                <b>{days[i]}</b><br><span style='font-size:14px;'>AQI {aqis[i]}</span><br>
                <span style='font-size:12px;'>{statuses[i]}</span>
            </div>
            """, unsafe_allow_html=True)

    # ---------------- Pollutant Concentrations ----------------
    st.markdown("### 💨 Pollutant Concentrations")

    times = [f"{h:02d}:00" for h in range(0, 25, 4)]
    pollutants = ["AQI", "PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]

    color_map = {
        "AQI": "rgba(142, 36, 170, 1)",
        "PM2.5": "rgba(229, 57, 53, 1)",
        "PM10": "rgba(67, 160, 71, 1)",
        "O3": "rgba(30, 136, 229, 1)",
        "NO2": "rgba(251, 140, 0, 1)",
        "SO2": "rgba(109, 76, 65, 1)",
        "CO": "rgba(0, 172, 193, 1)"
    }

    fill_opacity = {
        "AQI": "rgba(142, 36, 170, 0.2)",
        "PM2.5": "rgba(229, 57, 53, 0.2)",
        "PM10": "rgba(67, 160, 71, 0.2)",
        "O3": "rgba(30, 136, 229, 0.2)",
        "NO2": "rgba(251, 140, 0, 0.2)",
        "SO2": "rgba(109, 76, 65, 0.2)",
        "CO": "rgba(0, 172, 193, 0.2)"
    }

    fig_pollutants = go.Figure()

    for p in pollutants:
        values = [random.uniform(20, 70) for _ in times]
        fig_pollutants.add_trace(go.Scatter(
            x=times,
            y=values,
            mode="lines+markers",
            name=p,
            line=dict(color=color_map[p], width=3),
            fill='tozeroy',
            fillcolor=fill_opacity[p]
        ))

    fig_pollutants.update_layout(
        yaxis_title="Concentration (µg/m³)",
        xaxis_title="Time of Day",
        plot_bgcolor="white",
        height=320,
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig_pollutants, use_container_width=True)

    # ---------------- Active Alerts ----------------
        # ---------------- Active Alerts ----------------
    st.markdown("### 🚨 Air Quality Alert")

    # Filter data for the selected station (use the same dropdown from top)
    if 'City' in df.columns:
        city_df = df[df['City'] == selected_station].copy()
    elif 'Station' in df.columns:
        city_df = df[df['Station'] == selected_station].copy()
    else:
        city_df = pd.DataFrame()  # fallback

    # Ensure pollutant columns exist
    pollutant_cols = ['AQI', 'PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO']
    for col in pollutant_cols:
        if col in city_df.columns:
            city_df[col] = pd.to_numeric(city_df[col], errors='coerce')

    # Generate Alert
    if city_df.empty:
        st.warning(f"No data available for **{selected_station}**.")
    else:
        latest_row = city_df.iloc[-1]
        latest_aqi = latest_row['AQI'] if 'AQI' in latest_row else None

        if pd.isna(latest_aqi):
            st.info(f"No AQI data available for **{selected_station}**.")
        else:
            if latest_aqi <= 50:
                alert = f"🟢 **Good Air Quality** in **{selected_station}** — Air is clean and healthy."
            elif latest_aqi <= 100:
                alert = f"🟡 **Moderate Air Quality** in **{selected_station}** — Acceptable but some pollutants may affect sensitive groups."
            elif latest_aqi <= 150:
                alert = f"🟠 **Unhealthy for Sensitive Groups** in **{selected_station}** — People with asthma or heart disease should reduce outdoor exertion."
            elif latest_aqi <= 200:
                alert = f"🔴 **Unhealthy Air Quality** in **{selected_station}** — Everyone may start experiencing health effects."
            elif latest_aqi <= 300:
                alert = f"🟣 **Very Unhealthy Air Quality** in **{selected_station}** — Health warnings of emergency conditions."
            else:
                alert = f"⚫ **Hazardous Air Quality** in **{selected_station}** — Serious health effects, avoid all outdoor activities."

            st.markdown(alert)
