import pytest
from risk.scorer import RiskScorer

def test_risk_scorer_normal():
    # A perfectly normal transaction with no deviations
    scorer = RiskScorer()
    txn = {
        'anomaly_score': 0.1,
        'historical_deviation': 0.0,
        'is_burst_activity': 0,
        'sender_unique_counterparties': 1
    }
    
    score, level, explanations = scorer.calculate_score(txn)
    
    # Expected score:
    # anomaly: (0.1/1)*100 = 10 * 0.3 = 3
    # deviation: 0 * 0.3 = 0
    # burst: 0 * 0.2 = 0
    # counterparty: (1/10)*100 = 10 * 0.2 = 2
    # Total weighted sum = 5. Total weight = 1.0. Final = 5.0
    
    assert score == 5.0
    assert level == 'Low'
    assert 'anomaly_score' in explanations

def test_risk_scorer_highly_anomalous():
    scorer = RiskScorer()
    txn = {
        'anomaly_score': 1.5, # > 1.0 caps at 100
        'historical_deviation': 4.0, # > 3.0 caps at 100
        'is_burst_activity': 1, # 100
        'sender_unique_counterparties': 20 # > 10 caps at 100
    }
    
    score, level, explanations = scorer.calculate_score(txn)
    
    # Everything should cap at 100, so score should be 100.
    assert score == 100.0
    assert level == 'Critical'
    
def test_risk_scorer_missing_signals():
    scorer = RiskScorer()
    txn = {
        'historical_deviation': 1.5
    }
    # Only deviation is present.
    # normalized_dev = (1.5/3)*100 = 50
    # weight = 0.3
    # weighted_sum = 15.0
    # total_weight = 0.3
    # final = 15/0.3 = 50.0
    
    score, level, explanations = scorer.calculate_score(txn)
    
    assert score == 50.0
    assert level == 'Medium'
    assert 'historical_deviation' in explanations
    assert 'anomaly_score' not in explanations

def test_risk_scorer_empty_signals():
    scorer = RiskScorer()
    txn = {}
    
    score, level, explanations = scorer.calculate_score(txn)
    
    assert score == 0.0
    assert level == 'Low'
    assert 'warning' in explanations

def test_risk_scorer_custom_thresholds():
    custom_thresholds = {
        'Fine': (0.0, 50.0),
        'Bad': (50.01, 100.0)
    }
    scorer = RiskScorer(thresholds=custom_thresholds)
    
    txn = {'historical_deviation': 3.0} # Maps to 100 score
    score, level, _ = scorer.calculate_score(txn)
    
    assert score == 100.0
    assert level == 'Bad'
