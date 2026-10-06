from .base_agent import BaseAgent
from .state import InvestigationState, AgentStatus
from llm.factory import get_llm_provider

class SarWriterAgent(BaseAgent):
    """
    AGENT 2 - SAR WRITER
    Responsibilities: Generate structured SAR narrative using only supplied evidence.
    """
    def execute(self, state: InvestigationState) -> InvestigationState:
        from .models import StructuredSAR, ReportStatus
        import uuid
        
        evidence = state.evidence_package
        investigator_context = state.investigator_summary
        feedback = state.audit_feedback
        
        prompt = f"""
        You are a financial compliance officer.
        Generate the text for a Suspicious Activity Report (SAR) narrative and a short summary based on the following evidence and investigation context.
        
        CRITICAL RULES:
        1. Only use the supplied evidence. Do not invent facts or unsupported claims.
        2. Correctly identify the transaction ID, amount, and dates from the evidence.
        3. Produce professional, compliance-oriented language.
        4. Use phrases like "the system detected..." or "the available evidence indicates...".
        5. Provide the output in exactly three sections separated by "---":
           Section 1: A brief suspicious activity summary.
           Section 2: The full narrative.
           Section 3: Behavior analysis.
        
        Transaction ID: {evidence.get('transaction_details', {}).get('transaction_id', 'UNKNOWN')}
        Amount: {evidence.get('transaction_details', {}).get('amount', 'UNKNOWN')}
        Date: {evidence.get('transaction_details', {}).get('timestamp', 'UNKNOWN')}
        Risk Score: {evidence.get('risk_score', 'UNKNOWN')}
        
        Investigation Context:
        {investigator_context}
        """
        
        if feedback:
            prompt += f"\n\nPrevious Audit Feedback to address (MUST FIX DISCREPANCIES):\n{feedback}"
            
        try:
            provider = get_llm_provider()
            result = provider.generate(prompt)
            if not result or "LLM Connection Failed" in result:
                raise ValueError("Malformed or empty LLM output from SAR Writer")
                
            parts = result.split("---")
            if len(parts) >= 3:
                summary = parts[0].strip()
                narrative = parts[1].strip()
                behavior = parts[2].strip()
            else:
                summary = "Generated summary."
                narrative = result.strip()
                behavior = "Generated behavior analysis."
                
            state.draft_narrative = narrative
            
            # Construct StructuredSAR
            sar_id = f"SAR-{uuid.uuid4().hex[:8].upper()}"
            sender = evidence.get("transaction_details", {}).get("sender", "UNKNOWN")
            
            structured_sar = StructuredSAR(
                sar_id=sar_id,
                investigation_id=state.transaction_id,
                subject_entity=str(sender),
                transaction_details=evidence.get("transaction_details", {}),
                detected_typologies=evidence.get("typologies", []),
                risk_score=float(evidence.get("risk_score", 0.0)),
                supporting_evidence=evidence.get("anomaly_signals", {}),
                suspicious_activity_summary=summary,
                narrative=narrative,
                suspicious_behavior=behavior
            )
            state.structured_sar = structured_sar
            state.status = AgentStatus.AUDITING
        except Exception as e:
            state.errors.append(str(e))
            state.status = AgentStatus.FAILED
            
        return state
