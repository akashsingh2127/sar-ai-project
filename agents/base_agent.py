from abc import ABC, abstractmethod
from .state import InvestigationState

class BaseAgent(ABC):
    @abstractmethod
    def execute(self, state: InvestigationState) -> InvestigationState:
        """
        Execute the agent's logic on the current state.
        Returns the updated state.
        """
        pass
