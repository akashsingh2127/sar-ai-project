import pytest
import pandas as pd
from evaluation.ml import MLEvaluator
from evaluation.llm import LLMEvaluator

def test_ml_evaluator_no_ground_truth():
    df = pd.DataFrame({
        'transaction_id': [1, 2, 3],
        'is_suspicious': [True, False, True]
    })
    
    evaluator = MLEvaluator()
    res = evaluator.evaluate(df)
    
    assert res['total_transactions'] == 3
    assert res['flagged_transactions'] == 2
    assert res['percentage_flagged'] == pytest.approx(66.66, 0.1)
    assert res['supervised_metrics_available'] is False
    assert "not available" in res['reason']

def test_ml_evaluator_with_ground_truth():
    df = pd.DataFrame({
        'transaction_id': [1, 2, 3, 4],
        'is_suspicious': [1, 0, 1, 0],
        'is_laundering': [1, 0, 0, 0],
        'anomaly_score': [0.9, 0.1, 0.8, 0.2]
    })
    
    evaluator = MLEvaluator(ground_truth_col='is_laundering')
    res = evaluator.evaluate(df)
    
    assert res['supervised_metrics_available'] is True
    assert res['total_transactions'] == 4
    assert res['flagged_transactions'] == 2
    assert res['precision'] == 0.5
    assert res['recall'] == 1.0
    assert 'roc_auc' in res

def test_ml_evaluator_one_class():
    df = pd.DataFrame({
        'transaction_id': [1, 2, 3],
        'is_suspicious': [1, 0, 1],
        'is_laundering': [0, 0, 0],
        'anomaly_score': [0.9, 0.1, 0.8]
    })
    
    evaluator = MLEvaluator(ground_truth_col='is_laundering')
    res = evaluator.evaluate(df)
    
    assert res['supervised_metrics_available'] is True
    assert res['precision'] == 0.0
    assert res['recall'] == 0.0
    assert 'roc_auc' not in res
    assert 'Only one class' in res['reason']

def test_llm_evaluator_single():
    evaluator = LLMEvaluator()
    evidence = {
        "transaction_details": {
            "transaction_id": "TXN-1234",
            "amount": 10000.50,
            "currency": "USD",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        "typologies": [{"typology_name": "STRUCTURING"}]
    }
    
    # Perfect narrative
    narrative_good = "Transaction TXN-1234 on 2024-01-01 involved 10,000.50 USD. Typology identified: STRUCTURING."
    res = evaluator.evaluate_sar(evidence, narrative_good)
    
    # Missing sender/receiver, but the evidence didn't have it either, so it shouldn't fail customer checks
    # Let's check overall_passed. Wait, date is checked.
    assert res['overall_passed'] is True
    assert res['evidence_coverage_percentage'] == 100.0
    
    # Bad narrative
    narrative_bad = "A transaction occurred for 500 EUR."
    res2 = evaluator.evaluate_sar(evidence, narrative_bad)
    
    assert res2['overall_passed'] is False
    assert res2['checks_failed'] > 0
    assert res2['missing_evidence_count'] > 0
    
def test_llm_evaluator_batch():
    evaluator = LLMEvaluator()
    records = [
        {
            "evidence": {"transaction_id": "T1", "amount": 100},
            "narrative": "T1 was for 100"
        },
        {
            "evidence": {"transaction_id": "T2", "amount": 200},
            "narrative": "T2 was for 500"
        }
    ]
    
    res = evaluator.evaluate_batch(records)
    
    assert res['total_sars_evaluated'] == 2
    assert res['sars_passed_audit'] == 1
    assert res['pass_rate_percentage'] == 50.0
