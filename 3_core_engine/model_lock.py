"""
AETHER-MRID1607X: CRYPTOGRAPHIC MODEL-LOCK & INTEGRITY VERIFICATION ENGINE
Part of THE MRIDANSH Core Engine (3_core_engine/model_lock.py)

Mission-Critical Model Weight & State Checkpoint Verification Mechanism.
Guarantees zero parameter drift and enforces cryptographic integrity against
bit rot, silent checkpoint corruption, and unauthorized model tampering.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AETHER.ModelLock")


class ModelIntegrityDriftError(RuntimeError):
    """Raised when a certified model weight or state checkpoint fails SHA-256 integrity verification."""
    pass


@dataclass(frozen=True)
class ModelArtifactLock:
    """
    Immutable specification of a certified model artifact.
    
    Attributes:
        name: Human-readable identifier.
        relative_path: Repository-relative path to the checkpoint artifact.
        golden_sha256: Cryptographically certified SHA-256 hexadecimal hash.
        byte_size: Expected binary file size in bytes.
        description: Functional description of the checkpoint subsystem.
    """
    name: str
    relative_path: str
    golden_sha256: str
    byte_size: int
    description: str


# ==============================================================================
# CERTIFIED GOLDEN HASHES LEDGER (Audited from Notebook 12 & Storage Manifests)
# ==============================================================================
CERTIFIED_MODEL_LOCK_REGISTRY: Dict[str, ModelArtifactLock] = {
    "pinn_richards_model": ModelArtifactLock(
        name="PINN Richards Physical Infiltration Neural Network",
        relative_path="5_storage/checkpoints/pinn_richards_model.pt",
        golden_sha256="de1cd19c9993f0b35b4612c89d6b92a0553f95d5adaab695264d1be92b697e42",
        byte_size=55877,
        description="Richards equation PINN physics-informed neural network checkpoint."
    ),
    "enkf_state_database": ModelArtifactLock(
        name="EnKF Sequential State Estimation Database",
        relative_path="5_storage/state_database/enkf_state_database.pt",
        golden_sha256="e525676287aab7769da5516c55de1820ae1a77c173f8180fc4937188b770f4ba",
        byte_size=16181,
        description="50-member ensemble state trajectories and cross-covariance matrices."
    ),
    "uncertainty_registry": ModelArtifactLock(
        name="Conformal Bayesian Uncertainty Registry",
        relative_path="5_storage/registry/uncertainty_registry.pt",
        golden_sha256="452c9da84a61d1d136e17ef47ebe2159b15a246c81b99aa53dcd0ad1e2efaeef",
        byte_size=40379,
        description="Empirical non-conformity scores and conformal quantile calibration bounds."
    ),
    "final_scientific_audit": ModelArtifactLock(
        name="Final Master Scientific Audit Certified Checkpoint",
        relative_path="5_storage/checkpoints/final_scientific_audit_checkpoint.pt",
        golden_sha256="c3afec5540c17405b621b3926aba48394c543de26f669f3bbb7bc27afbceb4e7",
        byte_size=2889,
        description="Notebook 12 100/100 Century Master Audit Sign-Off verification checkpoint."
    ),
}


def get_default_project_root() -> Path:
    """
    Locates the repository project root containing the 5_storage directory.
    """
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "5_storage").is_dir() or (current / ".git").is_dir():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def compute_file_sha256(filepath: Path | str, chunk_size: int = 65536) -> str:
    """
    Computes streaming SHA-256 digest of a file using chunked binary reading.
    
    Args:
        filepath: Absolute or relative path to the file.
        chunk_size: Read buffer size in bytes (default 64 KB).
        
    Returns:
        Lowercase hexadecimal SHA-256 hash string.
        
    Raises:
        FileNotFoundError: If the target file does not exist.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found on disk: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest().lower()


def verify_model_lock(
    project_root: Optional[Path | str] = None,
    registry: Optional[Dict[str, ModelArtifactLock]] = None,
    strict: bool = True
) -> Dict[str, Any]:
    """
    Audits and validates the cryptographic integrity of all certified model checkpoints.
    
    Args:
        project_root: Root directory of the repository (defaults to auto-detected root).
        registry: Custom registry mapping, or defaults to CERTIFIED_MODEL_LOCK_REGISTRY.
        strict: If True, raises ModelIntegrityDriftError immediately upon any mismatch.
        
    Returns:
        Dictionary containing structured audit telemetry and per-artifact verification results.
        
    Raises:
        ModelIntegrityDriftError: If strict is True and any artifact hash fails verification.
        FileNotFoundError: If strict is True and any certified artifact is missing.
    """
    root = Path(project_root) if project_root is not None else get_default_project_root()
    active_registry = registry if registry is not None else CERTIFIED_MODEL_LOCK_REGISTRY

    audit_timestamp = datetime.now(timezone.utc).isoformat()
    results: Dict[str, Any] = {
        "status": "SEALED_PASSED",
        "verified_at": audit_timestamp,
        "project_root": str(root),
        "total_artifacts": len(active_registry),
        "passed_count": 0,
        "failed_count": 0,
        "artifacts": {}
    }

    all_passed = True
    drift_violations: List[str] = []

    for key, lock in active_registry.items():
        file_path = root / lock.relative_path
        
        if not file_path.is_file():
            all_passed = False
            results["failed_count"] += 1
            results["artifacts"][key] = {
                "name": lock.name,
                "path": str(file_path),
                "status": "MISSING",
                "expected_hash": lock.golden_sha256,
                "computed_hash": None,
                "match": False,
                "error": "File does not exist on disk"
            }
            violation_msg = f"Missing certified artifact: '{lock.name}' at {file_path}"
            drift_violations.append(violation_msg)
            if strict:
                raise FileNotFoundError(violation_msg)
            continue

        computed_hash = compute_file_sha256(file_path)
        actual_size = file_path.stat().st_size
        is_match = (computed_hash == lock.golden_sha256.lower())

        if is_match:
            results["passed_count"] += 1
            results["artifacts"][key] = {
                "name": lock.name,
                "path": str(file_path),
                "status": "VERIFIED_SEALED",
                "expected_hash": lock.golden_sha256,
                "computed_hash": computed_hash,
                "byte_size": actual_size,
                "match": True
            }
        else:
            all_passed = False
            results["failed_count"] += 1
            results["artifacts"][key] = {
                "name": lock.name,
                "path": str(file_path),
                "status": "HASH_MISMATCH_TAMPERED",
                "expected_hash": lock.golden_sha256,
                "computed_hash": computed_hash,
                "byte_size": actual_size,
                "match": False,
                "error": "Cryptographic hash mismatch (parameter drift detected)"
            }
            violation_msg = (
                f"PARAMETER DRIFT / TAMPERING DETECTED in '{lock.name}'!\n"
                f"  Path:          {file_path}\n"
                f"  Expected Hash: {lock.golden_sha256}\n"
                f"  Computed Hash: {computed_hash}"
            )
            drift_violations.append(violation_msg)
            if strict:
                raise ModelIntegrityDriftError(violation_msg)

    if not all_passed:
        results["status"] = "CORRUPTED_FAILED"
        logger.error("AETHER-MRID1607X Model Lock Verification FAILED: %d violations.", len(drift_violations))
    else:
        logger.info("AETHER-MRID1607X Model Lock Certified: All %d checkpoints intact.", len(active_registry))

    return results


def enforce_engine_lock(project_root: Optional[Path | str] = None) -> bool:
    """
    Enforces strict model lock verification prior to inference execution.
    
    Returns:
        True if all certified models match their golden hashes.
        
    Raises:
        ModelIntegrityDriftError: If any parameter drift or tampering is detected.
    """
    telemetry = verify_model_lock(project_root=project_root, strict=True)
    return telemetry["status"] == "SEALED_PASSED"
