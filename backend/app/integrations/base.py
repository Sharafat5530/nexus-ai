from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseIntegrationAdapter(ABC):
    """Abstract base class for typed business system adapters."""
    
    @property
    @abstractmethod
    def system_name(self) -> str:
        """Name of authoritative business system (e.g. 'stripe', 'fedex', 'hubspot')."""
        pass
