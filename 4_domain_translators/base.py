# THE MRIDANSH - Domain Translators Base Contract
# Module: 4_domain_translators/base.py
# AETHER-MRID1607X Core Engine

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class DomainInput:
    """
    Standardized Input Contract for Domain Translators.

    Encapsulates estimated soil state tensors, optional spatial masks,
    uncertainty measures, and geospatial provenance for translation.

    Required Fields:
      soil_state: np.ndarray
          Primary physical soil state array (e.g. Volumetric Soil Moisture theta, m3/m3).
          Must have at least 2 spatial dimensions (H, W).

    Declared Physical Semantics:
      state_variable: str (default: "volumetric_soil_moisture")
          Physical quantity represented by soil_state.
      unit: str (default: "m3/m3")
          Physical unit of measurement.

    Optional Integrity & Quality Fields:
      valid_data_mask: Optional[np.ndarray] (default: None)
          Boolean mask where True = valid observation, False = invalid (cloud, nodata, shadow).
          If supplied, must have identical shape to soil_state.
      uncertainty: Optional[Union[float, np.ndarray]] (default: None)
          Scalar variance or per-pixel uncertainty tensor (e.g. EnKF posterior ensemble variance).
      uncertainty_type: Optional[str] (default: None)
          Specification of uncertainty representation: 'variance', 'std', 'ensemble_spread', etc.

    Optional Geospatial Metadata (Preserved from Ingestion/Fusion):
      crs: Optional[str] (default: None)
          Coordinate Reference System (e.g. 'EPSG:32645').
      transform: Optional[Tuple[float, float, float, float, float, float]] (default: None)
          6-element GDAL affine transform.
      bounds: Optional[Tuple[float, float, float, float]] (default: None)
          Geospatial bounding coordinates (min_x, min_y, max_x, max_y).
      resolution: Optional[Tuple[float, float]] (default: None)
          Ground sample resolution tuple (res_x, res_y) in CRS units.
      acquisition_datetime: Optional[str] (default: None)
          ISO 8601 acquisition timestamp string.
      provenance: Optional[Dict[str, Any]] (default: None)
          Upstream STAC metadata, asset keys, and processing lineage.

    Optional Contextual Auxiliary Data:
      ndvi: Optional[np.ndarray] (default: None)
          Optical vegetation index array for agronomic biomass blending.
      dry_density_g_cm3: Optional[float] (default: None)
          Soil dry bulk density in g/cm3 for geotechnical bearing capacity.
      extra_parameters: Dict[str, Any] = field(default_factory=dict)
          Extensible dictionary for caller-supplied domain arguments.
    """

    soil_state: np.ndarray
    state_variable: str = "volumetric_soil_moisture"
    unit: str = "m3/m3"

    valid_data_mask: Optional[np.ndarray] = None
    uncertainty: Optional[Union[float, np.ndarray]] = None
    uncertainty_type: Optional[str] = None

    crs: Optional[str] = None
    transform: Optional[Tuple[float, float, float, float, float, float]] = None
    bounds: Optional[Tuple[float, float, float, float]] = None
    resolution: Optional[Tuple[float, float]] = None
    acquisition_datetime: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None

    ndvi: Optional[np.ndarray] = None
    dry_density_g_cm3: Optional[float] = None
    extra_parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # 1. Soil State Validation
        if not isinstance(self.soil_state, np.ndarray):
            raise TypeError(
                f"soil_state must be a numpy.ndarray, got {type(self.soil_state).__name__}."
            )

        if self.soil_state.ndim < 2:
            raise ValueError(
                f"soil_state must have at least 2 spatial dimensions (H, W), "
                f"got shape {self.soil_state.shape} (ndim={self.soil_state.ndim})."
            )

        # 2. Validity Mask Validation
        if self.valid_data_mask is not None:
            if not isinstance(self.valid_data_mask, np.ndarray):
                raise TypeError(
                    f"valid_data_mask must be a numpy.ndarray, got {type(self.valid_data_mask).__name__}."
                )
            if self.valid_data_mask.dtype != bool and self.valid_data_mask.dtype != np.bool_:
                raise ValueError(
                    f"valid_data_mask must have boolean dtype, got {self.valid_data_mask.dtype}."
                )
            if self.valid_data_mask.shape != self.soil_state.shape:
                raise ValueError(
                    f"valid_data_mask shape {self.valid_data_mask.shape} must match "
                    f"soil_state shape {self.soil_state.shape}."
                )

        # 3. Numeric Finiteness Verification
        if self.valid_data_mask is None:
            if not np.isfinite(self.soil_state).all():
                raise ValueError(
                    "soil_state contains non-finite values (NaN or Inf) without an explicit valid_data_mask."
                )
        else:
            valid_pixels = self.soil_state[self.valid_data_mask]
            if len(valid_pixels) > 0 and not np.isfinite(valid_pixels).all():
                raise ValueError(
                    "soil_state contains non-finite values (NaN or Inf) within unmasked valid pixels."
                )

        # 4. Uncertainty Validation
        if self.uncertainty is not None:
            if isinstance(self.uncertainty, (int, float)):
                if not math.isfinite(self.uncertainty) or self.uncertainty < 0:
                    raise ValueError(
                        f"Uncertainty scalar must be finite and non-negative, got {self.uncertainty}."
                    )
            elif isinstance(self.uncertainty, np.ndarray):
                if not np.isfinite(self.uncertainty).all() or (self.uncertainty < 0).any():
                    raise ValueError(
                        "Uncertainty array must contain finite, non-negative values."
                    )
            else:
                raise TypeError(
                    f"uncertainty must be a float or np.ndarray, got {type(self.uncertainty).__name__}."
                )

        # 5. NDVI Auxiliary Validation
        if self.ndvi is not None:
            if not isinstance(self.ndvi, np.ndarray):
                raise TypeError(f"ndvi must be a numpy.ndarray, got {type(self.ndvi).__name__}.")
            if self.ndvi.shape != self.soil_state.shape:
                raise ValueError(
                    f"ndvi shape {self.ndvi.shape} must match soil_state shape {self.soil_state.shape}."
                )

        # 6. Dry Density Auxiliary Validation
        if self.dry_density_g_cm3 is not None:
            if not isinstance(self.dry_density_g_cm3, (int, float)):
                raise TypeError(
                    f"dry_density_g_cm3 must be numeric, got {type(self.dry_density_g_cm3).__name__}."
                )
            if not math.isfinite(self.dry_density_g_cm3) or self.dry_density_g_cm3 <= 0:
                raise ValueError(
                    f"dry_density_g_cm3 must be positive and finite, got {self.dry_density_g_cm3}."
                )

        # 7. Spatial Bounds Validation
        if self.bounds is not None:
            if not (isinstance(self.bounds, tuple) and len(self.bounds) == 4):
                raise ValueError(
                    f"bounds must be a 4-element tuple (min_x, min_y, max_x, max_y), got {self.bounds}."
                )
            min_x, min_y, max_x, max_y = self.bounds
            if min_x >= max_x or min_y >= max_y:
                raise ValueError(
                    f"Invalid bounds coordinates: min must be strictly less than max, got {self.bounds}."
                )

        # 8. Transform Validation
        if self.transform is not None:
            if not (isinstance(self.transform, tuple) and len(self.transform) == 6):
                raise ValueError(
                    f"transform must be a 6-element tuple, got {self.transform}."
                )

        # 9. Resolution Validation
        if self.resolution is not None:
            if not (isinstance(self.resolution, tuple) and len(self.resolution) == 2):
                raise ValueError(
                    f"resolution must be a 2-element tuple (res_x, res_y), got {self.resolution}."
                )
            res_x, res_y = self.resolution
            if res_x <= 0 or res_y <= 0 or not math.isfinite(res_x) or not math.isfinite(res_y):
                raise ValueError(
                    f"resolution elements must be positive finite floats, got {self.resolution}."
                )


@dataclass
class DomainOutput:
    """
    Standardized Output Contract for Domain Translators.

    Encapsulates translated engineering/agronomic metrics, preserved
    spatial metadata, valid data masks, and scientific caveats.

    Required Fields:
      domain: str
          Domain identifier: 'agriculture', 'civil', etc.
      metrics: Dict[str, Any]
          Dictionary of domain-specific translated variables (arrays, floats, strings).

    Optional Fields:
      valid_data_mask: Optional[np.ndarray] (default: None)
          Boolean mask reflecting valid pixels in translated metric rasters.
      metadata: Dict[str, Any] = field(default_factory=dict)
          Preserved spatial coordinates, CRS, resolution, and timestamps.
      uncertainty: Optional[Dict[str, Any]] (default: None)
          Translated uncertainty metrics, confidence bounds, or reliability scores.
      warnings: List[str] = field(default_factory=list)
          Audit notices, uncalibrated heuristic warnings, or out-of-domain flags.
    """

    domain: str
    metrics: Dict[str, Any]
    valid_data_mask: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    uncertainty: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.domain, str) or not self.domain.strip():
            raise ValueError("domain must be a non-empty string identifier.")
        if not isinstance(self.metrics, dict):
            raise TypeError(f"metrics must be a dictionary, got {type(self.metrics).__name__}.")

    # --- Dictionary Emulation for Full Backward Compatibility ---

    def __getitem__(self, key: str) -> Any:
        if key in self.metrics:
            return self.metrics[key]
        if key in self.__dict__:
            return getattr(self, key)
        raise KeyError(f"Key '{key}' not found in DomainOutput metrics or attributes.")

    def __contains__(self, key: str) -> bool:
        return key in self.metrics or key in self.__dict__

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        """Returns a flat dictionary containing all output fields and metrics."""
        res: Dict[str, Any] = {
            "domain": self.domain,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "warnings": self.warnings,
        }
        if self.valid_data_mask is not None:
            res["valid_data_mask"] = self.valid_data_mask
        if self.uncertainty is not None:
            res["uncertainty"] = self.uncertainty
        # Include metrics at top level for drop-in backward compatibility with legacy consumers
        for k, v in self.metrics.items():
            if k not in res:
                res[k] = v
        return res


class BaseDomainTranslator(ABC):
    """
    Abstract Base Class for Domain-Specific Soil State Translators.

    Subclasses must implement `translate`. The interface supports both:
      1. Modern structured input via `DomainInput` dataclass.
      2. Legacy NumPy array inputs via `normalize_input`.
    """

    @abstractmethod
    def translate(
        self,
        soil_input: Union[DomainInput, np.ndarray],
        **kwargs: Any,
    ) -> Union[DomainOutput, Dict[str, Any]]:
        """
        Translates raw/estimated soil state into domain-specific metrics.

        Parameters:
          soil_input: DomainInput dataclass or raw np.ndarray soil state matrix.
          **kwargs: Additional contextual parameters (e.g. ndvi, dry_density_g_cm3).

        Returns:
          DomainOutput containing domain metrics, metadata, and scientific notices.
        """
        pass

    @staticmethod
    def normalize_input(
        soil_input: Union[DomainInput, np.ndarray],
        **kwargs: Any,
    ) -> DomainInput:
        """
        Normalizes a loose array or DomainInput into a validated DomainInput instance.
        """
        if isinstance(soil_input, DomainInput):
            return soil_input
        elif isinstance(soil_input, np.ndarray):
            known_keys = {
                "state_variable", "unit", "valid_data_mask", "uncertainty",
                "uncertainty_type", "crs", "transform", "bounds", "resolution",
                "acquisition_datetime", "provenance", "ndvi", "dry_density_g_cm3"
            }
            extra = {k: v for k, v in kwargs.items() if k not in known_keys}
            return DomainInput(
                soil_state=soil_input,
                state_variable=kwargs.get("state_variable", "volumetric_soil_moisture"),
                unit=kwargs.get("unit", "m3/m3"),
                valid_data_mask=kwargs.get("valid_data_mask"),
                uncertainty=kwargs.get("uncertainty"),
                uncertainty_type=kwargs.get("uncertainty_type"),
                crs=kwargs.get("crs"),
                transform=kwargs.get("transform"),
                bounds=kwargs.get("bounds"),
                resolution=kwargs.get("resolution"),
                acquisition_datetime=kwargs.get("acquisition_datetime"),
                provenance=kwargs.get("provenance"),
                ndvi=kwargs.get("ndvi"),
                dry_density_g_cm3=kwargs.get("dry_density_g_cm3"),
                extra_parameters=extra,
            )
        else:
            raise TypeError(
                f"soil_input must be a DomainInput or np.ndarray, got {type(soil_input).__name__}."
            )
