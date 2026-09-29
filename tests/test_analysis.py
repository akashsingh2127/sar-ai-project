import pytest
import pandas as pd
from analysis.network import NetworkAnalyzer
from analysis.typologies import TypologyEngine

def test_network_analyzer_circular():
    # A -> B -> C -> A
    data = [
        {'transaction_id': '1', 'sender': 'A', 'receiver': 'B', 'amount': 100},
        {'transaction_id': '2', 'sender': 'B', 'receiver': 'C', 'amount': 100},
        {'transaction_id': '3', 'sender': 'C', 'receiver': 'A', 'amount': 100}
    ]
    df = pd.DataFrame(data)
    
    analyzer = NetworkAnalyzer()
    analyzer.build_graph(df)
    
    cycles = analyzer.detect_circular_patterns()
    assert len(cycles) > 0
    # One cycle should be ['A', 'B', 'C'] or variation
    assert set(cycles[0]) == {'A', 'B', 'C'}
    
def test_network_analyzer_hub():
    # A sends to 6 different people
    data = [{'transaction_id': str(i), 'sender': 'A', 'receiver': f'B{i}', 'amount': 10} for i in range(6)]
    df = pd.DataFrame(data)
    
    analyzer = NetworkAnalyzer()
    analyzer.build_graph(df)
    
    analysis = analyzer.analyze_entity('A')
    assert analysis['out_degree'] == 6
    assert analysis['unique_counterparties'] == 6
    assert analysis['is_hub'] == True

def test_typology_structuring():
    engine = TypologyEngine()
    txn = {'transaction_id': '1', 'amount': 9900.0}
    
    detected = engine.detect(txn)
    assert len(detected) == 1
    assert detected[0]['typology'] == 'Structuring'
    
def test_typology_circular():
    engine = TypologyEngine()
    txn = {'transaction_id': '1'}
    network_data = {'is_circular': True, 'cycle_nodes': ['A', 'B']}
    
    detected = engine.detect(txn, network_data=network_data)
    assert len(detected) == 1
    assert detected[0]['typology'] == 'Circular transaction pattern'

def test_typology_multiple():
    engine = TypologyEngine()
    # High value and burst
    txn = {
        'transaction_id': '1', 
        'anomaly_score': 0.95,
        'is_burst_activity': 1
    }
    
    detected = engine.detect(txn)
    assert len(detected) == 2
    types = [d['typology'] for d in detected]
    assert 'High-value anomaly' in types
    assert 'Unusual transaction burst' in types
