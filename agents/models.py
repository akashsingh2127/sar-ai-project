from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum

class ReviewerStatus(str, Enum):
    AWAITING_REVIEW = "AWAITING_HUMAN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"

class ReportStatus(str, Enum):
    GENERATED = "GENERATED"
    FACT_CHECK_FAILED = "FACT_CHECK_FAILED"
    AUDITOR_FLAGGED = "AUDITOR_FLAGGED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class StructuredSAR(BaseModel):
    sar_id: str
    investigation_id: str
    generated_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Metadata
    model_provider: str = "UNKNOWN"
    dataset_reference: str = "UNKNOWN"
    
    # Statuses
    report_status: ReportStatus = ReportStatus.GENERATED
    reviewer_status: ReviewerStatus = ReviewerStatus.AWAITING_REVIEW
    validation_status: str = "PENDING"
    
    # Evidence & Facts (Copied directly from EvidencePackage)
    subject_entity: str
    transaction_details: Dict[str, Any]
    detected_typologies: List[Dict[str, Any]]
    risk_score: float
    supporting_evidence: Dict[str, Any]
    
    # Generated Narrative (from LLM)
    suspicious_activity_summary: str
    narrative: str
    suspicious_behavior: str
    
    # Audit Result
    audit_result: Optional[Dict[str, Any]] = None
    
    # Disclaimer
    disclaimer: str = "AI-generated SAR research/prototype narrative. NOT a regulatory filing. For research/investigative assistance only."
    
    def to_json(self) -> str:
        return self.model_dump_json(indent=2)
        
    def to_txt(self) -> str:
        lines = [
            "===========================================================",
            f"SAR RESEARCH PROTOTYPE REPORT - ID: {self.sar_id}",
            "===========================================================",
            f"DISCLAIMER: {self.disclaimer}",
            "-----------------------------------------------------------",
            f"Generated: {self.generated_timestamp}",
            f"Status: {self.report_status} | Review: {self.reviewer_status}",
            f"Subject/Entity: {self.subject_entity}",
            f"Risk Score: {self.risk_score}",
            "",
            "--- SUSPICIOUS ACTIVITY SUMMARY ---",
            self.suspicious_activity_summary,
            "",
            "--- BEHAVIOR ANALYSIS ---",
            self.suspicious_behavior,
            "",
            "--- NARRATIVE ---",
            self.narrative,
            "",
            "--- TRANSACTION DETAILS ---",
            str(self.transaction_details),
            "",
            "--- DETECTED TYPOLOGIES ---",
            str(self.detected_typologies)
        ]
        if self.audit_result:
            lines.extend([
                "",
                "--- AUDIT RESULT ---",
                f"Validation Status: {self.audit_result.get('validation_status')}",
                f"Discrepancies: {len(self.audit_result.get('discrepancies', []))}"
            ])
        return "\n".join(lines)
