import pandas as pd
import os
from app.utils import safe_numeric_conversion
from app.schema import identify_columns
from app.detection import detect_suspicious_transactions
from app.scorer import calculate_risk_score
from app.typology import assign_typology
from app.evidence import generate_evidence
from app.narrative import build_prompt
from app.llm_service import generate_sar, run_adversarial_audit
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


    print(" Scanning for anomalies...")
    suspicious_txns = detect_suspicious_transactions(df, amount_col)
    
    if not suspicious_txns:
        print(" No suspicious transactions detected in this batch.")
        return

    print(f" Found {len(suspicious_txns)} suspicious records. Starting Multi-Agent Processing...\n")


    for txn in suspicious_txns:
        
        risk_score = calculate_risk_score(txn, df) 
        typology = assign_typology(txn)
        
       
        potential_keys = ['customer_id', 'customer_name', 'account_number']
        user_key = next((k for k in potential_keys if k in txn), 'transaction_id')
        user_val = txn.get(user_key)
    
        evidence_package = generate_evidence(txn, risk_score, typology, amount_col)
 
        print(f" Agent 1 (Writer): Generating Narrative for ID {txn.get('transaction_id')}...")
        prompt = build_prompt(evidence_package)
        sar_report = generate_sar(prompt)
        
        print(f" Agent 2 (Auditor): Verifying narrative against raw data...")
        audit_note = run_adversarial_audit(sar_report, txn)
        
  
        log_audit(evidence_package, sar_report)

        print("\n" + "═"*60)
        print(f"ID: {txn.get('transaction_id')} | SUBJECT: {user_val}")
        print(f"RISK: {risk_score:.2f}% | TYPOLOGY: {typology}")
        print(f"AUDIT STATUS: {audit_note}")
        print("─" * 60)
        print(sar_report)
        print("═"*60 + "\n")

    print(" Pipeline execution complete. Audit logs updated.")

if __name__ == "__main__":
    main()