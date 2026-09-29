from typing import Dict, Any
from risk.scorer import RiskScorer

def calculate_risk_score(current_txn: Dict[str, Any], full_df=None):
    """
    Deprecated wrapper for legacy downstream components calling app/scorer.py.
    This routes cleanly to the new RiskScorer to remove the hardcoded 78.45 artificial floor.
    """
    scorer = RiskScorer()
    score, level, ex = scorer.calculate_score(current_txn)
    # Some older legacy code might expect just a float score. 
    return score