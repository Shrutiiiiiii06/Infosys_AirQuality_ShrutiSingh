import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# --- Flask API Base URL ---
API_BASE = "http://127.0.0.1:5002/api"

WHO_LIMITS = {
    "PM2.5": 25,   # µg/m³ (24-hour mean)
    "PM10": 50,    # µg/m³ (24-hour mean)
    "O3": 100,     # µg/m³ (8-hour mean)
    "NO2": 200,    # µg/m³ (1-hour mean)
    "SO2": 20,     # µg/m³ (24-hour mean)
    "CO": 10       # mg/m³ (8-hour mean)
}


# --- Page Configuration ---
st.set_page_config(page_title="Air Quality Dashboard", layout="wide")
st.title("🌤️ Air Quality Monitoring & Alert System")

# --- Fetch Cities from API ---
try:
    response = requests.get(f"{API_BASE}/cities")
    response.raise_for_status()
    cities = response.json().get("cities", [])
except Exception as e:
    st.error(f"⚠️ Could not load cities from API: {e}")
    cities = []

# --- City Selector ---
selected_city = st.selectbox("🏙️ Select Monitoring Station", cities) if cities else None


# --- AQI Category Helper ---
def classify_aqi(aqi_value):
    if aqi_value <= 50:
        return "Good", "#00e400"
    elif aqi_value <= 100:
        return "Satisfactory", "#ffde33"
    elif aqi_value <= 200:
        return "Moderate", "#ff9933"
    elif aqi_value <= 300:
        return "Poor", "#cc0033"
    elif aqi_value <= 400:
        return "Very Poor", "#660099"
    else:
        return "Severe", "#7e0023"


# --- AQI Donut Chart ---
def plot_aqi_donut(current_aqi):
    category, color = classify_aqi(current_aqi)
    labels = ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe']
    values = [1, 1, 1, 1, 1, 1]
    colors = ['#00e400', '#ffde33', '#ff9933', '#cc0033', '#660099', '#7e0023']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.75,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='none'
    )])

    fig.add_annotation(
        text=(f"<b><span style='font-size:46px; color:{color};'>{int(current_aqi)}</span><br>"
              f"<span style='font-size:18px;'>AQI</span><br>"
              f"<span style='font-size:20px; color:{color};'>{category}</span></b>"),
        x=0.5, y=0.5, showarrow=False
    )

    fig.update_layout(showlegend=False, width=380, height=380, margin=dict(t=10, b=10, l=10, r=10))
    return fig


# --- Dashboard Display ---
if selected_city:
    col1, col2 = st.columns([1, 1.2])

    # --- Left Column: AQI Donut ---
    with col1:
        st.subheader(f"🌍 Current AQI for {selected_city}")
        try:
            aqi_response = requests.get(f"{API_BASE}/current_aqi", params={"city": selected_city})
            aqi_response.raise_for_status()
            try:
                aqi_data = aqi_response.json()
            except Exception:
                aqi_data = {}
            if aqi_data and "AQI" in aqi_data:
                fig = plot_aqi_donut(float(aqi_data["AQI"]))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"**Category:** {aqi_data.get('category', 'Unknown')}")
            else:
                st.warning("⚠️ No AQI data available for this city.")
        except Exception as e:
            st.error(f"⚠️ Failed to fetch AQI: {e}")

    # --- Right Column: 7-Day Forecast ---
    with col2:
        st.subheader("📅 7-Day Forecast (Mon–Sun)")
        try:
            forecast_response = requests.get(f"{API_BASE}/forecast", params={"city": selected_city})
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()

            if forecast_data:
                color_map = {
                    "Good": "#66BB6A",
                    "Moderate": "#FFEB3B",
                    "Unhealthy for Sensitive": "#FFB74D"
                }

                forecast_html = "<div style='display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:10px;'>"
                for item in forecast_data:
                    aqi = item.get("AQI", "--")
                    if aqi == "--":
                        category = "Unknown"
                        color = "#E0E0E0"
                    else:
                        aqi = float(aqi)
                        if aqi <= 50:
                            category = "Good"
                        elif aqi <= 100:
                            category = "Moderate"
                        else:
                            category = "Unhealthy for Sensitive"
                        color = color_map.get(category, "#E0E0E0")

                    forecast_html += f"""
                        <div style='background-color:{color};
                                    padding:16px;border-radius:12px;text-align:center;
                                    width:90px;box-shadow:0 2px 5px rgba(0,0,0,0.1);'>
                            <b>{item['day']}</b><br>
                            <span style='font-size:16px;'>AQI {aqi}</span>
                        </div>"""

                forecast_html += "</div>"

                # Add legend
                forecast_html += """
                    <div style='display:flex;justify-content:center;margin-top:10px;gap:20px;'>
                        <span style='color:#66BB6A;'><b>■ Good</b></span>
                        <span style='color:#FFEB3B;'><b>■ Moderate</b></span>
                        <span style='color:#FFB74D;'><b>■ Unhealthy for Sensitive</b></span>
                    </div>
                """

                st.markdown(forecast_html, unsafe_allow_html=True)

            else:
                st.warning("No forecast data available.")
        except Exception as e:
            st.error(f"Error fetching forecast: {e}")

    # --- Pollutant Concentrations Line Chart ---
    try:
        pollutant_response = requests.get(f"{API_BASE}/pollutant_concentrations", params={"city": selected_city})
        pollutant_response.raise_for_status()
        try:
            pollutant_data = pollutant_response.json()
        except Exception:
            pollutant_data = []

        if pollutant_data:
            df_pollutants = pd.DataFrame(pollutant_data)
            df_pollutants["Time"] = pd.to_datetime(df_pollutants["Time"], errors="coerce")

            pollutants = [col for col in df_pollutants.columns if col not in ["Time", "City", "AQI"]]
            fig_pollutants = go.Figure()

            for pollutant in pollutants:
                fig_pollutants.add_trace(go.Scatter(
                    x=df_pollutants["Time"],
                    y=df_pollutants[pollutant],
                    mode="lines+markers",  # ensure lines connect and points visible
                    name=pollutant,
                    line=dict(width=2),
                    marker=dict(size=7, symbol='circle')
                ))

                # WHO limit line (daily)
                if pollutant in WHO_LIMITS:
                    fig_pollutants.add_hline(
                        y=WHO_LIMITS[pollutant],
                        line=dict(color="red", dash="dot"),
                        annotation_text=f"WHO 24h Limit: {WHO_LIMITS[pollutant]} µg/m³",
                        annotation_position="top right"
                    )

                # Add 1-year average reference line (example: slightly above daily)
                fig_pollutants.add_hline(
                    y=WHO_LIMITS.get(pollutant, 50) * 0.6,  # example: 60% of daily limit
                    line=dict(color="blue", dash="dot"),
                    annotation_text="1-Year Avg Guideline",
                    annotation_position="bottom right"
                )

            fig_pollutants.update_layout(
                title=f"📊 Pollutant Concentrations in {selected_city}",
                xaxis_title="Time",
                yaxis_title="Concentration (µg/m³)",
                legend_title="Pollutants",
                template="plotly_white",
                height=450
            )

            st.plotly_chart(fig_pollutants, use_container_width=True)
        else:
            st.warning("No pollutant data found for this city.")
    except Exception as e:
        st.error(f"Error loading pollutant data: {e}")


    # --- Alerts Section ---
    st.markdown("### ⚠️ Active Alerts")
    try:
        alerts_response = requests.get(f"{API_BASE}/alerts", params={"city": selected_city})
        alerts_response.raise_for_status()
        try:
            alerts = alerts_response.json()
        except Exception:
            alerts = []

        if alerts:
            for alert in alerts:
                color = {
                    "danger": "red",
                    "warning": "orange",
                    "info": "blue",
                    "success": "green"
                }.get(alert.get("type", ""), "gray")

                st.markdown(
                    f"""
                    <div style="background-color:{color}20;
                                padding:10px 15px;
                                border-left: 5px solid {color};
                                border-radius:10px;
                                margin-bottom:8px;">
                        <b>{alert.get('title', 'Alert')}</b><br>
                        <small>{alert.get('description', '')}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ Air quality is stable. No active alerts.")
    except Exception as e:
        st.error(f"Error fetching alert data: {e}")

else:
    st.info("Please select a city to view the dashboard.")
