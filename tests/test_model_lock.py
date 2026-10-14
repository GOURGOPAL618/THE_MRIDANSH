"""
AETHER-MRID1607X: CRYPTOGRAPHIC MODEL-LOCK UNIT TESTS
Comprehensive verification suite for 3_core_engine/model_lock.py.

Tests:
1. Exact SHA-256 validation of certified artifacts against golden registry.
2. Tamper and bit-flip detection triggering ModelIntegrityDriftError.
3. Missing artifact handling in strict vs non-strict modes.
4. Deterministic streaming hash evaluation across multiple chunk sizes.
5. Non-strict telemetry structure and diagnostics reporting.
"""

import hashlib
import os
from pathlib import Path
import sys
import tempfile
import pytest

# Ensure 3_core_engine is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORE_ENGINE = _REPO_ROOT / "3_core_engine"
if str(_CORE_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CORE_ENGINE))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from model_lock import (
    CERTIFIED_MODEL_LOCK_REGISTRY,
    ModelArtifactLock,
    ModelIntegrityDriftError,
    compute_file_sha256,
    verify_model_lock,
    enforce_engine_lock,
)


class TestModelLockVerification:
    """Test suite for AETHER-MRID1607X cryptographic model locking."""

    def test_01_certified_artifacts_sha256_match(self):
        """
        Verify that all certified model checkpoints on disk match their
        golden SHA-256 hashes with 100% cryptographic precision.
        """
        telemetry = verify_model_lock(project_root=_REPO_ROOT, strict=True)
        assert telemetry["status"] == "SEALED_PASSED"
        assert telemetry["failed_count"] == 0
        assert telemetry["passed_count"] == len(CERTIFIED_MODEL_LOCK_REGISTRY)
        assert telemetry["total_artifacts"] == 4

        # Validate each artifact individually
        for key, artifact_info in telemetry["artifacts"].items():
            assert artifact_info["status"] == "VERIFIED_SEALED"
            assert artifact_info["match"] is True
            assert artifact_info["computed_hash"] == artifact_info["expected_hash"]
            assert artifact_info["byte_size"] > 0

        # Enforce lock assertion
        assert enforce_engine_lock(project_root=_REPO_ROOT) is True

    def test_02_tamper_detection_triggers_drift_error(self):
        """
        Simulate a bit flip / unauthorized model modification on disk.
        Assert that verify_model_lock in strict mode raises ModelIntegrityDriftError.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_checkpoint = temp_path / "tampered_checkpoint.pt"
            # Write initial binary content
            fake_checkpoint.write_bytes(b"INITIAL_TRAINED_WEIGHTS_TENSOR_STATE_DATA_0123456789")
            initial_hash = hashlib.sha256(fake_checkpoint.read_bytes()).hexdigest()

            # Create mock registry with initial hash as golden hash
            mock_registry = {
                "tampered_model": ModelArtifactLock(
                    name="Tampered Synthetic Checkpoint",
                    relative_path="tampered_checkpoint.pt",
                    golden_sha256=initial_hash,
                    byte_size=fake_checkpoint.stat().st_size,
                    description="Test checkpoint for tamper detection."
                )
            }

            # First verify it passes before tampering
            pre_tamper = verify_model_lock(project_root=temp_path, registry=mock_registry, strict=True)
            assert pre_tamper["status"] == "SEALED_PASSED"

            # Tamper with 1 single byte (simulate bit rot or unauthorized weight drift)
            fake_checkpoint.write_bytes(b"INITIAL_TRAINED_WEIGHTS_TENSOR_STATE_DATA_012345678X")

            # Must raise ModelIntegrityDriftError in strict mode
            with pytest.raises(ModelIntegrityDriftError) as exc_info:
                verify_model_lock(project_root=temp_path, registry=mock_registry, strict=True)
            
            assert "PARAMETER DRIFT / TAMPERING DETECTED" in str(exc_info.value)
            assert initial_hash in str(exc_info.value)

    def test_03_missing_file_detection(self):
        """
        Test behavior when a certified artifact file is missing.
        Strict mode must raise FileNotFoundError; non-strict mode returns CORRUPTED_FAILED.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mock_registry = {
                "missing_model": ModelArtifactLock(
                    name="Missing Checkpoint",
                    relative_path="does_not_exist.pt",
                    golden_sha256="0000000000000000000000000000000000000000000000000000000000000000",
                    byte_size=1234,
                    description="Test missing file."
                )
            }

            # Strict mode: must raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                verify_model_lock(project_root=temp_path, registry=mock_registry, strict=True)

            # Non-strict mode: must return structured error telemetry without crash
            telemetry = verify_model_lock(project_root=temp_path, registry=mock_registry, strict=False)
            assert telemetry["status"] == "CORRUPTED_FAILED"
            assert telemetry["failed_count"] == 1
            assert telemetry["artifacts"]["missing_model"]["status"] == "MISSING"
            assert telemetry["artifacts"]["missing_model"]["match"] is False

    def test_04_streaming_hash_consistency(self):
        """
        Ensure chunked streaming hash computation is 100% deterministic
        across tiny (1-byte, 64-byte) and large (64-KB) buffers, matching standard sha256.
        """
        sample_payload = b"AETHER_MISSION_GRADE_CHECKPOINT_STREAMING_VERIFICATION_PAYLOAD" * 1000
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(sample_payload)
            temp_file = Path(f.name)

        try:
            expected_hash = hashlib.sha256(sample_payload).hexdigest()
            # Test different chunk sizes
            hash_1b = compute_file_sha256(temp_file, chunk_size=1)
            hash_64b = compute_file_sha256(temp_file, chunk_size=64)
            hash_1kb = compute_file_sha256(temp_file, chunk_size=1024)
            hash_64kb = compute_file_sha256(temp_file, chunk_size=65536)

            assert hash_1b == expected_hash
            assert hash_64b == expected_hash
            assert hash_1kb == expected_hash
            assert hash_64kb == expected_hash
        finally:
            if temp_file.exists():
                temp_file.unlink()

    def test_05_non_strict_telemetry_reporting(self):
        """
        Verify that non-strict mode provides rich diagnostics and valid schema.
        """
        telemetry = verify_model_lock(project_root=_REPO_ROOT, strict=False)
        assert "status" in telemetry
        assert "verified_at" in telemetry
        assert "project_root" in telemetry
        assert "total_artifacts" in telemetry
        assert "passed_count" in telemetry
        assert "failed_count" in telemetry
        assert "artifacts" in telemetry
        assert telemetry["status"] == "SEALED_PASSED"
        assert len(telemetry["artifacts"]) == 4
