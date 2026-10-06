from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class StorageProvider(ABC):
    """
    Abstract base class defining the persistence layer for SAR-AI.
    """
    @abstractmethod
    def save_investigation(self, inv_id: str, status: str):
        pass
        
    @abstractmethod
    def save_sar_report(self, sar_id: str, inv_id: str, sar_data: Dict[str, Any]):
        pass
        
    @abstractmethod
    def log_audit(self, entity_id: str, entity_type: str, action: str, status: str, details: Optional[Dict[str, Any]] = None):
        pass
        
    @abstractmethod
    def get_sar_report(self, sar_id: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_all_sars(self) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_audit_history(self) -> List[Dict[str, Any]]:
        pass
