import pandas as pd
from typing import Dict, Tuple, Any

class RiskScorer:
    """
    Transparent risk scoring module mapping transaction features to a 0-100 risk score.
    """
    def __init__(
        self, 
        thresholds: Dict[str, Tuple[float, float]] = None,
        weights: Dict[str, float] = None
    ):
        # Configurable thresholds
        self.thresholds = thresholds or {
            'Low': (0.0, 29.99),
            'Medium': (30.0, 59.99),
            'High': (60.0, 79.99),
            'Critical': (80.0, 100.0)
        }
        
        # Component weights for available signals
        self.weights = weights or {
            'anomaly_score': 0.3,
            'historical_deviation': 0.3,
            'burst_activity': 0.2,
            'counterparty_risk': 0.2
        }
        
    def _get_risk_level(self, score: float) -> str:
        for level, (min_val, max_val) in self.thresholds.items():
            if min_val <= score <= max_val:
                return level
        if score >= 100.0:
            return 'Critical'
        return 'Low'

    def calculate_score(self, txn: Dict[str, Any]) -> Tuple[float, str, Dict[str, Any]]:
        """
        Calculates risk score based on measurable signals.
        Returns:
            risk_score (float)
            risk_level (str)
            explanations (dict of component contributions)
        """
        explanations = {}
        total_weight_used = 0.0
        weighted_sum = 0.0
        
        # 1. Anomaly Score (from detection pipeline)
        if 'anomaly_score' in txn and pd.notnull(txn['anomaly_score']):
            val = float(txn['anomaly_score'])
            # Assuming raw anomaly scores from IF or ZScore are around 0.0 to 1.0 on average, 
            # and > 1.0 for extremes. We normalize to 100 max.
            normalized_anomaly = min((val / 1.0) * 100.0, 100.0)
            weight = self.weights.get('anomaly_score', 0.3)
            
            weighted_sum += normalized_anomaly * weight
            total_weight_used += weight
            explanations['anomaly_score'] = {
                'raw': val,
                'normalized': round(normalized_anomaly, 2),
                'contribution': round(normalized_anomaly * weight, 2)
            }
            
        # 2. Historical Deviation (Z-score from engineer.py)
        if 'historical_deviation' in txn and pd.notnull(txn['historical_deviation']):
            dev = abs(float(txn['historical_deviation']))
            # A Z-score of 3 is generally a critical outlier
            normalized_dev = min((dev / 3.0) * 100.0, 100.0)
            weight = self.weights.get('historical_deviation', 0.3)
            
            weighted_sum += normalized_dev * weight
            total_weight_used += weight
            explanations['historical_deviation'] = {
                'raw': round(dev, 3),
                'normalized': round(normalized_dev, 2),
                'contribution': round(normalized_dev * weight, 2)
            }
            
        # 3. Burst Activity (Temporal signal)
        if 'is_burst_activity' in txn and pd.notnull(txn['is_burst_activity']):
            val = int(txn['is_burst_activity'])
            normalized_burst = 100.0 if val == 1 else 0.0
            weight = self.weights.get('burst_activity', 0.2)
            
            weighted_sum += normalized_burst * weight
            total_weight_used += weight
            explanations['burst_activity'] = {
                'raw': val,
                'normalized': round(normalized_burst, 2),
                'contribution': round(normalized_burst * weight, 2)
            }
            
        # 4. Counterparty Risk (Network signal)
        if 'sender_unique_counterparties' in txn and pd.notnull(txn['sender_unique_counterparties']):
            count = int(txn['sender_unique_counterparties'])
            # We scale unique counterparties up to a cap of 10.
            normalized_cp = min((count / 10.0) * 100.0, 100.0)
            weight = self.weights.get('counterparty_risk', 0.2)
            
            weighted_sum += normalized_cp * weight
            total_weight_used += weight
            explanations['counterparty_risk'] = {
                'raw': count,
                'normalized': round(normalized_cp, 2),
                'contribution': round(normalized_cp * weight, 2)
            }

        if total_weight_used > 0:
            final_score = (weighted_sum / total_weight_used)
        else:
            final_score = 0.0
            explanations['warning'] = "No valid signals found for scoring."
            
        final_score = round(min(max(final_score, 0.0), 100.0), 2)
        risk_level = self._get_risk_level(final_score)
        
        return final_score, risk_level, explanations
