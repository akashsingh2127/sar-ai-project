from .base_agent import BaseAgent
from .state import InvestigationState, AgentStatus
from .llm_client import call_llm

class AuditorAgent(BaseAgent):
    """
    AGENT 3 - AUDITOR
    Responsibilities: Compare narrative against evidence, identify inconsistencies/hallucinations.
    """
    def execute(self, state: InvestigationState) -> InvestigationState:
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
            result = call_llm(prompt)
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
