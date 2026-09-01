# THE MRIDANSH / Base.py

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseDomainTranslator(ABC):
    """Abstract Base Class for Domain Specific Soil State Translators."""

    @abstractmethod
    def translate(self, soil_state_matrix: np.ndarray, **kwargs) -> dict[str, Any]:
        """Translates raw state predictions into domain specific metrics."""
