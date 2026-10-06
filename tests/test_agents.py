import pytest
import os
from agents.state import InvestigationState, AgentStatus
from agents.investigator_agent import InvestigatorAgent
from agents.sar_writer_agent import SarWriterAgent
from agents.auditor_agent import AuditorAgent
from agents.supervisor_agent import SupervisorAgent

@pytest.fixture
def sample_evidence():
    return {
        "transaction_id": "TXN-123",
        "amount": 50000,
        "timestamp": "2024-03-01",
        "risk_score": 88.5,
        "typology": "High-Value Anomaly"
    }

def test_agent_state_initialization(sample_evidence):
    state = InvestigationState(
        transaction_id="TXN-123",
        evidence_package=sample_evidence
    )
    assert state.status == AgentStatus.PENDING
    assert state.is_verified is False
    assert state.errors == []

def test_missing_evidence():
    state = InvestigationState(transaction_id="TXN-999", evidence_package={})
    agent = InvestigatorAgent()
    state = agent.execute(state)
    assert state.status == AgentStatus.FAILED
    assert "Missing evidence package" in state.errors[0]

def test_agent_transitions_success(monkeypatch, sample_evidence):
    # Test Investigator
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "Suspicious large round-number transfer.")
    state = InvestigationState(transaction_id="TXN-123", evidence_package=sample_evidence)
    
    agent_inv = InvestigatorAgent()
    state = agent_inv.execute(state)
    
    assert state.status == AgentStatus.WRITING
    assert state.investigator_summary == "Suspicious large round-number transfer."
    
    # Test Writer
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "Formal SAR Narrative Draft for TXN-123. Amount is 50000. Date is 2024-03-01.")
    agent_writer = SarWriterAgent()
    state = agent_writer.execute(state)
    
    assert state.status == AgentStatus.AUDITING
    assert state.draft_narrative == "Formal SAR Narrative Draft for TXN-123. Amount is 50000. Date is 2024-03-01."
    
    # Test Auditor (Verified)
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "VERIFIED: The narrative matches the evidence.")
    agent_auditor = AuditorAgent()
    state = agent_auditor.execute(state)
    
    assert state.status == AgentStatus.COMPLETED
    assert state.is_verified is True
    assert state.audit_feedback is None

def test_agent_transitions_revision_loop(monkeypatch, sample_evidence):
    # Setup initial state ready for Auditor
    state = InvestigationState(
        transaction_id="TXN-123",
        evidence_package=sample_evidence,
        investigator_summary="Summary",
        draft_narrative="Bad Narrative",
        status=AgentStatus.AUDITING
    )
    
    # Auditor finds discrepancy
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "DISCREPANCY: Amount is incorrect.")
    agent_auditor = AuditorAgent()
    state = agent_auditor.execute(state)
    
    assert state.status == AgentStatus.REVISING
    assert state.is_verified is False
    assert "DISCREPANCY" in state.audit_feedback
    
    # Writer fixes it
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "Fixed Narrative.")
    agent_writer = SarWriterAgent()
    state = agent_writer.execute(state)
    
    assert state.status == AgentStatus.AUDITING
    assert state.draft_narrative == "Fixed Narrative."

def test_supervisor_orchestration_success(monkeypatch, sample_evidence):
    # The supervisor runs everything. We mock a single response for all to simplify,
    # but the auditor needs to say 'VERIFIED'.
    class MockLLMProvider:
        def __init__(self):
            self.calls = 0
        def generate(self, prompt):
            self.calls += 1
            if self.calls == 1:
                return "Investigator summary"
            elif self.calls == 2:
                return "Draft narrative TXN-123 50000 2024-03-01"
            elif self.calls == 3:
                return "VERIFIED"
            return "Unexpected"
            
    mock_instance = MockLLMProvider()
    def mock_get_llm_provider():
        return mock_instance
        
    import agents.investigator_agent
    import agents.sar_writer_agent
    import agents.auditor_agent
    monkeypatch.setattr(agents.investigator_agent, "get_llm_provider", mock_get_llm_provider)
    monkeypatch.setattr(agents.sar_writer_agent, "get_llm_provider", mock_get_llm_provider)
    monkeypatch.setattr(agents.auditor_agent, "get_llm_provider", mock_get_llm_provider)

    supervisor = SupervisorAgent()
    final_state = supervisor.run_investigation(sample_evidence)
    
    assert final_state.status == AgentStatus.COMPLETED
    assert final_state.is_verified is True

def test_supervisor_max_revisions(monkeypatch, sample_evidence):
    # Auditor always returns discrepancy, causing an infinite loop if not for supervisor max_revisions
    class MockLLMProvider:
        def __init__(self):
            self.calls = 0
        def generate(self, prompt):
            self.calls += 1
            if self.calls == 1:
                return "Investigator summary"
            elif self.calls % 2 == 0:
                return "Draft narrative TXN-123 50000 2024-03-01"
            else:
                return "DISCREPANCY: Constant error."
                
    mock_instance = MockLLMProvider()
    def mock_get_llm_provider():
        return mock_instance
        
    import agents.investigator_agent
    import agents.sar_writer_agent
    import agents.auditor_agent
    monkeypatch.setattr(agents.investigator_agent, "get_llm_provider", mock_get_llm_provider)
    monkeypatch.setattr(agents.sar_writer_agent, "get_llm_provider", mock_get_llm_provider)
    monkeypatch.setattr(agents.auditor_agent, "get_llm_provider", mock_get_llm_provider)
    
    supervisor = SupervisorAgent(max_revisions=2)
    final_state = supervisor.run_investigation(sample_evidence)
    
    assert final_state.status == AgentStatus.FAILED
    assert "Max revisions reached" in final_state.errors[0]
    
def test_malformed_llm_output(monkeypatch, sample_evidence):
    # Test Investigator getting empty output
    monkeypatch.setenv("MOCK_LLM_RESPONSE", "LLM Connection Failed: Timeout")
    state = InvestigationState(transaction_id="TXN-123", evidence_package=sample_evidence)
    
    agent_inv = InvestigatorAgent()
    state = agent_inv.execute(state)
    
    assert state.status == AgentStatus.FAILED
    assert len(state.errors) > 0
    assert "Malformed" in state.errors[0]
