from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd

class TransactionDetails(BaseModel):
    transaction_id: str
    sender: Optional[str] = None
    receiver: Optional[str] = None
    amount: float
    timestamp: Optional[str] = None
    currency: Optional[str] = None
    transaction_type: Optional[str] = None

class EvidencePackage(BaseModel):
    """
    Deterministic, structured payload defining exactly what the LLM can see.
    Prevents hallucination by providing pre-calculated facts.
    """
    transaction_details: TransactionDetails
    customer_history: List[Dict[str, Any]] = Field(default_factory=list)
    anomaly_signals: List[Dict[str, Any]] = Field(default_factory=list)
    risk_score: float
    risk_level: str
    risk_explanations: Dict[str, Any] = Field(default_factory=dict)
    typologies: List[Dict[str, Any]] = Field(default_factory=list)
    related_transactions: List[str] = Field(default_factory=list)
    network_signals: Dict[str, Any] = Field(default_factory=dict)

class EvidenceEngine:
    """
    Compiles disparate analytical signals into a single, cohesive Evidence Package.
    """
    def __init__(self, risk_scorer, typology_engine, network_analyzer):
        self.risk_scorer = risk_scorer
        self.typology_engine = typology_engine
        self.network_analyzer = network_analyzer

    def generate(self, txn_id: str, df: pd.DataFrame) -> EvidencePackage:
        """
        Generates the evidence package for a specific transaction.
        Expects `df` to already contain engineered features from Phase 3 and 4A.
        """
        if df.empty or 'transaction_id' not in df.columns:
            raise ValueError("Dataframe must contain 'transaction_id'.")
            
        # 1. Isolate the target transaction
        txn_rows = df[df['transaction_id'].astype(str) == str(txn_id)]
        if txn_rows.empty:
            raise ValueError(f"Transaction ID {txn_id} not found.")
            
        # If there are multiple detectors, the same transaction_id might appear multiple times in the combined output of 4A.
        # But we assume `df` here is the master dataframe where each row is a transaction, 
        # and anomalies are merged back as columns or handled via the RiskScorer.
        txn_series = txn_rows.iloc[0]
        txn_dict = txn_series.to_dict()
        
        # 2. Transaction Details
        details = TransactionDetails(
            transaction_id=str(txn_id),
            sender=str(txn_series.get('sender', 'UNKNOWN')),
            receiver=str(txn_series.get('receiver', 'UNKNOWN')),
            amount=float(txn_series.get('amount', 0.0)),
            timestamp=str(txn_series.get('timestamp', '')) if pd.notnull(txn_series.get('timestamp')) else None,
            currency=str(txn_series.get('currency', 'UNKNOWN')),
            transaction_type=str(txn_series.get('transaction_type', 'UNKNOWN'))
        )
        
        # 3. Customer History
        sender = txn_series.get('sender')
        history_dicts = []
        if pd.notnull(sender):
            # Fetch past transactions for the same sender, up to 10
            hist_df = df[(df['sender'] == sender) & (df['transaction_id'] != txn_id)].head(10)
            history_dicts = hist_df[['transaction_id', 'amount', 'timestamp', 'receiver']].to_dict(orient='records')
            # Fix timestamps
            for h in history_dicts:
                if pd.notnull(h.get('timestamp')):
                    h['timestamp'] = str(h['timestamp'])
                else:
                    h['timestamp'] = None

        # 4. Risk Score & Explanations
        risk_score, risk_level, explanations = self.risk_scorer.calculate_score(txn_dict)
        
        # 5. Network Signals
        network_signals = {}
        if pd.notnull(sender):
            network_signals = self.network_analyzer.analyze_entity(sender)
            
        is_circular = False
        cycle_nodes = []
        cycles = self.network_analyzer.detect_circular_patterns()
        for c in cycles:
            if sender in c or txn_series.get('receiver') in c:
                is_circular = True
                cycle_nodes = c
                break
                
        network_data = {'is_circular': is_circular, 'cycle_nodes': cycle_nodes}
        network_signals['is_circular'] = is_circular
        network_signals['cycle_nodes'] = cycle_nodes

        # 6. Typologies
        typologies = self.typology_engine.detect(txn_dict, network_data=network_data)
        
        # 7. Related Transactions (Extract from typologies or cycles)
        related_txns = set()
        for t in typologies:
            for rt in t.get('supporting_transaction_ids', []):
                if str(rt) != str(txn_id):
                    related_txns.add(str(rt))
                    
        # 8. Anomaly Signals (Grab from explanations or direct from df)
        anomaly_signals = []
        if 'anomaly_score' in explanations:
            anomaly_signals.append({
                'signal': 'anomaly_score',
                'raw': explanations['anomaly_score']['raw']
            })
        if 'historical_deviation' in explanations:
            anomaly_signals.append({
                'signal': 'historical_deviation',
                'raw': explanations['historical_deviation']['raw']
            })
            
        return EvidencePackage(
            transaction_details=details,
            customer_history=history_dicts,
            anomaly_signals=anomaly_signals,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_explanations=explanations,
            typologies=typologies,
            related_transactions=list(related_txns),
            network_signals=network_signals
        )
