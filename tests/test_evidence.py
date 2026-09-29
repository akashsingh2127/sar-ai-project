import pytest
import pandas as pd
from evidence.engine import EvidenceEngine
from risk.scorer import RiskScorer
from analysis.typologies import TypologyEngine
from analysis.network import NetworkAnalyzer

def test_evidence_engine():
    # Setup dependencies
    risk_scorer = RiskScorer()
    typology_engine = TypologyEngine()
    network_analyzer = NetworkAnalyzer()
    
    engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
    
    # Setup data
    data = [
        {
            'transaction_id': '101',
            'sender': 'Alice',
            'receiver': 'Bob',
            'amount': 9500.0,
            'timestamp': '2023-01-01 10:00:00',
            'currency': 'USD',
            'transaction_type': 'wire',
            'anomaly_score': 0.95,
            'historical_deviation': 3.5,
            'is_burst_activity': 1,
            'sender_unique_counterparties': 2
        },
        {
            'transaction_id': '102',
            'sender': 'Alice',
            'receiver': 'Charlie',
            'amount': 100.0,
            'timestamp': '2023-01-01 09:00:00',
            'currency': 'USD',
            'transaction_type': 'wire'
        }
    ]
    df = pd.DataFrame(data)
    network_analyzer.build_graph(df)
    
    # Generate package
    pkg = engine.generate('101', df)
    
    # Assert completeness and constraints
    assert pkg.transaction_details.transaction_id == '101'
    assert pkg.transaction_details.amount == 9500.0
    
    # Customer history should have 1 item (the previous transaction 102)
    assert len(pkg.customer_history) == 1
    assert pkg.customer_history[0]['transaction_id'] == '102'
    
    # Typologies should detect High Value, Burst, Structuring
    detected_types = [t['typology'] for t in pkg.typologies]
    assert 'Structuring' in detected_types
    assert 'High-value anomaly' in detected_types
    assert 'Unusual transaction burst' in detected_types
    
    # Risk Score
    assert pkg.risk_score > 0
    assert pkg.risk_level in ['Low', 'Medium', 'High', 'Critical']
    
    # Network signals
    assert 'unique_counterparties' in pkg.network_signals
    assert pkg.network_signals['unique_counterparties'] == 2

def test_evidence_engine_missing_txn():
    risk_scorer = RiskScorer()
    typology_engine = TypologyEngine()
    network_analyzer = NetworkAnalyzer()
    
    engine = EvidenceEngine(risk_scorer, typology_engine, network_analyzer)
    df = pd.DataFrame([{'transaction_id': '101'}])
    
    with pytest.raises(ValueError, match="Transaction ID 999 not found"):
        engine.generate('999', df)
