from .state import InvestigationState, AgentStatus
from .investigator_agent import InvestigatorAgent
from .sar_writer_agent import SarWriterAgent
from .auditor_agent import AuditorAgent

class SupervisorAgent:
    """
    AGENT 4 - SUPERVISOR / ORCHESTRATOR
    Responsibilities: Coordinate agents, manage state transitions, determine loop completion.
    """
    def __init__(self, max_revisions: int = 2):
        self.investigator = InvestigatorAgent()
        self.writer = SarWriterAgent()
        self.auditor = AuditorAgent()
        self.max_revisions = max_revisions
        
    def run_investigation(self, evidence_package: dict) -> InvestigationState:
        """
        Runs the full state machine pipeline.
        Returns the final state.
        """
        state = InvestigationState(
            transaction_id=str(evidence_package.get("transaction_id", "UNKNOWN")),
            evidence_package=evidence_package,
            status=AgentStatus.INVESTIGATING
        )
        
        revisions = 0
        
        while state.status not in (AgentStatus.COMPLETED, AgentStatus.FAILED):
            if state.status == AgentStatus.INVESTIGATING:
                state = self.investigator.execute(state)
            
            elif state.status in (AgentStatus.WRITING, AgentStatus.REVISING):
                if state.status == AgentStatus.REVISING:
                    revisions += 1
                    if revisions > self.max_revisions:
                        state.errors.append("Supervisor Error: Max revisions reached. Unable to pass audit.")
                        state.status = AgentStatus.FAILED
                        break
                state = self.writer.execute(state)
                
            elif state.status == AgentStatus.AUDITING:
                state = self.auditor.execute(state)
                
            else:
                # Fallback for unexpected states
                state.errors.append(f"Supervisor Error: Unknown state {state.status}")
                state.status = AgentStatus.FAILED
                
        return state
