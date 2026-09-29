from typing import Dict, Any, List

class TypologyEngine:
    def __init__(self):
        # Enforce distinction between rules, ML, and LLM behavior
        self.categories = {
            'Structuring': 'RULE-BASED',
            'Rapid movement of funds': 'RULE-BASED',
            'High-value anomaly': 'ML/STATISTICAL SIGNAL',
            'Unusual transaction burst': 'RULE-BASED',
            'Multiple-counterparty behavior': 'RULE-BASED',
            'Circular transaction pattern': 'RULE-BASED'
        }
        
    def detect(self, txn: Dict[str, Any], network_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Evaluates a transaction for known typologies based on hard signals.
        Returns a list of detected typologies with evidence.
        """
        detected = []
        txn_id = txn.get('transaction_id', 'unknown')
        
        # 1. High-value anomaly (ML/STATISTICAL)
        anomaly_score = float(txn.get('anomaly_score', 0.0)) if txn.get('anomaly_score') is not None else 0.0
        hist_dev = float(txn.get('historical_deviation', 0.0)) if txn.get('historical_deviation') is not None else 0.0
        
        if anomaly_score > 0.8 or abs(hist_dev) > 2.5:
            detected.append({
                'typology': 'High-value anomaly',
                'source': self.categories['High-value anomaly'],
                'confidence': 'High' if anomaly_score > 0.9 else 'Medium',
                'supporting_transaction_ids': [txn_id],
                'supporting_signals': f"Anomaly score: {anomaly_score}, Hist Dev: {hist_dev}",
                'explanation': 'Transaction significantly deviates from established behavior.'
            })
            
        # 2. Unusual transaction burst
        burst = int(txn.get('is_burst_activity', 0)) if txn.get('is_burst_activity') is not None else 0
        if burst == 1:
            detected.append({
                'typology': 'Unusual transaction burst',
                'source': self.categories['Unusual transaction burst'],
                'confidence': 'High',
                'supporting_transaction_ids': [txn_id],
                'supporting_signals': "is_burst_activity=1",
                'explanation': 'Transaction occurred within an unusually short time window of previous activity.'
            })
            
        # 3. Multiple-counterparty behavior
        unique_cp = int(txn.get('sender_unique_counterparties', 0)) if txn.get('sender_unique_counterparties') is not None else 0
        if unique_cp > 5:
            detected.append({
                'typology': 'Multiple-counterparty behavior',
                'source': self.categories['Multiple-counterparty behavior'],
                'confidence': 'Medium',
                'supporting_transaction_ids': [txn_id],
                'supporting_signals': f"unique_counterparties={unique_cp}",
                'explanation': 'Sender is transacting with a high volume of distinct entities.'
            })
            
        # 4. Structuring
        amount = float(txn.get('amount', 0.0)) if txn.get('amount') is not None else 0.0
        if 9000 <= amount <= 9999.99:
            detected.append({
                'typology': 'Structuring',
                'source': self.categories['Structuring'],
                'confidence': 'Medium',
                'supporting_transaction_ids': [txn_id],
                'supporting_signals': f"amount={amount}",
                'explanation': 'Amount is just below typical $10k reporting thresholds.'
            })
            
        # 5. Circular transaction pattern
        if network_data and network_data.get('is_circular', False):
            cycle_nodes = network_data.get('cycle_nodes', [])
            detected.append({
                'typology': 'Circular transaction pattern',
                'source': self.categories['Circular transaction pattern'],
                'confidence': 'High',
                'supporting_transaction_ids': [txn_id],
                'supporting_signals': f"Detected cycle among: {cycle_nodes}",
                'explanation': 'Funds flow in a circular path between entities.'
            })
            
        return detected
