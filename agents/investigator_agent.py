from .base_agent import BaseAgent
from .state import InvestigationState, AgentStatus
from .llm_client import call_llm

class InvestigatorAgent(BaseAgent):
    """
    AGENT 1 - INVESTIGATOR / EVIDENCE AGENT
    Responsibilities: Inspect evidence, summarize signals, prepare context.
    """
    def execute(self, state: InvestigationState) -> InvestigationState:
        if not state.evidence_package:
            state.errors.append("Investigator Error: Missing evidence package.")
            state.status = AgentStatus.FAILED
            return state

        prompt = f"""
        You are an AML Investigator. Review the following structured evidence package and summarize the suspicious signals.
        Do not invent any facts. Only use the provided evidence.
        
        Evidence:
        {state.evidence_package}
        
        Provide a concise investigation context summary detailing the suspicious signals, relevant entities, and reasons for flagging.
        """
        
        try:
            summary = call_llm(prompt)
            if not summary or "LLM Connection Failed" in summary:
                raise ValueError("Malformed or empty LLM output from Investigator")
                
            state.investigator_summary = summary
            state.status = AgentStatus.WRITING
        except Exception as e:
            state.errors.append(str(e))
            state.status = AgentStatus.FAILED
            
        return state
