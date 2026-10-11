import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional

try:
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class MLEvaluator:
    """
    Evaluates detection performance on datasets.
    Supports calculating supervised metrics if ground truth labels are available.
    """
    def __init__(self, ground_truth_col: Optional[str] = None, prediction_col: str = 'is_suspicious', score_col: str = 'anomaly_score'):
        self.ground_truth_col = ground_truth_col
        self.prediction_col = prediction_col
        self.score_col = score_col
        
    def evaluate(self, df: pd.DataFrame) -> Dict[str, Any]:
        results = {}
        total = len(df)
        results['total_transactions'] = int(total)
        
        if self.prediction_col in df.columns:
            flagged = df[self.prediction_col].sum()
            results['flagged_transactions'] = int(flagged)
            results['percentage_flagged'] = float((flagged / total) * 100) if total > 0 else 0.0
        else:
            results['error'] = f"Prediction column '{self.prediction_col}' missing"
            return results
            
        if not self.ground_truth_col or self.ground_truth_col not in df.columns:
            results['supervised_metrics_available'] = False
            results['reason'] = "Ground truth labels not available in dataset."
            return results
            
        if not SKLEARN_AVAILABLE:
            results['supervised_metrics_available'] = False
            results['reason'] = "scikit-learn is not installed."
            return results
            
        results['supervised_metrics_available'] = True
        
        y_true = df[self.ground_truth_col].fillna(0).astype(int)
        y_pred = df[self.prediction_col].fillna(0).astype(int)
        
        unique_classes = np.unique(y_true)
        if len(unique_classes) < 2:
            results['reason'] = "Only one class present in ground truth labels. Cannot calculate ROC-AUC or PR-AUC."
            results['precision'] = float(precision_score(y_true, y_pred, zero_division=0))
            results['recall'] = float(recall_score(y_true, y_pred, zero_division=0))
            results['f1'] = float(f1_score(y_true, y_pred, zero_division=0))
            results['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()
            return results
            
        results['precision'] = float(precision_score(y_true, y_pred, zero_division=0))
        results['recall'] = float(recall_score(y_true, y_pred, zero_division=0))
        results['f1'] = float(f1_score(y_true, y_pred, zero_division=0))
        results['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()
        
        if self.score_col in df.columns:
            y_score = df[self.score_col].fillna(0)
            try:
                results['roc_auc'] = float(roc_auc_score(y_true, y_score))
                results['pr_auc'] = float(average_precision_score(y_true, y_score))
            except Exception as e:
                results['auc_error'] = str(e)
                
        # Calculate overlap
        true_positives = ((y_true == 1) & (y_pred == 1)).sum()
        results['true_positives'] = int(true_positives)
        results['overlap_percentage'] = float((true_positives / y_true.sum()) * 100) if y_true.sum() > 0 else 0.0
                
        return results
