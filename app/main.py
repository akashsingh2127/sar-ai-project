import pandas as pd
import os
from app.utils import safe_numeric_conversion
from app.schema import identify_columns

from detection.detector_pipeline import DetectorPipeline
from risk.scorer import RiskScorer
from analysis.typologies import TypologyEngine
from analysis.network import NetworkAnalyzer
from evidence.engine import EvidenceEngine
from agents.supervisor_agent import SupervisorAgent
from app.audit import log_audit

def main():
    print("--- Barclays Hackathon: SAR-AI Generation System ---")
    
    csv_path = os.path.join("data", "sample_transactions.csv")
    if not os.path.exists(csv_path):
        print(f" Error: {csv_path} not found.")
        return

    print(" Loading dataset...")
    df = pd.read_csv(csv_path)

    try:
        cols = identify_columns(df)
        amount_col = cols['amount']
        df = safe_numeric_conversion(df, amount_col)
        print(f"Data cleaned. Monitoring column: '{amount_col}'")
    except Exception as e:
        print(f" Schema Error: {e}")
        return

    print(" Initializing Pipeline Components...")
    detector = DetectorPipeline(detectors=['zscore', 'isolation_forest'])
    risk_scorer = RiskScorer()
    typology_engine = TypologyEngine()
    network_analyzer = NetworkAnalyzer()
    
    # Must build graph first
    network_analyzer.build_graph(df)
    
    evidence_engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
    supervisor = SupervisorAgent()

    print(" Scanning for anomalies...")
    detector.fit(df)
    anomalies_df = detector.predict(df)
    
    suspicious_txns = anomalies_df[anomalies_df['is_anomaly'] == True]
    
    if suspicious_txns.empty:
        print(" No suspicious transactions detected in this batch.")
        return

    # We need unique transaction IDs that are anomalous
    unique_suspicious_ids = suspicious_txns['transaction_id'].unique()

    print(f" Found {len(unique_suspicious_ids)} suspicious records. Starting Multi-Agent Processing...\n")

    for txn_id in unique_suspicious_ids:
        # Get raw transaction data from original df
        txn_series = df[df['transaction_id'].astype(str) == str(txn_id)].iloc[0]
        
        print(f" Orchestrating agents for ID {txn_id}...")
        
        try:
            # Generate deterministic evidence package
            evidence_package_obj = evidence_engine.generate(str(txn_id), df)
            evidence_package = evidence_package_obj.model_dump()
            
            # Run Supervisor state machine
            final_state = supervisor.run_investigation(evidence_package)
            
            structured_sar = final_state.structured_sar
            if structured_sar:
                sar_report = structured_sar.to_txt()
                audit_note = f"{structured_sar.validation_status} - Discrepancies: {len(structured_sar.audit_result.get('discrepancies', [])) if structured_sar.audit_result else 0}"
            else:
                sar_report = final_state.draft_narrative
                audit_note = final_state.audit_feedback if final_state.audit_feedback else "VERIFIED"
            
            # Format output
            risk_score = evidence_package.get('risk_score', 0.0)
            typologies = evidence_package.get('typologies', [])
            if isinstance(typologies, list):
                typology_str = ", ".join([t.get('name', 'Unknown') if isinstance(t, dict) else str(t) for t in typologies])
            else:
                typology_str = str(typologies)
            if not typology_str:
                typology_str = "None"
            
            log_audit(evidence_package, sar_report, structured_sar)

            print("\n" + "═"*60)
            print(f"ID: {txn_id} | SUBJECT: {txn_series.get('sender', 'UNKNOWN')}")
            print(f"RISK: {risk_score:.2f} | TYPOLOGY: {typology_str}")
            print(f"AUDIT STATUS: {audit_note}")
            print("─" * 60)
            print(sar_report)
            print("═"*60 + "\n")
            
        except Exception as e:
            print(f"Error processing transaction {txn_id}: {e}")

    print(" Pipeline execution complete. Audit logs updated.")

if __name__ == "__main__":
    main()