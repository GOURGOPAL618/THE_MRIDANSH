# THE MRIDANSH / Base.py

from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any

class BaseDomainTranslator(ABC):
    """Abstract Base Class for Domain Specific Soil State Translators."""

    @abstractmethod
    def translate(self, soil_state_matrix: np.ndarray, **kwargs) -> Dict[str, Any]:
        """Translates raw state predictions into domain specific metrics."""
        pass
    