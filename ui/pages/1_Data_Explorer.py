import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Explorer", page_icon="📊", layout="wide")
st.title("📊 Data Explorer")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("⚠️ No dataset loaded. Please go to the Home dashboard to upload a file.")
    st.stop()

df = st.session_state.df
cols = st.session_state.get('cols', {})

st.markdown("### Transaction View")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    customer_id_col = cols.get('customer_id')
    if customer_id_col and customer_id_col in df.columns:
        customers = ["All"] + list(df[customer_id_col].dropna().unique())
        selected_cust = st.selectbox("Customer Filter", customers)
    else:
        selected_cust = "All"
        
with col2:
    amount_col = cols.get('amount')
    if amount_col and amount_col in df.columns:
        min_amt = float(df[amount_col].min())
        max_amt = float(df[amount_col].max())
        amt_range = st.slider("Amount Filter", min_value=min_amt, max_value=max_amt, value=(min_amt, max_amt))
    else:
        amt_range = None
        
with col3:
    if "is_suspicious" in df.columns:
        suspicious_only = st.checkbox("Show only Suspicious Transactions", value=False)
    else:
        suspicious_only = False

# Apply filters
filtered_df = df.copy()

if selected_cust != "All" and customer_id_col:
    filtered_df = filtered_df[filtered_df[customer_id_col] == selected_cust]

if amt_range and amount_col:
    filtered_df = filtered_df[(filtered_df[amount_col] >= amt_range[0]) & (filtered_df[amount_col] <= amt_range[1])]
    
if suspicious_only and "is_suspicious" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["is_suspicious"] == True]

st.dataframe(filtered_df, use_container_width=True)
st.caption(f"Showing {len(filtered_df)} of {len(df)} transactions.")
