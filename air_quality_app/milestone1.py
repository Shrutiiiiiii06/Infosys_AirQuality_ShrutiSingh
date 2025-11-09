import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def run(df):
    # ---------------------- STYLES ----------------------
    st.markdown("""
    <style>
    h2, h3 {
        color: #4B0082;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## 📘 Milestone 1: Data Overview & Correlation")

    # ---------------------- CITY / LOCATION SELECTION ----------------------
    location_cols = [col for col in df.columns if col.lower() in ["city", "location", "station", "area", "site"]]
    if location_cols:
        location_col = location_cols[0]
        cities = df[location_col].dropna().unique().tolist()
        selected_city = st.sidebar.selectbox("🌆 Select Location", cities)
        city_df = df[df[location_col] == selected_city]
    else:
        st.warning("No location column found; showing full dataset.")
        city_df = df.copy()

    # ---------------------- POLLUTANT SELECTION ----------------------
    pollutant_cols = [col for col in df.columns if any(p in col.upper() for p in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO", "AQI"])]
    selected_pollutant = st.sidebar.radio("Select Pollutant", pollutant_cols if pollutant_cols else ["PM2.5"])

    st.markdown(f"### 🌫️ {selected_pollutant} Time Series - {selected_city if location_cols else 'All Locations'}")

    # ---------------------- TIME PARSING ----------------------
    time_col = None
    for col in df.columns:
        if any(t in col.lower() for t in ["date", "time", "timestamp"]):
            time_col = col
            break

    if time_col:
        city_df[time_col] = pd.to_datetime(city_df[time_col], errors="coerce")
        city_df = city_df.dropna(subset=[time_col])
        city_df = city_df.sort_values(by=time_col)
    else:
        st.error("No time/date column found. Please ensure your dataset includes a time or date column.")
        return

    # ---------------------- CHARTS ----------------------
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = px.line(city_df, x=time_col, y=selected_pollutant, title=f"{selected_pollutant} Concentration Over Time",
                      markers=True, color_discrete_sequence=["#6a11cb"])
        fig.update_layout(
            template="simple_white",
            title_x=0.3,
            xaxis_title="Time",
            yaxis_title=f"{selected_pollutant} (µg/m³)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🧮 Statistical Summary")
        # Coerce selected pollutant to numeric for safety
        city_df[selected_pollutant] = pd.to_numeric(city_df[selected_pollutant], errors="coerce")
        pollutant_data = city_df[selected_pollutant].dropna()
        stats = {
            "Mean (µg/m³)": pollutant_data.mean(),
            "Median (µg/m³)": pollutant_data.median(),
            "Max (µg/m³)": pollutant_data.max(),
            "Min (µg/m³)": pollutant_data.min(),
            "Std Dev": pollutant_data.std(),
            "Data Points": pollutant_data.count()
        }
        stats_df = pd.DataFrame(list(stats.items()), columns=["Metric", "Value"])
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    # ---------------------- POLLUTANT CORRELATIONS ----------------------
    st.markdown("### 🔗 Pollutant Correlations")

    if len(pollutant_cols) > 1:
        # Convert all pollutant columns to numeric safely
        corr_data = city_df[pollutant_cols].apply(pd.to_numeric, errors='coerce')
        corr_df = corr_data.corr().round(2)

        fig_corr = px.imshow(
            corr_df,
            text_auto=True,
            color_continuous_scale="Purples",
            title="Pollutant Correlation Heatmap"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.info("Not enough pollutant columns to compute correlations.")

    # ---------------------- DISTRIBUTION ANALYSIS ----------------------
    st.markdown("### 📊 Distribution Analysis")

    fig_dist = px.histogram(city_df, x=selected_pollutant, nbins=20,
                            title=f"{selected_pollutant} Distribution",
                            color_discrete_sequence=["#6a11cb"])
    fig_dist.update_layout(template="simple_white", title_x=0.3)
    st.plotly_chart(fig_dist, use_container_width=True)

    # ---------------------- DATA QUALITY METRICS ----------------------
    st.markdown("### ✅ Data Quality")
    total = len(df)
    valid = city_df[selected_pollutant].count()
    completeness = (valid / total) * 100
    st.progress(completeness / 100)
    st.write(f"**Data Completeness:** {completeness:.2f}%")

    st.success("Milestone 1 Dashboard Rendered Successfully 💜")
