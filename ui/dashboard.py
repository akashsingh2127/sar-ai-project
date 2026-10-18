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
from data.ingestion.dataset_registry import DATASET_REGISTRY, DEFAULT_DATASET
from data.ingestion.huggingface_loader import load_and_validate_dataset

st.set_page_config(page_title="SAR-AI | AML Dashboard", page_icon="🛡️", layout="wide")

st.title("🛡️ SAR-AI: AML Investigation Dashboard")
st.markdown("### Operational Overview")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "suspicious_df" not in st.session_state:
    st.session_state.suspicious_df = None
if "source_metadata" not in st.session_state:
    st.session_state.source_metadata = None

@st.cache_data(show_spinner=False)
def load_hf_cached(registry_name: str, max_records: int) -> pd.DataFrame:
    """Cached wrapper to prevent re-downloading Hugging Face datasets on Streamlit reruns."""
    return load_and_validate_dataset(registry_name=registry_name, max_records=max_records)

# Sidebar Ingestion
st.sidebar.header("📁 Ingestion")
source_choice = st.sidebar.radio(
    "Data Source",
    options=["Local CSV", "Hugging Face"],
    index=0,
    help="Select local CSV upload or live streaming from Hugging Face."
)

if source_choice == "Local CSV":
    uploaded_file = st.sidebar.file_uploader("Upload Transaction Dataset", type="csv")
    sample_btn = st.sidebar.button("📄 Load Sample CSV (Offline Demo)")
    
    if uploaded_file and (st.session_state.df is None or st.sidebar.button("Reload Uploaded Data")):
        with st.spinner("Loading and mapping uploaded CSV..."):
            try:
                raw_df = pd.read_csv(uploaded_file)
                cols = identify_columns(raw_df)
                amount_col = cols.get('amount')
                df = safe_numeric_conversion(raw_df.copy(), amount_col) if amount_col else raw_df.copy()
                
                st.session_state.df = df
                st.session_state.cols = cols
                st.session_state.suspicious_df = None
                st.session_state.source_metadata = {
                    "type": "Local CSV",
                    "name": uploaded_file.name,
                    "records": len(df)
                }
                st.sidebar.success(f"Loaded {len(df)} records from uploaded file.")
            except Exception as e:
                st.sidebar.error(f"Error loading CSV: {e}")
                
    elif sample_btn:
        sample_path = os.path.join("data", "sample_transactions.csv")
        if os.path.exists(sample_path):
            with st.spinner("Loading sample offline dataset..."):
                try:
                    raw_df = pd.read_csv(sample_path)
                    cols = identify_columns(raw_df)
                    amount_col = cols.get('amount')
                    df = safe_numeric_conversion(raw_df.copy(), amount_col) if amount_col else raw_df.copy()
                    
                    st.session_state.df = df
                    st.session_state.cols = cols
                    st.session_state.suspicious_df = None
                    st.session_state.source_metadata = {
                        "type": "Local CSV (Sample)",
                        "name": "sample_transactions.csv",
                        "records": len(df)
                    }
                    st.sidebar.success(f"Loaded {len(df)} records from sample CSV.")
                except Exception as e:
                    st.sidebar.error(f"Error loading sample CSV: {e}")
        else:
            st.sidebar.error(f"Sample file not found at {sample_path}")

elif source_choice == "Hugging Face":
    available_datasets = list(DATASET_REGISTRY.keys())
    selected_ds = st.sidebar.selectbox("Registered Dataset", available_datasets, index=0)
    dataset_info = DATASET_REGISTRY[selected_ds]
    st.sidebar.caption(f"Hub Path: `{dataset_info['path']}` (streaming)")
    
    max_records = st.sidebar.number_input(
        "Max Records to Stream",
        min_value=50,
        max_value=10000,
        value=1000,
        step=100,
        help="Specifies sample size for the streaming iterator."
    )
    
    if st.sidebar.button("🚀 Load Hugging Face Dataset"):
        with st.spinner(f"Streaming {max_records} records from Hugging Face ({selected_ds})..."):
            try:
                hf_df = load_hf_cached(selected_ds, int(max_records))
                cols = identify_columns(hf_df)
                amount_col = cols.get('amount')
                df = safe_numeric_conversion(hf_df.copy(), amount_col) if amount_col else hf_df.copy()
                
                st.session_state.df = df
                st.session_state.cols = cols
                st.session_state.suspicious_df = None
                st.session_state.source_metadata = {
                    "type": "Hugging Face",
                    "registry_name": selected_ds,
                    "dataset_path": dataset_info['path'],
                    "records": len(df)
                }
                st.sidebar.success(f"Loaded and normalized {len(df)} records from Hugging Face!")
            except Exception as e:
                st.sidebar.error(f"Failed to load Hugging Face dataset: {e}")
                st.sidebar.info("Tip: You can switch to 'Local CSV' to continue working offline.")

df = st.session_state.df

if df is not None:
    # Display Source Metadata Banner
    if st.session_state.source_metadata:
        meta = st.session_state.source_metadata
        if meta["type"] == "Hugging Face":
            st.info(f"🌐 **Active Source:** Hugging Face — `{meta['dataset_path']}` ({meta['records']:,} records streamed & validated)")
        else:
            st.info(f"📁 **Active Source:** {meta['type']} — `{meta['name']}` ({meta['records']:,} records loaded)")
            
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
    
    # Optional visualization if amount is available
    if 'cols' in st.session_state and st.session_state.cols.get('amount'):
        amount_col = st.session_state.cols['amount']
        st.subheader("Transaction Amount Distribution")
        fig = px.histogram(df, x=amount_col, nbins=50, title=f"Amount Distribution ({amount_col})", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Please upload a transaction CSV file or select a Hugging Face dataset from the sidebar to begin.")