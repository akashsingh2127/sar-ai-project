import sys
import os
import streamlit as st
import pandas as pd

# Path fix for local imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from storage import get_storage

st.set_page_config(page_title="Audit Trail", page_icon="🧾", layout="wide")
st.title("🧾 Historical Audit Trail")
st.markdown("Displays all agent executions, reviews, and SAR reports stored in persistent storage.")

try:
    storage = get_storage()
    
    st.subheader("Audit Logs")
    audit_history = storage.get_audit_history()
    
    if audit_history:
        audit_df = pd.DataFrame(audit_history)
        st.dataframe(audit_df, use_container_width=True)
    else:
        st.info("No audit logs found in the database.")
        
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Stored Investigations")
        try:
            # Depending on if the storage interface implements get_all_investigations
            # If not, we might need a raw query or similar, or just show SARs.
            if hasattr(storage, 'get_investigation'):
                # Quick workaround to grab recent logs with INVESTIGATION type
                inv_logs = [log for log in audit_history if log.get('entity_type') == 'INVESTIGATION']
                if inv_logs:
                    inv_df = pd.DataFrame(inv_logs)
                    st.dataframe(inv_df[['entity_id', 'action', 'status', 'timestamp']], use_container_width=True)
                else:
                    st.info("No investigations found.")
            else:
                st.info("Storage layer does not expose get_all_investigations yet.")
        except Exception as e:
            st.error(f"Could not load investigations: {e}")
            
    with col2:
        st.subheader("Stored SAR Reports")
        try:
            sars = storage.get_all_sars()
            if sars:
                sar_records = []
                for s in sars:
                    sar_records.append({
                        "SAR ID": s.get('sar_id'),
                        "Investigation ID": s.get('investigation_id'),
                        "Timestamp": s.get('created_at')
                    })
                sar_df = pd.DataFrame(sar_records)
                st.dataframe(sar_df, use_container_width=True)
            else:
                st.info("No SAR reports found.")
        except Exception as e:
            st.error(f"Could not load SARs: {e}")

except Exception as e:
    st.error(f"Failed to connect to storage: {e}")
