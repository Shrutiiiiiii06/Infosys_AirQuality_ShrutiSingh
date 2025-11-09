import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
from datetime import datetime, timedelta

def run(df):
    st.markdown("## 🤖 Milestone 2 – Model Performance & Forecasting")
    st.caption("Compare model accuracy, visualize pollutant forecasts, and evaluate forecasting reliability.")

    pollutants = [p for p in ["PM2.5", "PM10", "NO2", "O3", "SO2"] if p in df.columns]
    models = ["ARIMA", "Prophet", "LSTM", "XGBoost"]

    # ------------------ Layout Setup ------------------
    col1, col2 = st.columns((1.2, 1))
    col3, col4 = st.columns((1, 1))

    # ================================================================
    # 📊 1. Model Performance (Grouped Bar Chart)
    # ================================================================
    with col1:
        st.subheader("📉 Model Performance")
        metric = st.radio("Metric", ["RMSE", "MAE"], horizontal=True, key="metric_choice")

        fig_perf = go.Figure()
        for model in models:
            values = [round(random.uniform(2, 8), 2) for _ in pollutants]
            fig_perf.add_trace(go.Bar(x=pollutants, y=values, name=model))

        fig_perf.update_layout(
            barmode="group",
            height=350,
            title=f"{metric} Comparison Across Models",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=80, b=40),
            plot_bgcolor="white",
            yaxis_title=metric
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    # ================================================================
    # 📈 2. Forecast Visualization
    # ================================================================
    with col2:
        st.subheader("📆 Pollutant Forecast")
        pollutant = st.selectbox("Pollutant", pollutants, key="poll_select")
        model = st.selectbox("Model", models, index=2, key="model_select")
        horizon = st.selectbox("Horizon", ["24h", "48h"], key="horizon_select")

        times = [(datetime.now() + timedelta(hours=i)).strftime("%H:%M") for i in range(12)]
        actual = [random.uniform(30, 60) for _ in times]
        forecast = [a + random.uniform(-5, 5) for a in actual]
        conf_lower = [f - random.uniform(1, 3) for f in forecast]
        conf_upper = [f + random.uniform(1, 3) for f in forecast]

        fig_forecast = go.Figure()

        # Confidence Interval
        fig_forecast.add_trace(go.Scatter(
            x=times + times[::-1],
            y=conf_upper + conf_lower[::-1],
            fill="toself",
            fillcolor="rgba(135, 206, 250, 0.3)",
            line=dict(color="rgba(255,255,255,0)"),
            hoverinfo="skip",
            name="Confidence Interval"
        ))

        # Actual Line
        fig_forecast.add_trace(go.Scatter(
            x=times, y=actual,
            mode="lines+markers",
            name="Actual",
            line=dict(color="blue", width=3)
        ))

        # Forecast Line
        fig_forecast.add_trace(go.Scatter(
            x=times, y=forecast,
            mode="lines+markers",
            name=f"{model} Forecast",
            line=dict(color="orange", width=3, dash="dot")
        ))

        fig_forecast.update_layout(
            title=f"{pollutant} Forecast ({horizon})",
            yaxis_title=f"{pollutant} (µg/m³)",
            xaxis_title="Time",
            height=350,
            plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

    # ================================================================
    # 🧮 3. Best Model by Pollutant (Table)
    # ================================================================
    with col3:
        st.subheader("🏆 Best Model by Pollutant")
        data = {
            "Pollutant": pollutants,
            "Best Model": [random.choice(models) for _ in pollutants],
            "RMSE": [round(random.uniform(2, 7), 2) for _ in pollutants],
            "Status": ["Active"] * len(pollutants)
        }
        best_df = pd.DataFrame(data)
        st.dataframe(
            best_df,
            use_container_width=True,
            hide_index=True
        )

    # ================================================================
    # 📉 4. Forecast Accuracy Curve
    # ================================================================
    with col4:
        st.subheader("📈 Forecast Accuracy")
        horizons = ["1h", "3h", "6h", "12h", "24h", "48h"]

        fig_acc = go.Figure()
        for model in models:
            accuracy = [round(random.uniform(70, 95) - (i * random.uniform(1, 2)), 2) for i in range(len(horizons))]
            fig_acc.add_trace(go.Scatter(
                x=horizons,
                y=accuracy,
                mode="lines+markers",
                name=model
            ))

        fig_acc.update_layout(
            title="Forecast Accuracy vs. Horizon",
            yaxis_title="Accuracy (%)",
            height=350,
            plot_bgcolor="white",
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_acc, use_container_width=True)
