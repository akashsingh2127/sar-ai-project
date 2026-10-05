from .base_agent import BaseAgent
from .state import InvestigationState, AgentStatus
from .llm_client import call_llm

class SarWriterAgent(BaseAgent):
    """
    AGENT 2 - SAR WRITER
    Responsibilities: Generate structured SAR narrative using only supplied evidence.
    """
    def execute(self, state: InvestigationState) -> InvestigationState:
        evidence = state.evidence_package
        investigator_context = state.investigator_summary
        feedback = state.audit_feedback
        
        prompt = f"""
        You are a financial compliance officer.
        Generate a formal Suspicious Activity Report (SAR) narrative based on the following evidence and investigation context.
        
        CRITICAL RULES:
        1. Only use the supplied evidence. Do not invent facts or unsupported claims.
        2. Correctly identify the transaction ID, amount, and dates from the evidence.
        3. Produce professional, compliance-oriented language.
        
        Transaction ID: {evidence.get('transaction_id', 'UNKNOWN')}
        Amount: {evidence.get('amount', 'UNKNOWN')}
        Date: {evidence.get('timestamp', 'UNKNOWN')}
        Risk Score: {evidence.get('risk_score', 'UNKNOWN')}
        Typology: {evidence.get('typology', 'UNKNOWN')}
        
        Investigation Context:
        {investigator_context}
        """
        
        if feedback:
            prompt += f"\n\nPrevious Audit Feedback to address (MUST FIX DISCREPANCIES):\n{feedback}"
            
        try:
            narrative = call_llm(prompt)
            if not narrative or "LLM Connection Failed" in narrative:
                raise ValueError("Malformed or empty LLM output from SAR Writer")
                
            state.draft_narrative = narrative
            state.status = AgentStatus.AUDITING
        except Exception as e:
            state.errors.append(str(e))
            state.status = AgentStatus.FAILED
            
        return state
