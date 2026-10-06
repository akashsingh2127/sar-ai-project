from .base_agent import BaseAgent
from .state import InvestigationState, AgentStatus
from llm.factory import get_llm_provider
import re

class AuditorAgent(BaseAgent):
    """
    AGENT 3 - AUDITOR
    Responsibilities: Compare narrative against evidence deterministically, then identify inconsistencies/hallucinations via LLM.
    """
    
    def _deterministic_fact_check(self, evidence: dict, narrative: str) -> list[str]:
        """
        Deterministically verifies that key facts from the evidence are present in the narrative.
        Uses the new robust validation framework.
        """
        from .validators import run_deterministic_audit
        
        audit_result = run_deterministic_audit(evidence, narrative)
        
        discrepancies = []
        if not audit_result.overall_passed:
            for d in audit_result.discrepancies:
                discrepancies.append(d.description)
                
        return discrepancies

    def execute(self, state: InvestigationState) -> InvestigationState:
        # 1. Deterministic Check
        det_discrepancies = self._deterministic_fact_check(state.evidence_package, state.draft_narrative or "")
        
        if det_discrepancies:
            state.is_verified = False
            state.audit_feedback = "DETERMINISTIC DISCREPANCY: " + "; ".join(det_discrepancies)
            state.status = AgentStatus.REVISING
            return state

        # 2. LLM Check
        prompt = f"""
        You are a Senior AML Auditor.
        TASK: Verify if the generated SAR narrative accurately reflects the structured evidence without hallucinating facts.
        
        EVIDENCE PACKAGE: 
        {state.evidence_package}
        
        NARRATIVE TO AUDIT: 
        {state.draft_narrative}
        
        Check for:
        1. Correct Transaction ID, Amount, and Dates.
        2. Verification of typology statements (do they match the evidence?).
        3. Any 'hallucinations' (facts not in the data).
        
        If accurate and completely supported by evidence, reply exactly with 'VERIFIED'.
        If there are discrepancies or hallucinations, reply with 'DISCREPANCY:' followed by the reasons.
        """
        
        try:
            provider = get_llm_provider()
            result = provider.generate(prompt)
            if not result or "LLM Connection Failed" in result:
                raise ValueError("Malformed LLM output from Auditor")
                
            if result.strip().upper().startswith("VERIFIED"):
                state.is_verified = True
                state.audit_feedback = None
                state.status = AgentStatus.COMPLETED
            else:
                state.is_verified = False
                state.audit_feedback = result
                state.status = AgentStatus.REVISING
        except Exception as e:
            state.errors.append(str(e))
            state.status = AgentStatus.FAILED
            
        return state
