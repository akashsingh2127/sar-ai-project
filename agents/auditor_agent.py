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
        """
        discrepancies = []
        if not narrative:
            return ["Narrative is empty."]
            
        narrative_upper = narrative.upper()
        
        # Helper to safely get nested dict values
        def get_val(key):
            # Check root (for tests)
            if key in evidence:
                return evidence[key]
            # Check transaction_details (for production)
            if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
                return evidence["transaction_details"].get(key)
            return None

        # Check Transaction ID
        txn_id = get_val("transaction_id")
        if txn_id and str(txn_id).upper() not in narrative_upper:
            discrepancies.append(f"Missing Transaction ID: {txn_id}")
            
        # Check Amount
        amount = get_val("amount")
        if amount is not None:
            # Check for standard formatting (e.g. 50000 -> 50,000 or 50000.00)
            amt_str = str(amount)
            # Remove trailing .0 from floats
            if amt_str.endswith(".0"):
                amt_str = amt_str[:-2]
            
            # Simple check if the raw number or formatted number is in the text
            formatted_amt = f"{float(amount):,.2f}"
            formatted_amt_no_cents = f"{float(amount):,.0f}"
            
            if amt_str not in narrative and formatted_amt not in narrative and formatted_amt_no_cents not in narrative:
                discrepancies.append(f"Missing or incorrect Amount: {amount}")

        # Check Timestamp/Date
        timestamp = get_val("timestamp")
        if timestamp:
            # Usually a date string like YYYY-MM-DD
            ts_str = str(timestamp).split("T")[0] # Just the date part
            if ts_str not in narrative:
                discrepancies.append(f"Missing Timestamp/Date: {ts_str}")
                
        # Check Customer/Sender ID
        sender = get_val("sender")
        if sender and str(sender).upper() != "UNKNOWN":
            if str(sender).upper() not in narrative_upper:
                discrepancies.append(f"Missing Sender/Customer ID: {sender}")

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
