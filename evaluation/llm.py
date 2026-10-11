from typing import Dict, Any, List
from agents.validators import run_deterministic_audit, AuditResult

class LLMEvaluator:
    """
    Evaluates LLM-generated SARs using deterministic fact-checking logic.
    Reuses Phase 9 validators to measure exact factual adherence.
    """
    def __init__(self):
        pass
        
    def evaluate_sar(self, evidence: dict, narrative: str) -> Dict[str, Any]:
        """
        Evaluate a single SAR narrative against its evidence package.
        Returns metrics on factual accuracy.
        """
        audit_result: AuditResult = run_deterministic_audit(evidence, narrative)
        
        # Calculate coverage: how much of the evidence was correctly reported
        # We can approximate this by (checks_passed / checks_run)
        coverage_percentage = (audit_result.checks_passed / audit_result.checks_run) * 100 if audit_result.checks_run > 0 else 0.0
        
        results = {
            "overall_passed": audit_result.overall_passed,
            "checks_run": audit_result.checks_run,
            "checks_passed": audit_result.checks_passed,
            "checks_failed": audit_result.checks_failed,
            "evidence_coverage_percentage": float(coverage_percentage),
            "unsupported_claims_count": len(audit_result.unsupported_claims),
            "missing_evidence_count": len(audit_result.missing_evidence),
            "discrepancies": [d.model_dump() for d in audit_result.discrepancies],
            "methodology": "Deterministic factual validation based on exact string matching against evidence payload."
        }
        
        return results
        
    def evaluate_batch(self, sar_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a batch of SARs.
        Expects a list of dicts with 'evidence' and 'narrative' keys.
        """
        if not sar_records:
            return {"error": "Empty batch provided for evaluation."}
            
        total_sars = len(sar_records)
        passed = 0
        total_checks = 0
        total_passed = 0
        total_unsupported = 0
        total_missing = 0
        
        for record in sar_records:
            res = self.evaluate_sar(record.get('evidence', {}), record.get('narrative', ''))
            if res.get('overall_passed'):
                passed += 1
            total_checks += res.get('checks_run', 0)
            total_passed += res.get('checks_passed', 0)
            total_unsupported += res.get('unsupported_claims_count', 0)
            total_missing += res.get('missing_evidence_count', 0)
            
        return {
            "total_sars_evaluated": total_sars,
            "sars_passed_audit": passed,
            "pass_rate_percentage": float((passed / total_sars) * 100),
            "average_evidence_coverage": float((total_passed / total_checks) * 100) if total_checks > 0 else 0.0,
            "total_unsupported_claims": total_unsupported,
            "total_missing_evidence": total_missing,
            "limitations": "Does not measure stylistic quality or subjective reasoning. Only counts deterministic presence of expected facts."
        }
