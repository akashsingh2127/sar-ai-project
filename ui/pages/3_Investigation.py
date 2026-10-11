import sys
import os
import streamlit as st
import pandas as pd
import json

# Path fix for local imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from risk.scorer import RiskScorer
from analysis.typologies import TypologyEngine
from analysis.network import NetworkAnalyzer
from evidence.engine import EvidenceEngine
from agents.supervisor_agent import SupervisorAgent
from storage import get_storage

st.set_page_config(page_title="Investigation & Review", page_icon="🕵️", layout="wide")
st.title("🕵️ Multi-Agent Investigation & SAR Review")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("⚠️ No dataset loaded. Please go to the Home dashboard to upload a file.")
    st.stop()

if "suspicious_df" not in st.session_state or st.session_state.suspicious_df is None or st.session_state.suspicious_df.empty:
    st.warning("⚠️ No suspicious transactions detected. Please go to the Detection page first.")
    st.stop()

suspicious_df = st.session_state.suspicious_df
cols = st.session_state.get('cols', {})
txn_col = cols.get("transaction_id", "transaction_id")

selected_id = st.selectbox("Select Transaction ID to Investigate", suspicious_df[txn_col].unique())

if st.button("🚀 Execute Multi-Agent Pipeline"):
    with st.status("Agents Collaborating...") as status:
        try:
            # 1. Setup engines
            st.write("Initializing ML risk & typology engines...")
            risk_scorer = RiskScorer()
            typology_engine = TypologyEngine()
            network_analyzer = NetworkAnalyzer()
            
            # Use full dataset for network analysis
            network_analyzer.build_graph(st.session_state.df)
            
            # 2. Gather Evidence
            st.write("Gathering deterministic evidence...")
            evidence_engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
            evidence_package_obj = evidence_engine.generate(str(selected_id), st.session_state.df)
            evidence_package = evidence_package_obj.model_dump()
            
            # 3. Agent Investigation
            st.write("Running Supervisor, Writer, and Auditor Agents...")
            supervisor = SupervisorAgent()
            final_state = supervisor.run_investigation(evidence_package)
            
            st.session_state.investigation_results = {
                "id": selected_id,
                "evidence": evidence_package,
                "final_state": final_state
            }
            
            status.update(label="Full Audit Complete!", state="complete", expanded=False)
            
        except Exception as e:
            status.update(label=f"Investigation Failed: {e}", state="error")
            st.error(f"Error during execution: {str(e)}")
            st.stop()

if "investigation_results" in st.session_state and st.session_state.investigation_results["id"] == selected_id:
    res = st.session_state.investigation_results
    evidence = res["evidence"]
    final_state = res["final_state"]
    structured_sar = final_state.structured_sar
    
    st.divider()
    
    # Show Agent Process
    st.markdown("### 🧠 Multi-Agent Reasoning Chain")
    col_e, col_i, col_a = st.columns(3)
    
    with col_e:
        risk = evidence.get('risk_score', 0.0)
        st.info(f"**📊 Evidence & Risk**\n\nRisk Score: {risk:.2f}%\n\nTypologies: {len(evidence.get('typologies', []))} detected.")
        with st.expander("View Evidence JSON"):
            st.json(evidence)
            
    with col_i:
        st.warning(f"**✍️ Writer Agent**\n\nGenerated draft narrative from evidence constraints.")
        
    with col_a:
        if structured_sar:
            audit_status = structured_sar.validation_status
            discreps = len(structured_sar.audit_result.get('discrepancies', [])) if structured_sar.audit_result else 0
            st.success(f"**🕵️ Auditor Agent**\n\nStatus: {audit_status}\nDiscrepancies: {discreps}")
        else:
            st.success(f"**🕵️ Auditor Agent**\n\nStatus: {final_state.audit_feedback or 'VERIFIED'}")

    st.divider()
    
    st.markdown("### 📝 SAR Review")
    
    if structured_sar:
        final_report = structured_sar.to_txt()
    else:
        final_report = final_state.draft_narrative
        
    st.text_area("Final Regulatory Narrative (Read-Only)", value=final_report, height=300, disabled=True)
    
    st.markdown("---")
    st.markdown("#### Compliance Decision")
    st.info("AI-generated recommendations are NOT final compliance decisions. Human review is required.")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("✅ Approve"):
            try:
                storage = get_storage()
                if structured_sar:
                    from agents.models import ReportStatus, ReviewerStatus
                    structured_sar.report_status = ReportStatus.APPROVED
                    structured_sar.reviewer_status = ReviewerStatus.APPROVED
                    
                storage.save_investigation(str(selected_id), "APPROVED")
                storage.save_sar_report(structured_sar.sar_id if structured_sar else f"SAR-{selected_id}", str(selected_id), json.loads(structured_sar.to_json()) if structured_sar else {"narrative": final_report})
                storage.log_audit(
                    entity_id=structured_sar.sar_id if structured_sar else f"SAR-{selected_id}",
                    entity_type="SAR_REPORT",
                    action="HUMAN_REVIEW_APPROVED",
                    status="COMPLETED"
                )
                st.success("SAR successfully approved and logged to persistent storage.")
                st.balloons()
            except Exception as e:
                st.error(f"Persistence error: {e}")
                
    with c2:
        if st.button("❌ Reject"):
            try:
                storage = get_storage()
                if structured_sar:
                    from agents.models import ReportStatus, ReviewerStatus
                    structured_sar.report_status = ReportStatus.REJECTED
                    structured_sar.reviewer_status = ReviewerStatus.REJECTED
                    
                storage.save_investigation(str(selected_id), "REJECTED")
                storage.log_audit(
                    entity_id=structured_sar.sar_id if structured_sar else f"SAR-{selected_id}",
                    entity_type="SAR_REPORT",
                    action="HUMAN_REVIEW_REJECTED",
                    status="COMPLETED"
                )
                st.warning("Investigation rejected and logged.")
            except Exception as e:
                st.error(f"Persistence error: {e}")
                
    with c3:
        if st.button("🔄 Request Revision"):
            try:
                storage = get_storage()
                if structured_sar:
                    from agents.models import ReportStatus, ReviewerStatus
                    structured_sar.report_status = ReportStatus.PENDING_REVIEW
                    structured_sar.reviewer_status = ReviewerStatus.REVISION_REQUESTED
                    
                storage.save_investigation(str(selected_id), "REVISION_REQUESTED")
                storage.log_audit(
                    entity_id=structured_sar.sar_id if structured_sar else f"SAR-{selected_id}",
                    entity_type="SAR_REPORT",
                    action="HUMAN_REVIEW_REVISION_REQUESTED",
                    status="COMPLETED"
                )
                st.info("Revision requested and logged.")
            except Exception as e:
                st.error(f"Persistence error: {e}")
                
    with c4:
        st.download_button(
            label="📥 Download SAR (.txt)",
            data=final_report,
            file_name=f"SAR_{selected_id}.txt",
            mime="text/plain"
        )
