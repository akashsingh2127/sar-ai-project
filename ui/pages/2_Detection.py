import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# Path fix for local imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from detection.detector_pipeline import DetectorPipeline
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector

st.set_page_config(page_title="Detection", page_icon="🔍", layout="wide")
st.title("🔍 Suspicious Activity Detection")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("⚠️ No dataset loaded. Please go to the Home dashboard to upload a file.")
    st.stop()

df = st.session_state.df
cols = st.session_state.get('cols', {})
amount_col = cols.get('amount')

st.markdown("### Detection Configuration")

col1, col2 = st.columns(2)
with col1:
    use_zscore = st.checkbox("Enable Z-Score Detection", value=True)
    z_threshold = st.slider("Z-Score Threshold", 1.0, 10.0, 3.0, disabled=not use_zscore)

with col2:
    use_if = st.checkbox("Enable Isolation Forest", value=True)
    contamination = st.slider("IF Contamination", 0.01, 0.1, 0.05, disabled=not use_if)

if st.button("🚀 Run Anomaly Detection"):
    with st.spinner("Running detection algorithms..."):
        detectors = []
        if use_zscore:
            detectors.append(ZScoreDetector(threshold=z_threshold))
        if use_if:
            detectors.append(IsolationForestDetector(contamination=contamination))
            
        if not detectors:
            st.error("Please select at least one detector.")
            st.stop()
            
        pipeline = DetectorPipeline(detectors=detectors)
        pipeline.fit(df)
        
        # DetectorPipeline expects 'transaction_id' usually, but safe_numeric_conversion and schema map handles some.
        # Let's run prediction
        anomalies_df = pipeline.predict(df)
        
        if anomalies_df.empty:
            st.success("No anomalies detected.")
            st.session_state.suspicious_df = pd.DataFrame()
        else:
            suspicious_txns_ids = anomalies_df[anomalies_df['is_anomaly'] == True]['transaction_id'].unique()
            df["is_suspicious"] = df[cols.get("transaction_id", "transaction_id")].isin(suspicious_txns_ids)
            suspicious_df = df[df["is_suspicious"]]
            st.session_state.suspicious_df = suspicious_df
            
            st.success(f"Detected {len(suspicious_df)} suspicious transactions.")
            
            # Anomaly Scatter Plot
            if amount_col:
                st.subheader("Anomaly Visualization")
                fig = px.scatter(df, x=df.index, y=amount_col, color="is_suspicious",
                                 color_discrete_map={True: "#FF4B4B", False: "#0068C9"},
                                 title="Transaction Scatter (Anomalies in Red)",
                                 template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(suspicious_df, use_container_width=True)
