from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentStatus(Enum):
    PENDING = "PENDING"
    INVESTIGATING = "INVESTIGATING"
    WRITING = "WRITING"
    AUDITING = "AUDITING"
    REVISING = "REVISING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class InvestigationState:
    """Structured state passed between agents during the investigation lifecycle."""
    transaction_id: str
    evidence_package: Dict[str, Any]
    
    investigator_summary: Optional[str] = None
    draft_narrative: Optional[str] = None
    structured_sar: Optional[Any] = None # Will hold StructuredSAR, typed as Any to avoid circular import if needed
    audit_feedback: Optional[str] = None
    
    is_verified: bool = False
    status: AgentStatus = AgentStatus.PENDING
    errors: List[str] = field(default_factory=list)
