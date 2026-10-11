import sys
import os
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import pandas as pd
import plotly.express as px

# Path fix for local imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from app.schema import identify_columns
from app.utils import safe_numeric_conversion
from storage import get_storage

st.set_page_config(page_title="SAR-AI | AML Dashboard", page_icon="🛡️", layout="wide")

st.title("🛡️ SAR-AI: AML Investigation Dashboard")
st.markdown("### Operational Overview")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "suspicious_df" not in st.session_state:
    st.session_state.suspicious_df = None

# Sidebar Upload
st.sidebar.header("📁 Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Transaction Dataset", type="csv")

if uploaded_file and (st.session_state.df is None or st.sidebar.button("Reload Data")):
    with st.spinner("Loading and mapping dataset..."):
        raw_df = pd.read_csv(uploaded_file)
        cols = identify_columns(raw_df)
        amount_col = cols.get('amount')
        
        if amount_col:
            df = safe_numeric_conversion(raw_df.copy(), amount_col)
        else:
            df = raw_df.copy()
            
        st.session_state.df = df
        st.session_state.cols = cols
        st.success("Dataset loaded successfully.")

df = st.session_state.df

if df is not None:
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_txns = len(df)
    col1.metric("Total Transactions", f"{total_txns:,}")
    
    suspicious_count = len(st.session_state.suspicious_df) if st.session_state.suspicious_df is not None else 0
    col2.metric("Suspicious Transactions", f"{suspicious_count:,}")
    
    # Audit trail stats
    storage = get_storage()
    history = storage.get_audit_history()
    inv_count = len([h for h in history if h.get("entity_type") == "INVESTIGATION"])
    sar_count = len(storage.get_all_sars())
    
    col3.metric("Total Investigations", f"{inv_count:,}")
    col4.metric("SARs Generated", f"{sar_count:,}")
    
    st.divider()
    
    # Optional generic visualization if amount is available
    if 'cols' in st.session_state and st.session_state.cols.get('amount'):
        amount_col = st.session_state.cols['amount']
        st.subheader("Transaction Amount Distribution")
        fig = px.histogram(df, x=amount_col, nbins=50, title="Amount Distribution", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Please upload a transaction CSV file from the sidebar to begin.")