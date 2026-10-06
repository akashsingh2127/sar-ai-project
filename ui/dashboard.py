import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- STAGE 0: PATH FIX ---
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Import New Architecture Modules
from app.utils import safe_numeric_conversion
from app.schema import identify_columns
from app.audit import log_audit

from detection.detector_pipeline import DetectorPipeline
from detection.zscore import ZScoreDetector
from detection.isolation_forest import IsolationForestDetector
from risk.scorer import RiskScorer
from analysis.typologies import TypologyEngine
from analysis.network import NetworkAnalyzer
from evidence.engine import EvidenceEngine
from agents.supervisor_agent import SupervisorAgent

# --- UI CONFIG ---
st.set_page_config(page_title="Barclays SAR-AI | Multi-Agent", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #00AEEF !important; }
    .logic-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .agent-title { font-weight: bold; color: #8b949e; margin-bottom: 10px; text-transform: uppercase; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ SAR-AI: Multi-Agent Compliance Suite")

# --- SIDEBAR ---
st.sidebar.header("📁 Step 1: Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Transaction Dataset", type="csv")

if not uploaded_file:
    st.info("💡 Please upload a CSV file to begin analysis.")
    col_img, col_text = st.columns([1, 2.5])
    with col_img:
        icon_path = os.path.join(root_path, "ui", "assets", "security_icon.png")
        if os.path.exists(icon_path):
            st.image(icon_path, width=200)
        else:
            st.markdown("<h1 style='font-size: 150px;'>🛡️</h1>", unsafe_allow_html=True)
    with col_text:
        st.markdown("### AI-Powered Financial Vigilance\nSelect a transaction file to trigger the Agentic Pipeline.")
else:
    try:
        raw_df = pd.read_csv(uploaded_file)
        cols = identify_columns(raw_df)
        amount_col = cols['amount']
        df = safe_numeric_conversion(raw_df.copy(), amount_col)

        # --- DETECTION ---
        st.subheader("🔍 Step 2: Suspicion Detection")
        z_threshold = st.sidebar.slider("Anomaly Sensitivity (Z-Score)", 1.0, 5.0, 2.0)
        
        detector = DetectorPipeline(detectors=[])
        zscore_detector = ZScoreDetector(threshold=z_threshold)
        detector.detectors.append(zscore_detector)
        detector.detectors.append(IsolationForestDetector())
        
        detector.fit(df)
        anomalies_df = detector.predict(df)
        suspicious_txns_ids = anomalies_df[anomalies_df['is_anomaly'] == True]['transaction_id'].unique()
        
        df["is_suspicious"] = df["transaction_id"].isin(suspicious_txns_ids)
        suspicious_df = df[df["is_suspicious"]]

        st.dataframe(suspicious_df, use_container_width=True)

        # --- VISUALIZATION ---
        st.subheader("📊 Step 2.5: Risk Distribution Analysis")
        fig = px.scatter(df, x=df.index, y=amount_col, color="is_suspicious",
                         color_discrete_map={True: "#FF4B4B", False: "#0068C9"},
                         size=df[amount_col].abs(), hover_data=df.columns,
                         template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # --- PIPELINE EXECUTION ---
        st.divider()
        if not suspicious_df.empty:
            selected_id = st.selectbox("Select Transaction ID for Audit", suspicious_df['transaction_id'].unique())
            
            if st.button("🚀 Execute Multi-Agent Pipeline"):
                txn_row = suspicious_df[suspicious_df['transaction_id'] == selected_id].iloc[0].to_dict()
                
                with st.status("Agents Collaborating...") as status:
                    risk_scorer = RiskScorer()
                    typology_engine = TypologyEngine()
                    network_analyzer = NetworkAnalyzer()
                    network_analyzer.build_graph(df)
                    
                    evidence_engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
                    supervisor = SupervisorAgent()
                    
                    evidence_package_obj = evidence_engine.generate(str(selected_id), df)
                    evidence_package = evidence_package_obj.model_dump()
                    
                    final_state = supervisor.run_investigation(evidence_package)
                    
                    structured_sar = final_state.structured_sar
                    if structured_sar:
                        sar_report = structured_sar.to_txt()
                        audit_note = f"{structured_sar.validation_status} - Discrepancies: {len(structured_sar.audit_result.get('discrepancies', [])) if structured_sar.audit_result else 0}"
                    else:
                        sar_report = final_state.draft_narrative
                        audit_note = final_state.audit_feedback if final_state.audit_feedback else "VERIFIED"
                        
                    risk = evidence_package.get('risk_score', 0.0)
                    
                    typologies = evidence_package.get('typologies', [])
                    if isinstance(typologies, list):
                        typology_str = ", ".join([t.get('name', 'Unknown') if isinstance(t, dict) else str(t) for t in typologies])
                    else:
                        typology_str = str(typologies)
                    if not typology_str:
                        typology_str = "None"
                    
                    signals = []
                    for sig in evidence_package.get('anomaly_signals', []):
                        if isinstance(sig, dict):
                            signals.append(f"{sig.get('signal')}: {sig.get('raw')}")
                        else:
                            signals.append(str(sig))
                    context_msg = " | ".join(signals) if signals else "No specific historical deviation detected."
                    
                    st.session_state.current_data = {
                        "risk": risk, "typology": typology_str, "context": context_msg, 
                        "audit": audit_note, "report": sar_report, "evidence": evidence_package,
                        "id": selected_id,
                        "structured_sar": structured_sar
                    }
                    status.update(label="Full Audit Complete!", state="complete")

            # --- MULTI-AGENT REASONING & AUDIT TRAIL ---
            if 'current_data' in st.session_state:
                data = st.session_state.current_data
                
                st.markdown('<div class="logic-box">', unsafe_allow_html=True)
                st.markdown("### 🧠 Multi-Agent Reasoning Chain")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info(f"**⚖️ Typology Agent**\n\n{data['typology']}")
                with c2:
                    st.warning(f"**📈 Contextual Agent**\n\n{data['context']}")
                with c3:
                    st.success(f"**🕵️ Auditor Agent**\n\n{data['audit']}")
                st.markdown(f"**Confidence Score: {data['risk']:.2f}%**")
                st.markdown('</div>', unsafe_allow_html=True)

                # --- SAR REVIEW, AUDIT LOGGING, & DOWNLOAD ---
                st.write("#### 📝 Final Regulatory Narrative")
                final_report = st.text_area("AI Drafted SAR:", data['report'], height=300)

                col_left, col_right = st.columns(2)
                with col_left:
                    # THE AUDIT TRAIL OPTION
                    if st.button("✅ Approve & Log to Audit Trail"):
                        structured_sar = data.get('structured_sar')
                        if structured_sar:
                            from agents.models import ReportStatus, ReviewerStatus
                            structured_sar.report_status = ReportStatus.APPROVED
                            structured_sar.reviewer_status = ReviewerStatus.APPROVED
                            
                        log_audit(data['evidence'], final_report, structured_sar)
                        st.balloons()
                        st.success(f"Transaction {data['id']} successfully logged to SQLite Storage!")
                
                with col_right:
                    # THE DOWNLOAD TXT OPTION
                    st.download_button(
                        label="📥 Download SAR (.txt)",
                        data=final_report,
                        file_name=f"Barclays_SAR_{data['id']}.txt",
                        mime="text/plain"
                    )

    except Exception as e:
        st.error(f"System Error: {e}")