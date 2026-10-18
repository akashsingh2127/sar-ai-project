import sys
import os
import argparse
import pandas as pd
from dotenv import load_dotenv

# Path fix for local imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

load_dotenv()

from app.utils import safe_numeric_conversion
from app.schema import identify_columns
from data.ingestion.dataset_registry import DEFAULT_DATASET
from data.ingestion.huggingface_loader import load_and_validate_dataset

from detection.detector_pipeline import DetectorPipeline
from risk.scorer import RiskScorer
from analysis.typologies import TypologyEngine
from analysis.network import NetworkAnalyzer
from evidence.engine import EvidenceEngine
from agents.supervisor_agent import SupervisorAgent
from app.audit import log_audit
from app.logger import setup_logger

logger = setup_logger("sar_ai.main")

def main():
    parser = argparse.ArgumentParser(description="Barclays Hackathon: SAR-AI Generation System")
    parser.add_argument(
        "--source", 
        choices=["csv", "huggingface", "hf"], 
        default=os.environ.get("DATA_SOURCE", "csv"), 
        help="Data source: 'csv' for local file, 'huggingface'/'hf' for Hugging Face stream"
    )
    parser.add_argument(
        "--csv-path", 
        default=os.environ.get("CSV_PATH", os.path.join("data", "sample_transactions.csv")), 
        help="Path to local CSV dataset"
    )
    parser.add_argument(
        "--dataset", 
        default=os.environ.get("HF_DATASET", DEFAULT_DATASET), 
        help="Registered Hugging Face dataset identifier"
    )
    parser.add_argument(
        "--max-records", 
        type=int, 
        default=int(os.environ.get("MAX_RECORDS", "1000")), 
        help="Maximum records to load from Hugging Face stream"
    )
    args = parser.parse_args()

    logger.info("--- Barclays Hackathon: SAR-AI Generation System ---")
    source = args.source.lower()
    
    if source in ["huggingface", "hf"]:
        logger.info(f"Loading Hugging Face dataset '{args.dataset}' (max {args.max_records} records)...")
        try:
            df = load_and_validate_dataset(args.dataset, max_records=args.max_records)
            logger.info(f"Loaded and validated {len(df)} records from Hugging Face ({args.dataset}).")
            source_info = f"Hugging Face: {args.dataset} ({len(df)} records)"
        except Exception as e:
            logger.error(f"Failed to load Hugging Face dataset '{args.dataset}': {e}. Falling back to local CSV...")
            if not os.path.exists(args.csv_path):
                logger.error(f"Fallback CSV path {args.csv_path} not found.")
                return
            df = pd.read_csv(args.csv_path)
            source_info = f"Local CSV (Fallback): {args.csv_path}"
    else:
        if not os.path.exists(args.csv_path):
            logger.error(f"Error: {args.csv_path} not found.")
            return
        logger.info(f"Loading local dataset from {args.csv_path}...")
        df = pd.read_csv(args.csv_path)
        source_info = f"Local CSV: {args.csv_path}"

    try:
        cols = identify_columns(df)
        amount_col = cols['amount']
        df = safe_numeric_conversion(df, amount_col)
        logger.info(f"Data cleaned. Monitoring column: '{amount_col}' from {source_info}")
    except Exception as e:
        logger.exception(f"Schema Error: {e}")
        return

    logger.info("Initializing Pipeline Components...")
    detector = DetectorPipeline(detectors=['zscore', 'isolation_forest'])
    risk_scorer = RiskScorer()
    typology_engine = TypologyEngine()
    network_analyzer = NetworkAnalyzer()
    
    # Must build graph first
    network_analyzer.build_graph(df)
    
    evidence_engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
    supervisor = SupervisorAgent()

    logger.info("Scanning for anomalies...")
    detector.fit(df)
    anomalies_df = detector.predict(df)
    
    suspicious_txns = anomalies_df[anomalies_df['is_anomaly'] == True]
    
    if suspicious_txns.empty:
        logger.info("No suspicious transactions detected in this batch.")
        return

    # We need unique transaction IDs that are anomalous
    unique_suspicious_ids = suspicious_txns['transaction_id'].unique()

    logger.info(f"Found {len(unique_suspicious_ids)} suspicious records from {source_info}. Starting Multi-Agent Processing...")

    for txn_id in unique_suspicious_ids:
        # Get raw transaction data from original df
        txn_matches = df[df['transaction_id'].astype(str) == str(txn_id)]
        if txn_matches.empty:
            continue
        txn_series = txn_matches.iloc[0]
        
        logger.info(f"Orchestrating agents for ID {txn_id}...")
        
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

            print("\n" + "="*60)
            print(f"SOURCE: {source_info}")
            print(f"ID: {txn_id} | SUBJECT: {txn_series.get('sender', 'UNKNOWN')}")
            print(f"RISK: {risk_score:.2f} | TYPOLOGY: {typology_str}")
            print(f"AUDIT STATUS: {audit_note}")
            print("-" * 60)
            print(sar_report)
            print("="*60 + "\n")
            
        except Exception as e:
            logger.exception(f"Error processing transaction {txn_id}: {e}")

    logger.info("Pipeline execution complete. Audit logs updated.")

if __name__ == "__main__":
    main()