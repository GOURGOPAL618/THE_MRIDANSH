# THE MRIDANSH - DOMAIN INTEGRATION ROUTER
# Module: 4_domain_translators/domain_integrator.py
# AETHER-MRID1607X Core Engine

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

try:
    from .base import BaseDomainTranslator, DomainInput, DomainOutput
    from .agronomy_translator import (
        AgronomyHealthTranslator,
        SUPPORTED_STATE_VARIABLES,
        SUPPORTED_UNITS,
    )
    from .civil_translator import CivilLoadTranslator
except ImportError:
    from base import BaseDomainTranslator, DomainInput, DomainOutput
    from agronomy_translator import (
        AgronomyHealthTranslator,
        SUPPORTED_STATE_VARIABLES,
        SUPPORTED_UNITS,
    )
    from civil_translator import CivilLoadTranslator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class IntegrationBlockedError(Exception):
    """
    Raised when a core-engine or pipeline output cannot be converted into a domain
    soil state because no scientifically validated mapping or projection head exists.
    """
    pass


class IntegrationValidationError(ValueError):
    """
    Raised when inputs to the domain integration layer violate shape, unit, or semantic contracts.
    """
    pass


@dataclass
class IntegrationResult:
    """
    Standardized Result Container for Domain Integration Operations.

    Attributes:
      status: Execution status ('SUCCESS', 'BLOCKED', 'REJECTED').
      domain: Target domain ('agriculture', 'civil', 'both', or 'none').
      source_type: Upstream origin ('enkf', 'backbone', 'physics', 'direct', 'snapshot').
      domain_output: Translated DomainOutput instance or dict of DomainOutputs if domain='both'.
      message: Human-readable status description.
      blocked_reason: Explicit scientific rationale if conversion was blocked.
      required_evidence: Necessary empirical or algorithmic evidence required to unblock.
    """
    status: str
    domain: str
    source_type: str
    domain_output: Optional[Union[DomainOutput, Dict[str, DomainOutput]]] = None
    message: str = ""
    blocked_reason: Optional[str] = None
    required_evidence: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"

    @property
    def is_blocked(self) -> bool:
        return self.status == "BLOCKED"

    @property
    def is_rejected(self) -> bool:
        return self.status == "REJECTED"


class DomainIntegrationRouter:
    """
    Domain Integration Orchestrator and Semantic Router.

    Establishes a controlled, explicit integration boundary between upstream
    core-engine outputs (Backbone, Physics, EnKF), data-pipeline products,
    and downstream domain translators (AgronomyHealthTranslator, CivilLoadTranslator).

    Enforces the Mandatory Semantic Gate:
    1. Latent representations (B, D, H, W) are strictly blocked from being relabeled
       as physical soil moisture.
    2. Physics flux divergence outputs (cm/day) are strictly blocked from being routed
       as soil moisture content (m3/m3).
    3. EnKF posterior state outputs are routable ONLY when explicit soil moisture
       semantics and valid units (m3/m3) are established.
    4. Upstream uncertainty (e.g. EnKF posterior ensemble variance) is preserved
       honestly without false claims of downstream metric uncertainty.
    """

    def __init__(
        self,
        agronomy_translator: Optional[AgronomyHealthTranslator] = None,
        civil_translator: Optional[CivilLoadTranslator] = None,
    ):
        self.agronomy_translator = agronomy_translator or AgronomyHealthTranslator()
        self.civil_translator = civil_translator or CivilLoadTranslator()
        logging.info("Initialized DomainIntegrationRouter.")

    # ──────────────────────────────────────────────────────────────────────────
    # 1. EnKF State Estimation Integration Route (Executable)
    # ──────────────────────────────────────────────────────────────────────────

    def integrate_enkf_state(
        self,
        enkf_output: Dict[str, Any],
        domain: str = "both",
        state_variable: str = "volumetric_soil_moisture",
        unit: str = "m3/m3",
        valid_data_mask: Optional[np.ndarray] = None,
        ndvi: Optional[np.ndarray] = None,
        dry_density_g_cm3: Optional[float] = None,
        crs: Optional[str] = None,
        transform: Optional[Tuple[float, float, float, float, float, float]] = None,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        resolution: Optional[Tuple[float, float]] = None,
        acquisition_datetime: Optional[str] = None,
        provenance: Optional[Dict[str, Any]] = None,
        strict: bool = True,
    ) -> IntegrationResult:
        """
        Integrates an EnKF state estimation output dictionary into domain translators.

        Contract requirements:
          - enkf_output must contain 'posterior_soil_state' (np.ndarray with ndim >= 2).
          - enkf_output must contain 'uncertainty_variance' (scalar float).
          - state_variable must match supported soil moisture semantics.
          - unit must match supported volumetric fraction units (e.g. m3/m3).
        """
        logging.info("Integrating EnKF State Output into domain translators...")

        # 1. Validate EnKF output structure
        if not isinstance(enkf_output, dict):
            raise IntegrationValidationError(
                f"enkf_output must be a dictionary, got {type(enkf_output).__name__}."
            )

        if "posterior_soil_state" not in enkf_output:
            raise IntegrationValidationError(
                "enkf_output is missing required key 'posterior_soil_state'."
            )

        soil_arr = enkf_output["posterior_soil_state"]
        if not isinstance(soil_arr, np.ndarray):
            raise IntegrationValidationError(
                f"posterior_soil_state must be a numpy.ndarray, got {type(soil_arr).__name__}."
            )

        if soil_arr.ndim < 2:
            raise IntegrationValidationError(
                f"posterior_soil_state must have at least 2 spatial dimensions (H, W), "
                f"got shape {soil_arr.shape} (ndim={soil_arr.ndim})."
            )

        # 2. Semantic Gate: Validate variable semantics and units
        norm_var = state_variable.strip().lower()
        if norm_var not in SUPPORTED_STATE_VARIABLES:
            msg = (
                f"Unsupported state variable '{state_variable}' for EnKF domain integration. "
                f"Supported variables: {sorted(SUPPORTED_STATE_VARIABLES)}."
            )
            if strict:
                raise IntegrationValidationError(msg)
            return IntegrationResult(
                status="REJECTED", domain=domain, source_type="enkf", message=msg
            )

        norm_unit = unit.strip().lower()
        if norm_unit not in SUPPORTED_UNITS:
            msg = (
                f"Unsupported unit '{unit}' for EnKF soil moisture integration. "
                f"Expected volumetric fraction in m3/m3. Supported: {sorted(SUPPORTED_UNITS)}."
            )
            if strict:
                raise IntegrationValidationError(msg)
            return IntegrationResult(
                status="REJECTED", domain=domain, source_type="enkf", message=msg
            )

        # 3. Uncertainty Extraction (Safeguarded)
        # Note: EnKF produces scalar posterior ensemble variance.
        # SAFEGUARD: Do NOT convert variance to std dev; do NOT expand to 2D raster.
        uncertainty_val = None
        uncertainty_type = None
        if "uncertainty_variance" in enkf_output:
            raw_unc = enkf_output["uncertainty_variance"]
            if isinstance(raw_unc, (int, float, np.floating)):
                uncertainty_val = float(raw_unc)
                uncertainty_type = "ensemble_variance"
            elif raw_unc is not None:
                uncertainty_val = raw_unc
                uncertainty_type = "ensemble_variance"

        # 4. Construct Standardized DomainInput
        try:
            domain_input = DomainInput(
                soil_state=soil_arr,
                state_variable=state_variable,
                unit=unit,
                valid_data_mask=valid_data_mask,
                uncertainty=uncertainty_val,
                uncertainty_type=uncertainty_type,
                crs=crs,
                transform=transform,
                bounds=bounds,
                resolution=resolution,
                acquisition_datetime=acquisition_datetime,
                provenance=provenance,
                ndvi=ndvi,
                dry_density_g_cm3=dry_density_g_cm3,
            )
        except (ValueError, TypeError) as e:
            raise IntegrationValidationError(f"DomainInput construction failed: {e}") from e

        # 5. Route to Requested Domain
        domain_norm = domain.strip().lower()
        outputs: Dict[str, DomainOutput] = {}

        try:
            if domain_norm in ("agriculture", "both", "all"):
                outputs["agriculture"] = self.agronomy_translator.translate(domain_input)

            if domain_norm in ("civil", "both", "all"):
                outputs["civil"] = self.civil_translator.translate(domain_input)
        except (ValueError, TypeError) as e:
            raise IntegrationValidationError(f"Domain translation failed: {e}") from e

        if not outputs:
            raise IntegrationValidationError(
                f"Unsupported domain '{domain}'. Supported: 'agriculture', 'civil', 'both'."
            )

        result_payload = outputs[domain_norm] if domain_norm in outputs else outputs

        return IntegrationResult(
            status="SUCCESS",
            domain=domain_norm,
            source_type="enkf",
            domain_output=result_payload,
            message="EnKF posterior state successfully integrated and routed.",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Backbone Latent Feature Integration Route (Blocked by Semantic Gate)
    # ──────────────────────────────────────────────────────────────────────────

    def integrate_backbone_latent(
        self,
        backbone_output: Dict[str, Any],
        domain: str = "both",
        strict: bool = False,
    ) -> IntegrationResult:
        """
        Attempts to integrate Neural Backbone latent representations.

        Enforces the Semantic Gate:
        Latent embeddings have shape (B, D, H, W) with dimensionless neural activations.
        No scientifically validated projection head maps latent space to physical soil
        moisture (m3/m3). Conversion is strictly BLOCKED.
        """
        logging.warning("Evaluating Backbone Latent Feature map against Semantic Gate...")

        blocked_reason = (
            "SpatialTemporalEncoderBackbone outputs an abstract latent feature tensor of "
            "shape (B, feature_dim, H, W) with dimensionless uncalibrated activations. "
            "It does NOT represent physical volumetric soil moisture [m3/m3]."
        )
        required_evidence = (
            "Unblocking requires an architecturally defined and calibrated physical projection head "
            "(e.g. latent-to-moisture decoder head) trained against certified ground-truth in-situ "
            "soil-moisture observations (e.g. ISMN stations) with validated RMSE and bias metrics."
        )

        if strict:
            raise IntegrationBlockedError(f"{blocked_reason}\nRequired Evidence: {required_evidence}")

        return IntegrationResult(
            status="BLOCKED",
            domain=domain,
            source_type="backbone",
            domain_output=None,
            message="Latent-to-physical conversion blocked by semantic gate.",
            blocked_reason=blocked_reason,
            required_evidence=required_evidence,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Richards Physics Engine Integration Route (Blocked by Semantic Gate)
    # ──────────────────────────────────────────────────────────────────────────

    def integrate_physics_output(
        self,
        physics_output: Dict[str, Any],
        domain: str = "both",
        strict: bool = False,
    ) -> IntegrationResult:
        """
        Attempts to integrate Richards physics engine flux divergence outputs.

        Enforces the Semantic Gate:
        RichardsSoilPhysicsEngine computes water_flux and hydraulic_conductivity in cm/day,
        which are flux divergence and transport rates, NOT volumetric soil moisture states.
        Conversion is strictly BLOCKED.
        """
        logging.warning("Evaluating Richards Physics output against Semantic Gate...")

        blocked_reason = (
            "RichardsSoilPhysicsEngine produces water_flux (cm/day) and hydraulic_conductivity (cm/day), "
            "which represent hydraulic gradient flux divergence, NOT volumetric soil moisture content [m3/m3]."
        )
        required_evidence = (
            "Unblocking requires a coupled temporal state-integration solver that numerically integrates "
            "d(theta)/dt over a forward time horizon dt to update volumetric water content grids."
        )

        if strict:
            raise IntegrationBlockedError(f"{blocked_reason}\nRequired Evidence: {required_evidence}")

        return IntegrationResult(
            status="BLOCKED",
            domain=domain,
            source_type="physics",
            domain_output=None,
            message="Physics flux divergence output cannot be directly routed as soil moisture.",
            blocked_reason=blocked_reason,
            required_evidence=required_evidence,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Pipeline Snapshot Context Extraction (Helper)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def extract_pipeline_context(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely extracts contextual auxiliary information from a 2_data_pipeline snapshot.

        Extracts:
          - OPTICAL_NDVI (if present in snapshot['channels']) as a 2D float32 array.
          - 2D valid_data_mask for NDVI or combined sensor validity.
          - Snapshot provenance and geospatial lineage.

        Does NOT synthesize or invent soil moisture content from raw reflectance channels.
        """
        if not isinstance(snapshot, dict):
            raise IntegrationValidationError(
                f"snapshot must be a dictionary, got {type(snapshot).__name__}."
            )

        context: Dict[str, Any] = {
            "ndvi": None,
            "valid_data_mask": None,
            "provenance": snapshot.get("provenance"),
        }

        channels: Optional[List[str]] = snapshot.get("channels")
        fused_tensor: Optional[np.ndarray] = snapshot.get("fused_tensor")
        fused_mask: Optional[np.ndarray] = snapshot.get("fused_validity_mask")

        if channels and fused_tensor is not None and isinstance(fused_tensor, np.ndarray):
            if "OPTICAL_NDVI" in channels:
                ndvi_idx = channels.index("OPTICAL_NDVI")
                if fused_tensor.ndim == 3 and fused_tensor.shape[2] > ndvi_idx:
                    context["ndvi"] = fused_tensor[..., ndvi_idx].astype(np.float32)

                    if (
                        fused_mask is not None
                        and isinstance(fused_mask, np.ndarray)
                        and fused_mask.ndim == 3
                        and fused_mask.shape[2] > ndvi_idx
                    ):
                        context["valid_data_mask"] = fused_mask[..., ndvi_idx].astype(bool)

        return context

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Direct Physical State Route (Executable for Verified Sources)
    # ──────────────────────────────────────────────────────────────────────────

    def integrate_direct_state(
        self,
        soil_state: np.ndarray,
        domain: str = "both",
        state_variable: str = "volumetric_soil_moisture",
        unit: str = "m3/m3",
        valid_data_mask: Optional[np.ndarray] = None,
        uncertainty: Optional[Union[float, np.ndarray]] = None,
        uncertainty_type: Optional[str] = None,
        ndvi: Optional[np.ndarray] = None,
        dry_density_g_cm3: Optional[float] = None,
        crs: Optional[str] = None,
        transform: Optional[Tuple[float, float, float, float, float, float]] = None,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        resolution: Optional[Tuple[float, float]] = None,
        acquisition_datetime: Optional[str] = None,
        provenance: Optional[Dict[str, Any]] = None,
        strict: bool = True,
    ) -> IntegrationResult:
        """
        Integrates a verified physical soil state array directly into domain translators.
        """
        norm_var = state_variable.strip().lower()
        if norm_var not in SUPPORTED_STATE_VARIABLES:
            msg = f"Unsupported state variable '{state_variable}'."
            if strict:
                raise IntegrationValidationError(msg)
            return IntegrationResult(status="REJECTED", domain=domain, source_type="direct", message=msg)

        norm_unit = unit.strip().lower()
        if norm_unit not in SUPPORTED_UNITS:
            msg = f"Unsupported unit '{unit}'."
            if strict:
                raise IntegrationValidationError(msg)
            return IntegrationResult(status="REJECTED", domain=domain, source_type="direct", message=msg)

        try:
            domain_input = DomainInput(
                soil_state=soil_state,
                state_variable=state_variable,
                unit=unit,
                valid_data_mask=valid_data_mask,
                uncertainty=uncertainty,
                uncertainty_type=uncertainty_type,
                crs=crs,
                transform=transform,
                bounds=bounds,
                resolution=resolution,
                acquisition_datetime=acquisition_datetime,
                provenance=provenance,
                ndvi=ndvi,
                dry_density_g_cm3=dry_density_g_cm3,
            )
        except (ValueError, TypeError) as e:
            raise IntegrationValidationError(f"DomainInput validation failed: {e}") from e

        domain_norm = domain.strip().lower()
        outputs: Dict[str, DomainOutput] = {}

        try:
            if domain_norm in ("agriculture", "both", "all"):
                outputs["agriculture"] = self.agronomy_translator.translate(domain_input)

            if domain_norm in ("civil", "both", "all"):
                outputs["civil"] = self.civil_translator.translate(domain_input)
        except (ValueError, TypeError) as e:
            raise IntegrationValidationError(f"Domain translation failed: {e}") from e

        if not outputs:
            raise IntegrationValidationError(f"Unsupported domain '{domain}'.")

        result_payload = outputs[domain_norm] if domain_norm in outputs else outputs

        return IntegrationResult(
            status="SUCCESS",
            domain=domain_norm,
            source_type="direct",
            domain_output=result_payload,
            message="Direct physical soil state successfully integrated.",
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Unified Dispatcher / Semantic Route Entry Point
    # ──────────────────────────────────────────────────────────────────────────

    def route(
        self,
        source_type: str,
        data: Dict[str, Any],
        domain: str = "both",
        strict: bool = False,
        **kwargs: Any,
    ) -> IntegrationResult:
        """
        Unified dispatch router for all domain integration requests.

        Parameters:
          source_type: 'enkf', 'backbone', 'physics', 'direct', or 'snapshot'
          data: Source payload dictionary
          domain: 'agriculture', 'civil', or 'both'
          strict: If True, blocks and rejections raise exceptions rather than returning IntegrationResult.
          **kwargs: Additional parameters (crs, transform, ndvi, dry_density_g_cm3, etc.)
        """
        norm_source = source_type.strip().lower()

        if norm_source == "enkf":
            return self.integrate_enkf_state(
                enkf_output=data,
                domain=domain,
                strict=strict,
                **kwargs,
            )
        elif norm_source == "backbone":
            return self.integrate_backbone_latent(
                backbone_output=data,
                domain=domain,
                strict=strict,
            )
        elif norm_source == "physics":
            return self.integrate_physics_output(
                physics_output=data,
                domain=domain,
                strict=strict,
            )
        elif norm_source == "direct":
            if "soil_state" not in data:
                raise IntegrationValidationError("direct source_type requires 'soil_state' in data dictionary.")
            return self.integrate_direct_state(
                soil_state=data["soil_state"],
                domain=domain,
                strict=strict,
                **kwargs,
            )
        else:
            raise IntegrationValidationError(
                f"Unknown source_type '{source_type}'. Supported: 'enkf', 'backbone', 'physics', 'direct'."
            )
