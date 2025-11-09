import streamlit as st
import pandas as pd

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Forecasting Air Quality Using Historical Pollution Data", layout="wide", page_icon="🌫️")

# ---------------------- THEME TOGGLE ----------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"  # default

theme = st.sidebar.radio(
    "🌓 Theme",
    ["Light", "Dark"],
    index=0 if st.session_state["theme"] == "light" else 1
)
st.session_state["theme"] = theme.lower()  # persist across pages

# ---------------------- APPLY THEME CSS ----------------------
def apply_theme(theme):
    if theme == "light":
        return """
        <style>
        body, .block-container { background-color: #f8f9fd !important; color: #111 !important; }
        h1, h2, h3, h4 { color: #4B0082 !important; }
        div.stText { color: #111 !important; }
        div.stMarkdown { color: #111 !important; }
        .stMetricValue, .stMetricDelta { color: #111 !important; }
        .stButton>button {
            background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
            color: white; border-radius: 12px;
            font-size: 17px; padding: 0.6em 1.4em; font-weight: 600; border: none;
        }
        .stButton>button:hover { background: linear-gradient(90deg, #2575fc 0%, #6a11cb 100%); }
        .card { padding: 1.8rem; background: white; border-radius: 18px; box-shadow: 0px 4px 12px rgba(0,0,0,0.1); text-align: center; transition: 0.3s ease; }
        .card:hover { transform: scale(1.03); }
        </style>
        """
    else:
        return """
        <style>
        body, .block-container { background-color: #0e1117 !important; color: #fafafa !important; }
        h1, h2, h3, h4 { color: #a78bfa !important; }
        div.stText { color: #fafafa !important; }
        div.stMarkdown { color: #fafafa !important; }
        .stMetricValue, .stMetricDelta { color: #fafafa !important; }
        .stButton>button {
            background: linear-gradient(90deg, #9333ea 0%, #3b82f6 100%);
            color: white; border-radius: 12px;
            font-size: 17px; padding: 0.6em 1.4em; font-weight: 600; border: none;
        }
        .stButton>button:hover { background: linear-gradient(90deg, #3b82f6 0%, #9333ea 100%); }
        .card { padding: 1.8rem; background: #1e1e2f; border-radius: 18px; box-shadow: 0px 4px 18px rgba(0,0,0,0.5); text-align: center; transition: 0.3s ease; }
        .card:hover { transform: scale(1.03); }
        </style>
        """

st.markdown(apply_theme(st.session_state["theme"]), unsafe_allow_html=True)

# ---------------------- HELPER FUNCTIONS ----------------------
def themed_dataframe(df):
    """Display dataframe with text visible in current theme"""
    if st.session_state["theme"] == "dark":
        return st.dataframe(df.style.set_properties(**{'color': 'white','background-color': '#1e1e2f'}))
    else:
        return st.dataframe(df)

# ---------------------- SIDEBAR ----------------------
st.sidebar.header("📂 Dataset Controls")
uploaded_file = st.sidebar.file_uploader("Upload Air Quality Dataset", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.session_state["df"] = df
    st.sidebar.success("✅ Dataset uploaded successfully.")
else:
    st.sidebar.info("Upload a CSV file to continue.")

# ---------------------- MAIN HEADER ----------------------
st.markdown("<h1 style='text-align:center;'>🌫️ AirAware Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:gray;'>Air Quality Forecasting & Analysis</h4>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------- DATA SUMMARY ----------------------
if "df" in st.session_state:
    df = st.session_state["df"]
    cols = st.columns(3)
    with cols[0]:
        st.metric("📊 Total Records", f"{len(df):,}")
    with cols[1]:
        st.metric("🏙️ Monitoring Stations", df['City'].nunique() if 'City' in df else 'N/A')
    with cols[2]:
        pollutants = [p for p in ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO", "AQI"] if p in df.columns]
        st.metric("🧪 Pollutants Tracked", len(pollutants))
    st.markdown("<hr>", unsafe_allow_html=True)

# ---------------------- MILESTONE GRID ----------------------
st.markdown("### 📘 Project Milestones Overview")
col1, col2, col3, col4 = st.columns(4)

milestones = [
    ("Dashboard 1", "Data Preprocessing & EDA", "Handle missing values, resample data, and visualize pollutant trends.", "milestone1"),
    ("Dashboard 2", "Model Training & Evaluation", "Train ARIMA, Prophet, and LSTM models and evaluate with RMSE/MAE.", "milestone2"),
    ("Dashboard 3", "AQI Alert System", "Generate dynamic alerts, visualize daily AQI trends, and highlight risks.", "milestone3"),
    ("Dashboard 4", "Streamlit Dashboard", "Full dashboard with station selection, forecasts, and admin tools.", "milestone4")
]

for col, (title, subtitle, desc, page_name) in zip([col1, col2, col3, col4], milestones):
    with col:
        st.markdown(f"""
        <div class='card'>
        <h3>{title}</h3>
        <p><b>{subtitle}</b></p>
        <p style='font-size:13px; color:gray;'>{desc}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🚀 Launch {title}", key=page_name, use_container_width=True):
            st.session_state["page"] = page_name

st.markdown("<br><hr>", unsafe_allow_html=True)

# ---------------------- MODEL SECTION ----------------------
st.markdown("### 🧠 Model Overview & Capabilities")
model_cols = st.columns(4)  # Changed to 4 columns to fit XGBoost

models = [
    ("ARIMA", "Autoregressive Integrated Moving Average", "Captures temporal dependencies for linear pollutant trends.", "📈 Best for short-term forecasts with regular intervals."),
    ("Prophet", "Facebook Prophet Model", "Handles daily, weekly, and yearly seasonality effectively.", "🕒 Ideal for longer-term trend forecasting."),
    ("LSTM", "Long Short-Term Memory Networks", "Captures complex, non-linear temporal patterns in pollutant sequences.", "🤖 Suited for adaptive real-time AQI predictions."),
    ("XGBoost", "Extreme Gradient Boosting", "Powerful ensemble model for regression & classification tasks.", "⚡ Can capture complex patterns and interactions in pollutant data.")
]

for col, (name, subtitle, desc, extra) in zip(model_cols, models):
    with col:
        st.markdown(f"""
        <div class='card'>
        <h3>{name}</h3>
        <p><b>{subtitle}</b></p>
        <p style='font-size:13px; color:gray;'>{desc}</p>
        <p>{extra}</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------- PAGE ROUTING ----------------------
if "page" in st.session_state and "df" in st.session_state:
    df = st.session_state["df"]
    page = st.session_state["page"]
    if page == "milestone1":
        import milestone1; milestone1.run(df)
    elif page == "milestone2":
        import milestone2; milestone2.run(df)
    elif page == "milestone3":
        import milestone3; milestone3.run(df)
    elif page == "milestone4":
        import milestone4; milestone4.run(df)
elif "page" in st.session_state:
    st.warning("⚠️ Please upload a dataset before proceeding.")

# ---------------------- FOOTER ----------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align:center; color:gray; font-size:14px;'>
AirAware © 2025 | Developed by <b>Shruti Singh</b> 🌸<br>
Empowering cleaner cities with AI-driven insights.
</div>
""", unsafe_allow_html=True)
