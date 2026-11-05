# THE MRIDANSH (AETHER-MRID1607X)
# Module: 3_core_engine/data - Pipeline Snapshot Adapter
# Requirements, Verification and Configuration Control

---

## 1. Document Control

### 1.1 Identification
- **Document Identifier**: `DOC-MRID-03-DATA-001`
- **Module Name**: Pipeline Snapshot Data Adapter
- **Module Path**: `3_core_engine/data/`
- **Source Files**: `pipeline_adapter.py`, `__init__.py`
- **Classification**: High-Integrity Multi-Modal Tensor Ingestion Adapter
- **Effective Date**: 2026-11-05
- **Status**: RELEASED / PRODUCTION AUDITED

### 1.2 Revision History
| Version | Date | Author | Description of Change |
|:---:|:---:|:---:|:---|
| 1.0 | 2026-11-05 | Gourgopal Mohapatra | Unfiltered engineering baseline and verification audit for `3_core_engine/data/pipeline_adapter.py`. Discloses batch dimension handling, shape invariants, emoji logging in production namespace, and PyTorch `Dataset` contract. |

### 1.3 Document Conventions
- **Requirement Tagging**:
  - `FR-ENG-DAT-xxx`: Functional Requirement
  - `DI-ENG-DAT-xxx`: Data Integrity and Invariant Requirement
  - `IF-ENG-DAT-xxx`: Interface Requirement
  - `NF-ENG-DAT-xxx`: Non-Functional Performance Requirement
- **Verification Methods**:
  - `T`: Automated Software Test
  - `A`: Mathematical / Static Analysis
  - `I`: Dynamic Code Inspection

---

## 2. Purpose and Scope

### 2.1 Purpose
The `3_core_engine/data` subsystem serves as the boundary adapter connecting the upstream `2_data_pipeline` geospatial data structures with the deep learning backbones in `3_core_engine/models/`. It converts NumPy snapshot dictionaries emitted by `SatelliteSAROpticalFusionEngine` into PyTorch 5D tensors formatted as $(B, T, C, H, W)$ for spatiotemporal sequence processing.

### 2.2 In Scope
1. [3_core_engine/data/pipeline_adapter.py](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20(RS-SDA%20DIVISION)/THE_MRIDANSH/3_core_engine/data/pipeline_adapter.py) (92 lines)
2. [3_core_engine/data/__init__.py](file:///d:/JAGANNATH_CODE_SANCTUM/JCC%20CAMPUS%202%20(RS-SDA%20DIVISION)/THE_MRIDANSH/3_core_engine/data/__init__.py) (0 lines)
3. Integration with `tests/test_core_integration_d05.py` and `tests/test_core_trainer_d06.py`

---

## 3. Mandatory Unfiltered Engineering Disclosure & Architectural Audit

> [!CAUTION]
> **BRUTAL ARCHITECTURAL REALITY & CODE AUDIT**:
> 1. **Hardcoded Batch and Time Dimensions in `__getitem__` (Defect D-ENG-DAT-001)**:
>    In `PipelineSnapshotAdapter.__getitem__` (lines 80–82):
>    ```python
>    tensor_chw = np.transpose(tensor_np, (2, 0, 1))  # (C, H, W)
>    tensor_btchw = tensor_chw[np.newaxis, np.newaxis, ...]  # (1, 1, C, H, W)
>    tensor_torch = torch.from_numpy(tensor_btchw).float()
>    ```
>    The adapter forcibly injects both $B=1$ and $T=1$ inside individual dataset items. If wrapped in a standard PyTorch `DataLoader(..., batch_size=4)`, the DataLoader prepends *another* batch dimension, resulting in an unhandled 6D tensor of shape $(4, 1, 1, C, H, W)$, which crashes downstream convolutional encoders!
> 2. **Rigid Channel Count Coupling (Defect D-ENG-DAT-002)**:
>    The constructor hardcodes `in_channels: int = 5` as default. However, the frozen AETHER-MRID1607X operational flight bundle requires 4 distinct sensor modalities with different channel configurations (SAR=2 or 4, Optical=4 or 5, Terrain=4, Weather=3). Passing a modern 4-modality tensor into `PipelineSnapshotAdapter` raises an immediate `ValueError: Expected 5 channels for the backbone, got N`.
> 3. **Unchecked Validity Mask Data Integrity (Defect D-ENG-DAT-003)**:
>    While `tensor_np` is checked for finiteness via `np.isfinite(tensor_np).all()`, `mask_np` is only checked for shape equivalence (`mask_np.shape != tensor_np.shape`). The adapter never validates whether the mask is boolean or uint8, nor does it check for NaNs in the mask.
> 4. **Production Terminal Logging with Raw Emojis (Defect D-ENG-DAT-004)**:
>    Line 34 executes `logging.info(f"📦 PipelineSnapshotAdapter initialised with...")`. On standard Windows consoles with OEM code page 437 or CP1252, unhandled UTF-8 emoji strings trigger `UnicodeEncodeError`.

---

## 4. Technical Specification

### 4.1 Class: `PipelineSnapshotAdapter(Dataset)`
- **Input Snapshot Dictionary Contract**:
  - `fused_tensor`: `np.ndarray` of shape $(H, W, C)$, dtype `float32`
  - `fused_validity_mask`: `np.ndarray` of shape $(H, W, C)$
  - `channels`: `List[str]` of length $C$
  - Optional metadata: timestamp, CRS, bounding box, satellite provenance
- **Validation Sequence**:
  1. `snapshots` must be a non-empty list.
  2. Dict must contain all required keys: `fused_tensor`, `fused_validity_mask`, `channels`.
  3. `ndim == 3`.
  4. Spatial shape congruence: `fused_validity_mask.shape == fused_tensor.shape`.
  5. Channel length consistency: `len(channels) == C == in_channels`.
  6. Finiteness check: `np.isfinite(fused_tensor).all()`.
- **Output Item Contract**:
  - `input_tensor`: `torch.Tensor` of shape $(1, 1, C, H, W)$, dtype `torch.float32`
  - `metadata`: `Dict[str, Any]` preserving non-tensor metadata

### 4.2 Helper Function: `snapshot_to_tensor`
- **Signature**: `snapshot_to_tensor(snapshot: Dict[str, Any], in_channels: int = 5) -> torch.Tensor`
- **Functionality**: Instantiates a single-element adapter and extracts `adapter[0]["input_tensor"]`.

---

## 5. Requirements Catalog

### 5.1 Functional Requirements
- **FR-ENG-DAT-001: Snapshot Ingestion & Layout Permutation**: The adapter shall ingest $(H, W, C)$ NumPy arrays and permute axis ordering to $(C, H, W)$ layout.
- **FR-ENG-DAT-002: PyTorch Dataset Compliance**: `PipelineSnapshotAdapter` shall implement `__len__` and `__getitem__` conforming to PyTorch `torch.utils.data.Dataset`.
- **FR-ENG-DAT-003: Standalone Helper Execution**: `snapshot_to_tensor` shall provide zero-overhead single snapshot conversion.

### 5.2 Data Integrity Requirements
- **DI-ENG-DAT-001: Strict Finite Value Enforcement**: Snapshots containing `NaN` or `Inf` values shall be rejected with `ValueError`.
- **DI-ENG-DAT-002: Spatial Mask Congruence**: Mismatched array dimensions between tensor and mask shall raise `ValueError`.
- **DI-ENG-DAT-003: Channel Count Enforcement**: Channel dimension discrepancies with `in_channels` shall raise `ValueError`.

### 5.3 Non-Functional Requirements
- **NF-ENG-DAT-001: Conversion Latency**: Single $64 \times 64 \times 5$ snapshot conversion shall execute in $< 0.5\,\text{ms}$ on CPU.

---

## 6. Verification Procedures & Empirical Test Evidence

### 6.1 Automated Verification
Verified in integration test suites `tests/test_core_integration_d05.py` and `tests/test_core_trainer_d06.py`.

### 6.2 Test Output
```text
tests/test_core_integration_d05.py::test_pipeline_adapter_instantiation PASSED
tests/test_core_integration_d05.py::test_pipeline_adapter_shape_validation PASSED
tests/test_core_integration_d05.py::test_pipeline_adapter_nan_rejection PASSED
```

---

## 7. Traceability Matrix

| Requirement | Source Implementation | Verification Procedure | Status |
|:---|:---|:---|:---:|
| `FR-ENG-DAT-001` | `PipelineSnapshotAdapter.__getitem__` | `tests/test_core_integration_d05.py` | **MET** |
| `FR-ENG-DAT-002` | `PipelineSnapshotAdapter` | `tests/test_core_integration_d05.py` | **MET** |
| `FR-ENG-DAT-003` | `snapshot_to_tensor` | `tests/test_core_integration_d05.py` | **MET** |
| `DI-ENG-DAT-001` | `PipelineSnapshotAdapter.__getitem__` | `tests/test_core_integration_d05.py` | **MET** |
| `DI-ENG-DAT-002` | `PipelineSnapshotAdapter.__getitem__` | `tests/test_core_integration_d05.py` | **MET** |
| `DI-ENG-DAT-003` | `PipelineSnapshotAdapter.__getitem__` | `tests/test_core_integration_d05.py` | **MET** |

---

## 8. Defect Log and Technical Debt Register

| Defect ID | Description | Severity | Impact | Remediation Plan |
|:---:|:---|:---:|:---|:---|
| **D-ENG-DAT-001** | Embedded $(1, 1, C, H, W)$ rank causes 6D crash under multi-sample PyTorch DataLoader. | HIGH | Prevents standard mini-batching in PyTorch training loops. | Remove extra batch dimension inside `__getitem__`; return $(T, C, H, W)$. |
| **D-ENG-DAT-002** | Hardcoded `in_channels=5` defaults to legacy 5-band prototype. | MEDIUM | Incompatible with modern 4-source AETHER multimodal input bundles. | Dynamic channel count inference from snapshot metadata. |
| **D-ENG-DAT-003** | Missing mask finite & boolean value validation. | LOW | Invalids in mask could propagate undetected. | Validate `np.isin(mask_np, [0, 1]).all()`. |
| **D-ENG-DAT-004** | UTF-8 box emoji in console logging. | LOW | Windows cp1252 crash risk on non-UTF8 terminals. | Strip emojis from logging statements. |
