.. AETHER-MRID1607X-NB02-DOC-001  |  Version 1.0  |  2026-10-06
.. Format: reStructuredText (Sphinx / docutils compatible)

:Document ID: AETHER-MRID1607X-NB02-DOC-001
:Version: 1.0 (Draft for Owner Review)
:Date: 2026-10-06
:Owner: Gourgopal Mohapatra
:Organization: JCC HEADQUARTER, JCC CAMPUS 2, RS-SDA Division
:Item documented: ``02-preprocessing.ipynb``
:Classification: Confidential & Proprietary

.. contents:: Table of Contents
   :depth: 3
   :local:

AETHER-MRID1607X — Notebook 02: Satellite Data Preprocessing
============================================================

Software Requirements, Design, Verification and Traceability Document (DO-178C-style)
-------------------------------------------------------------------------------------

0. Document Control
-------------------

+------------------------------------------------------+------------------------------------------------------+
| Field                                                | Value                                                |
+======================================================+======================================================+
| **Document ID**                                      | AETHER-MRID1607X-NB02-DOC-001                        |
+------------------------------------------------------+------------------------------------------------------+
| **Document Title**                                   | Software Requirements Data, Design Description,      |
|                                                      | Verification Cases/Results and Trace Data for        |
|                                                      | ``02-preprocessing.ipynb``                           |
+------------------------------------------------------+------------------------------------------------------+
| **Project**                                          | THE MRIDANSH                                         |
+------------------------------------------------------+------------------------------------------------------+
| **Central Engine**                                   | AETHER : MRID1607X (Multi-Domain Soil Intelligence   |
|                                                      | Engine)                                              |
+------------------------------------------------------+------------------------------------------------------+
| **Item Documented**                                  | Jupyter notebook ``02-preprocessing.ipynb``          |
|                                                      | (Notebook 02, Sprint Days 3–4)                       |
+------------------------------------------------------+------------------------------------------------------+
| **Document Version**                                 | 1.0 (Draft for Owner Review)                         |
+------------------------------------------------------+------------------------------------------------------+
| **Document Date**                                    | 2026-10-06                                           |
+------------------------------------------------------+------------------------------------------------------+
| **Owner / Developer**                                | Gourgopal Mohapatra                                  |
+------------------------------------------------------+------------------------------------------------------+
| **Organization**                                     | JCC HEADQUARTER — JCC CAMPUS 2, RS-SDA Division      |
+------------------------------------------------------+------------------------------------------------------+
| **Document Status**                                  | Baseline-ready, pending owner review and approval    |
+------------------------------------------------------+------------------------------------------------------+
| **Reviewer / Approver**                              | *(to be completed by owner)*                         |
+------------------------------------------------------+------------------------------------------------------+
| **Classification**                                   | Confidential & Proprietary (see Appendix C)          |
+------------------------------------------------------+------------------------------------------------------+

0.1 Revision History
~~~~~~~~~~~~~~~~~~~~

+--------------------------+-----------------+-----------------------+--------------------------------------+
| Version                  | Date            | Author                | Description                          |
+==========================+=================+=======================+======================================+
| 0.1                      | 2026-10-06      | Documentation pass    | Reverse-engineered from notebook     |
|                          |                 |                       | source, cell outputs and metadata    |
+--------------------------+-----------------+-----------------------+--------------------------------------+
| 1.0                      | 2026-10-06      | Documentation pass    | Requirements, design, verification,  |
|                          |                 |                       | traceability and problem reports     |
|                          |                 |                       | consolidated                         |
+--------------------------+-----------------+-----------------------+--------------------------------------+

0.2 Important Notice on Certification Claims
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This document is **structured after the life-cycle data items of RTCA DO-178C / EUROCAE ED-12C** (Software
Requirements Data, Design Description, Verification Cases and Procedures, Verification Results, Configuration
Index, Problem Reports, Trace Data). It is written to give the notebook the same *rigor of traceability and
evidence*.

It is **not** a certification artifact. No Design Assurance Level (DAL) has been assigned by any certification
authority, and no claim of DO-178C compliance is made. The notebook is research software for a remote-sensing
/ geotechnical data pipeline, not airborne software.

0.3 How Evidence Is Labeled in This Document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------------------------------+---------------------------------------------------------------------+
| Tag                                  | Meaning                                                             |
+======================================+=====================================================================+
| **[NB]**                             | Evidence taken directly from the saved notebook (source code, saved |
|                                      | cell outputs, metadata)                                             |
+--------------------------------------+---------------------------------------------------------------------+
| **[AN]**                             | Evidence obtained by re-executing the notebook logic offline during |
|                                      | this documentation pass (same seed, same code). All offline         |
|                                      | re-execution results for the values printed by the notebook matched |
|                                      | the notebook’s printed values exactly                               |
+--------------------------------------+---------------------------------------------------------------------+
| **[INS]**                            | Evidence from manual inspection of source text                      |
+--------------------------------------+---------------------------------------------------------------------+

1. Introduction
---------------

1.1 Purpose
~~~~~~~~~~~

This document defines, for ``02-preprocessing.ipynb``:

1. what the software is required to do (high-level, low-level and derived requirements),
2. how it is designed to do it (architecture, algorithms, data structures, parameters),
3. how each requirement is verified and what the verification evidence shows,
4. the complete bidirectional traceability between requirements, design, code cells and verification cases,
5. every discrepancy, defect and limitation found between *what the notebook claims* and *what the notebook
   does* (Section 12).

1.2 Scope
~~~~~~~~~

In scope: every one of the 29 cells of the notebook (13 code cells, 16 markdown cells), all 4 figures, all
printed audit reports, and both exported artifacts.

Out of scope: Notebook 01 (data ingestion), Notebook 03 (GCN spatial modeling), PINN/EnKF components, and the
Kaggle platform itself.

1.3 Notebook Purpose (Summary)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Notebook 02 takes a 35-record Sentinel-1 (SAR) / Sentinel-2 (optical) / DEM telemetry table and performs:

-  NDVI derivation,
-  Sentinel-2 cloud quality control (threshold ≤ 50 % cloud cover),
-  Sentinel-1 VV 1-D temporal Lee speckle filtering,
-  80/20 chronological train/test partition,
-  Z-score scaling (SAR VV-Lee, SAR VH, DEM) and Min-Max scaling (NDVI) fitted on the training partition,
-  integrity assertions,
-  export of ``preprocessed_telemetry.csv`` and ``scaler_manifest.json``.

1.4 Intended Audience
~~~~~~~~~~~~~~~~~~~~~

Project owner, algorithm developers (Notebook 03 / PINN / GCN), reviewers, and anyone auditing data-leakage
claims.

1.5 Document Conventions
~~~~~~~~~~~~~~~~~~~~~~~~

-  **shall** = mandatory requirement; **should** = recommended; **may** = permitted.
-  Cell references use the **0-based cell index** ``C00``\ …\ ``C28`` (Section 4.3).
-  Requirement IDs: ``HLR-nn`` (high-level), ``LLR-nn`` (low-level), ``DR-nn`` (derived), ``NFR-nn``
   (non-functional / constraint), ``IF-nn`` (interface), ``VC-nn`` (verification case), ``PR-nn`` (problem
   report).
-  Verification methods: **T** = Test (execution), **I** = Inspection, **A** = Analysis, **D** =
   Demonstration.

2. Reference Documents
----------------------

+-----------------------------------+------------------------------------------------------------------------+
| Ref                               | Document                                                               |
+===================================+========================================================================+
| [R1]                              | RTCA DO-178C / EUROCAE ED-12C, *Software Considerations in Airborne    |
|                                   | Systems and Equipment Certification* (structure used as a model only)  |
+-----------------------------------+------------------------------------------------------------------------+
| [R2]                              | ``02-preprocessing.ipynb``, 642,415 bytes, nbformat 4.4 (item under    |
|                                   | documentation)                                                         |
+-----------------------------------+------------------------------------------------------------------------+
| [R3]                              | Notebook 01 (data ingestion; artifact ``stac_telemetry_raw.csv``       |
|                                   | referenced by Step 1 markdown; **not provided**)                       |
+-----------------------------------+------------------------------------------------------------------------+
| [R4]                              | Notebook 03 (Spatial Modeling & GCN; downstream consumer; **not        |
|                                   | provided**)                                                            |
+-----------------------------------+------------------------------------------------------------------------+
| [R5]                              | J.-S. Lee, “Digital image enhancement and noise filtering by use of    |
|                                   | local statistics,” IEEE TPAMI, 1980 (algorithm family of the Lee       |
|                                   | filter)                                                                |
+-----------------------------------+------------------------------------------------------------------------+
| [R6]                              | ESA Sentinel-2 Level-2A Scene Classification Layer (SCL) specification |
|                                   | (cited by the notebook narrative only)                                 |
+-----------------------------------+------------------------------------------------------------------------+

3. Definitions and Acronyms
---------------------------

================ ===================================================================
Term             Definition
================ ===================================================================
AETHER-MRID1607X Central engine of project THE MRIDANSH
DEM              Digital Elevation Model
DAL              Design Assurance Level (DO-178C A–E)
EnKF             Ensemble Kalman Filter
GCN              Graph Convolutional Network
HLR / LLR / DR   High-Level / Low-Level / Derived Requirement
NDVI             Normalized Difference Vegetation Index, (NIR − Red) / (NIR + Red)
PINN             Physics-Informed Neural Network
QC               Quality Control
SAR              Synthetic Aperture Radar
SCL              Sentinel-2 Scene Classification Layer
S1 / S2          Sentinel-1 / Sentinel-2
VV / VH          SAR polarization channels (vertical-vertical / vertical-horizontal)
STAC             SpatioTemporal Asset Catalog
θv               Volumetric soil moisture (project target quantity)
Train / Test     First 80 % / last 20 % of the chronologically ordered records
Leakage          Any dependence of training-side computation on test-period data
================ ===================================================================

4. Notebook Identification and Configuration Index
--------------------------------------------------

4.1 Item Identification
~~~~~~~~~~~~~~~~~~~~~~~

================================= ========================================================== ========
Attribute                         Value                                                      Source
================================= ========================================================== ========
File name                         ``02-preprocessing.ipynb``                                 upload
Internal self-name (manifest)     ``02_preprocessing.ipynb`` (underscore; see PR-12)         [NB] C26
File size                         642,415 bytes                                              [AN]
Notebook format                   nbformat 4, minor 4                                        [NB]
Kernel                            ``python3`` (“Python 3”)                                   [NB]
Language / version                Python 3.12.13                                             [NB]
Platform metadata                 Kaggle notebook (``sourceType: notebook``)                 [NB]
Accelerator                       none (``isGpuEnabled: false``)                             [NB]
Internet                          disabled (``isInternetEnabled: false``)                    [NB]
Attached data sources             none (``dataSources: []``)                                 [NB]
Docker image version id           28755                                                      [NB]
Execution counts                  30 → 42, strictly increasing in cell order (13 code cells) [NB]
Execution errors in saved outputs none (no ``error`` outputs)                                [NB]
Embedded figures                  4 PNG (``display_data``) in C08, C12, C20, C22             [NB]
================================= ========================================================== ========

4.2 Library Baseline
~~~~~~~~~~~~~~~~~~~~

Exact library versions are **not recorded** in the notebook (see PR-15). The following is inferred.

+-------------------------+----------------------------+----------------------------------------------------+
| Library                 | Used for                   | Version evidence                                   |
+=========================+============================+====================================================+
| Python                  | runtime                    | 3.12.13 [NB]                                       |
+-------------------------+----------------------------+----------------------------------------------------+
| NumPy                   | arrays, RNG, ``where``,    | ≥ 2.0 inferred, because printed dictionary shows   |
|                         | ``maximum``                | ``np.float64(...)`` reprs [NB]                     |
+-------------------------+----------------------------+----------------------------------------------------+
| pandas                  | DataFrame, ``date_range``, | not recorded                                       |
|                         | CSV I/O                    |                                                    |
+-------------------------+----------------------------+----------------------------------------------------+
| SciPy                   | ``uniform_filter`` (used); | not recorded                                       |
| (``scipy.ndimage``)     | ``variance`` (imported,    |                                                    |
|                         | **unused**)                |                                                    |
+-------------------------+----------------------------+----------------------------------------------------+
| Matplotlib              | plotting, dark theme       | not recorded                                       |
+-------------------------+----------------------------+----------------------------------------------------+
| json, os, sys           | stdlib (``sys`` imported,  | stdlib                                             |
|                         | **unused**)                |                                                    |
+-------------------------+----------------------------+----------------------------------------------------+

Offline reproduction used NumPy 2.4.4, pandas 3.0.2, SciPy 1.17.1, Matplotlib 3.10.8 [AN] and reproduced every
printed number.

4.3 Cell Inventory (Complete)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

==== ==== ====== ==================================================================== ========================
Cell Type Exec # Title / Role                                                         Section in this document
==== ==== ====== ==================================================================== ========================
C00  MD   —      Project banner, engine, division, framework, operational target      1, 5
C01  MD   —      Notebook 02 header, sprint objective, Lee and Min-Max math           8.2, 8.3
C02  Code 30     Imports and Matplotlib dark-theme configuration                      8.1
C03  MD   —      Step 1 description (claims load from Notebook 01)                    8.2
C04  Code 31     In-memory telemetry generator, NDVI, write raw CSV                   8.2
C05  MD   —      Step 2 description (cloud QC, 50 % threshold)                        8.3
C06  Code 32     Cloud-QC flag and NDVI masking, counts report                        8.3
C07  MD   —      Plot 1 description                                                   13
C08  Code 33     Plot 1: raw vs masked NDVI                                           13
C09  MD   —      Step 3 description (Lee filter)                                      8.4
C10  Code 34     ``apply_lee_filter_1d``, apply to VV, variance report                8.4
C11  MD   —      Plot 2 description                                                   13
C12  Code 35     Plot 2: raw vs Lee-filtered VV                                       13
C13  MD   —      Step 4 description (leakage invariant)                               8.5
C14  Code 36     Split index, train stats, ``s1_vv_normalized``, audit report (Day 3) 8.5
C15  MD   —      Part 2 header (Day 4), Z-score and Min-Max math                      8.6
C16  Code 37     Feature list, ``df_proc``, split bounds report                       8.6
C17  MD   —      Step 5 description                                                   8.7
C18  Code 38     Z-score (3 columns) + NDVI Min-Max, ``train_stats``                  8.7
C19  MD   —      Plot 3 description                                                   13
C20  Code 39     Plot 3: distributions, raw vs Z-score                                13
C21  MD   —      Plot 4 description                                                   13
C22  Code 40     Plot 4: scaled multi-sensor series + split boundary                  13
C23  MD   —      Step 6 description (integrity audit)                                 8.8
C24  Code 41     Assertions and final audit report                                    8.8
C25  MD   —      Step 7 description (export)                                          8.9
C26  Code 42     Export CSV and scaler manifest JSON                                  8.9
C27  MD   —      Executive summary and milestones claims                              12, App. B
C28  MD   —      IP and copyright notice                                              App. C
==== ==== ====== ==================================================================== ========================

5. System Context and Software Overview
---------------------------------------

5.1 Position in the Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

     Notebook 01                    Notebook 02 (this item)                  Notebook 03
    (ingestion, STAC)   --------->  Preprocessing / QC / Despeckle / Scale  ---------> (GCN spatial
    stac_telemetry_raw.csv         preprocessed_telemetry.csv                         modeling)
    [not provided]                 scaler_manifest.json

..

   **Note [NB]:** In the delivered notebook, the raw table is *not* read from Notebook 01. It is regenerated
   in memory (C04) from a seeded random generator and then written to ``data_raw/``. See PR-01.

5.2 Internal Data Flow
~~~~~~~~~~~~~~~~~~~~~~

::

    C04  df_raw (8 cols, 35 rows)
           |
           v
    C06  df_qc  = df_raw + optical_qc_pass + ndvi_masked
           |
           v
    C10  df_qc  += s1_vv_lee                           (Lee filter on FULL series)
           |
           v
    C14  df_qc  += s1_vv_normalized                    (train mean/std, split_idx = 28)
           |
           v
    C16  df_proc = df_qc.copy();  train_df = [0:28];  test_df = [28:35]
           |
           v
    C18  scaled_df = df_proc + 3 z-score cols + ndvi_minmax;   train_stats{}
           |
           v
    C24  assertions (nulls, train z-mean/std, row count)
           |
           v
    C26  preprocessed_telemetry.csv  +  scaler_manifest.json

5.3 Software Characteristics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------------------+--------------------------------+
| Characteristic                                                            | Value                          |
+===========================================================================+================================+
| Execution model                                                           | Sequential, single-process,    |
|                                                                           | top-to-bottom cell execution;  |
|                                                                           | no concurrency                 |
+---------------------------------------------------------------------------+--------------------------------+
| Data volume                                                               | N = 35 records; ≈ 16 columns;  |
|                                                                           | negligible compute and memory  |
+---------------------------------------------------------------------------+--------------------------------+
| External inputs at run time                                               | none (all data synthetic,      |
|                                                                           | in-memory)                     |
+---------------------------------------------------------------------------+--------------------------------+
| Outputs                                                                   | 2 files, 4 figures, console    |
|                                                                           | reports                        |
+---------------------------------------------------------------------------+--------------------------------+
| Persistent state                                                          | shared kernel namespace        |
|                                                                           | between cells (cells depend on |
|                                                                           | earlier cells’ variables)      |
+---------------------------------------------------------------------------+--------------------------------+
| Randomness                                                                | ``numpy.random.seed(42)``      |
|                                                                           | once, in C04                   |
+---------------------------------------------------------------------------+--------------------------------+
| Safety-/hazard relevance                                                  | Indirect: output feeds         |
|                                                                           | downstream subgrade-stability  |
|                                                                           | (shear-strength) estimation;   |
|                                                                           | faulty preprocessing may bias  |
|                                                                           | downstream estimates           |
+---------------------------------------------------------------------------+--------------------------------+

5.4 Assumed Assurance Level (Informative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No DAL is formally assigned. Because the downstream product concerns geotechnical stability, a failure of this
stage is judged to yield *degraded accuracy* (not direct hazard) of an advisory estimate. For documentation
rigor the *structure* of DAL D/C-type objectives (requirements, trace, verification, problem reporting) is
applied. This is an informative assumption only and should be confirmed by the owner.

6. Software Life-Cycle Environment
----------------------------------

+---------------------------------+--------------------------------------------------------------------------+
| Item                            | Description                                                              |
+=================================+==========================================================================+
| Development environment         | Kaggle hosted Jupyter notebook, CPU only, internet disabled              |
+---------------------------------+--------------------------------------------------------------------------+
| Execution order requirement     | C02 → C04 → C06 → C08 → C10 → C12 → C14 → C16 → C18 → C20 → C22 → C24 →  |
|                                 | C26 (as executed, counts 30–42)                                          |
+---------------------------------+--------------------------------------------------------------------------+
| Hard-coded paths                | ``/kaggle/working/data_raw``, ``/kaggle/working/data_processed``         |
+---------------------------------+--------------------------------------------------------------------------+
| Plot theme                      | ``plt.style.use('dark_background')``; monospace font; edge color         |
|                                 | ``#00FFCC``; line width 1.2; grid ``#1A3344``, dashed, alpha 0.5         |
+---------------------------------+--------------------------------------------------------------------------+
| Magic commands                  | ``%matplotlib inline``                                                   |
+---------------------------------+--------------------------------------------------------------------------+
| Version control                 | none recorded (no commit hash / tag in notebook)                         |
+---------------------------------+--------------------------------------------------------------------------+
| Build / compile                 | none (interpreted)                                                       |
+---------------------------------+--------------------------------------------------------------------------+

7. Software Requirements Data
-----------------------------

7.1 High-Level Requirements (HLR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Status legend: **Met**, **Met with deviation**, **Partially met**, **Not met**.

+------+------------------------------------------------------+------------------+-------------+-------------+
| ID   | Requirement (shall statement)                        | Rationale        | Method      | Status      |
+======+======================================================+==================+=============+=============+
| **   | The software **shall** provide a raw telemetry table | Common input     | T, I        | **Met with  |
| HLR- | ``df_raw`` of 35 chronologically ordered records     | contract for all |             | deviation** |
| 01** | with fields ``timestamp``, ``s1_vv_db``,             | later steps      |             | (data       |
|      | ``s1_vh_db``, ``s2_cloud_cover_pct``,                |                  |             | synthetic,  |
|      | ``s2_b04_red``, ``s2_b08_nir``, ``dem_elevation_m``. |                  |             | not read    |
|      |                                                      |                  |             | from        |
|      |                                                      |                  |             | Notebook    |
|      |                                                      |                  |             | 01; PR-01)  |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** compute NDVI = (NIR − Red) /  | Vegetation proxy | T           | **Met**     |
| HLR- | (NIR + Red) for every record.                        | for moisture     |             |             |
| 02** |                                                      | modeling         |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** persist the raw table as CSV  | Reproducible raw | T           | **Met**     |
| HLR- | to                                                   | data lake        |             |             |
| 03** | ``/kaggle/working/data_raw/stac_telemetry_raw.csv``, | artifact         |             |             |
|      | creating the directory if absent.                    |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** classify each record as       | Prevent          | T           | **Met with  |
| HLR- | optical-QC-pass when ``s2_cloud_cover_pct`` ≤ 50.0   | cloud-corrupted  |             | deviation** |
| 04** | and **shall** set NDVI to NaN for records that fail, | indices entering |             | (percentage |
|      | without deleting rows.                               | models           |             | threshold;  |
|      |                                                      |                  |             | SCL bitmask |
|      |                                                      |                  |             | not used;   |
|      |                                                      |                  |             | PR-02)      |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** report the number and         | Visibility of    | T           | **Met**     |
| HLR- | percentage of QC-passed and QC-masked records.       | data loss        |             |             |
| 05** |                                                      |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** produce a speckle-reduced     | Noise reduction  | T, A        | **Met with  |
| HLR- | Sentinel-1 VV series ``s1_vv_lee`` using an adaptive | of SAR           |             | deviation** |
| 06** | Lee filter, ``Î = Ī + W·(I − Ī)``,                   | backscatter      |             | (1-D        |
|      | ``W = Var(I)/(Var(I)+σn²)``.                         |                  |             | temporal,   |
|      |                                                      |                  |             | dB domain,  |
|      |                                                      |                  |             | global σn²  |
|      |                                                      |                  |             | estimate;   |
|      |                                                      |                  |             | PR-11)      |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** partition the records         | Temporal         | T           | **Met**     |
| HLR- | chronologically (no shuffling) into a training set   | hold-out         |             |             |
| 07** | of the first ``floor(0.8·N)`` records and a test set | validation       |             |             |
|      | of the remaining records.                            |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** derive Z-score parameters     | Lea              | T, A        | **Met**     |
| HLR- | (mean, standard deviation) for ``s1_vv_lee``,        | kage-constrained |             | (for scaler |
| 08** | ``s1_vh_db``, ``dem_elevation_m`` and Min-Max        | scaling          |             | parameters) |
|      | parameters (min, max) for ``ndvi_masked``            |                  |             |             |
|      | **exclusively from the training partition**, and     |                  |             |             |
|      | apply them to all records.                           |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** ensure that no training-side  | Scientific       | A           | **Partially |
| HLR- | value, statistic or parameter depends on any         | validity of      |             | met** —     |
| 09** | test-period sample (zero-future-leakage invariant).  | hold-out         |             | violated in |
|      |                                                      | evaluation       |             | the SAR     |
|      |                                                      |                  |             | despeckling |
|      |                                                      |                  |             | stage       |
|      |                                                      |                  |             | (PR-03)     |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** verify, with run-halting      | Detect           | T           | **Met**     |
| HLR- | assertions, (a) zero nulls in the three Z-score      | preprocessing    |             | (limited    |
| 10** | columns, (b) training Z-score mean < 1e-4 in         | corruption       |             | coverage;   |
|      | magnitude and standard deviation within 1e-2 of 1.0, | before           |             | PR-05,      |
|      | (c) train + test row count equals total row count.   | persistence      |             | PR-07)      |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** export the preprocessed table | Hand-off to      | T           | **Met**     |
| HLR- | as                                                   | Notebook 03      |             |             |
| 11** | ``/kaggle/                                           |                  |             |             |
|      | working/data_processed/preprocessed_telemetry.csv``, |                  |             |             |
|      | creating the directory if absent.                    |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** export a scaler manifest      | Reproducible     | T           | **Met**     |
| HLR- | ``/                                                  | inverse/forward  |             |             |
| 12** | kaggle/working/data_processed/scaler_manifest.json`` | scaling          |             |             |
|      | containing project, engine, notebook name, split     | downstream       |             |             |
|      | index, train/test counts and all scaler parameters.  |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** render four diagnostic        | Human-verifiable | D           | **Met**     |
| HLR- | figures (NDVI QC, SAR despeckling, scaling           | evidence         |             | (annotation |
| 13** | distributions, multi-sensor series) with embedded    |                  |             | defects;    |
|      | textual diagnostics.                                 |                  |             | PR-09,      |
|      |                                                      |                  |             | PR-10)      |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** print a status/audit report   | Execution        | T           | **Met**     |
| HLR- | for every processing stage.                          | traceability     |             |             |
| 14** |                                                      |                  |             |             |
+------+------------------------------------------------------+------------------+-------------+-------------+
| **   | The software **shall** be deterministic:             | Reproducibility  | T, A        | **Met**     |
| HLR- | re-execution in the same environment shall yield     |                  |             | (seeded;    |
| 15** | identical numerical outputs.                         |                  |             | versions    |
|      |                                                      |                  |             | unpinned,   |
|      |                                                      |                  |             | PR-15)      |
+------+------------------------------------------------------+------------------+-------------+-------------+

7.2 Low-Level Requirements (LLR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------+-------------------------------------------------------+-------------+----------------------------+
| ID     | Low-level requirement                                 | Cell        | Parent HLR                 |
+========+=======================================================+=============+============================+
| **LL   | Import                                                | C02         | HLR-15                     |
| R-01** | ``sys, os, numpy as                                   |             |                            |
|        |  np, pandas as pd, json, scipy.ndimage.uniform_filter |             |                            |
|        | , scipy.ndimage.variance, matplotlib.pyplot as plt``. |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Select inline Matplotlib backend and set theme:       | C02         | HLR-13                     |
| R-02** | ``dark_background``, monospace font, axes edge        |             |                            |
|        | ``#00FFCC``, axes line width 1.2, grid ``#1A3344``,   |             |                            |
|        | linestyle ``--``, alpha 0.5.                          |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print initialization banner                           | C02         | HLR-14                     |
| R-03** | ``⚡ [AETHER-SYSTEMS] Prepro                          |             |                            |
|        | cessing Environment & Aerospace Theme Initialized!``. |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Call ``np.random.seed(42)`` before any random draw.   | C04         | HLR-15                     |
| R-04** |                                                       |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Create                                                | C04         | HLR-01                     |
| R-05** | ``timestamp = p                                       |             |                            |
|        | d.date_range("2026-08-01","2026-09-07", periods=35)`` |             |                            |
|        | (inclusive endpoints, constant step 1 d 02 h 07 min   |             |                            |
|        | 03.53 s).                                             |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Draw, in this exact order, 35 samples each from       | C04         | HLR-01, HLR-15             |
| R-06** | uniform distributions: ``s1_vv_db`` U(−18, −8);       |             |                            |
|        | ``s1_vh_db`` U(−25, −14); ``s2_cloud_cover_pct`` U(0, |             |                            |
|        | 90); ``s2_b04_red`` U(0.02, 0.18); ``s2_b08_nir``     |             |                            |
|        | U(0.20, 0.52).                                        |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Set ``dem_elevation_m`` to constant 18.5 for all      | C04         | HLR-01                     |
| R-07** | records.                                              |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Compute                                               | C04         | HLR-02                     |
| R-08** | ``ndvi = (s2                                          |             |                            |
|        | _b08_nir − s2_b04_red) / (s2_b08_nir + s2_b04_red)``. |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Create ``/kaggle/working/data_raw``                   | C04         | HLR-03                     |
| R-09** | (``exist_ok=True``) and write ``df_raw`` to           |             |                            |
|        | ``stac_telemetry_raw.csv`` with ``index=False``.      |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print record count and output path; display first 3   | C04         | HLR-14                     |
| R-10** | rows (``head(3)``).                                   |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Copy ``df_raw`` to ``df_qc``; set                     | C06         | HLR-04                     |
| R-11** | ``optical_qc_pass = (s2_cloud_cover_pct <= 50.0)``    |             |                            |
|        | (threshold inclusive).                                |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Set                                                   | C06         | HLR-04                     |
| R-12** | ``ndvi_masked = where(optical_qc_pass, ndvi, NaN)``.  |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Compute ``valid_count = sum(optical_qc_pass)``,       | C06         | HLR-05                     |
| R-13** | ``corrupted_count = N − valid_count``; print totals   |             |                            |
|        | and percentages to 1 decimal.                         |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Plot 1 per Section 13.1 (raw NDVI, masked NDVI, red   | C08         | HLR-13                     |
| R-14** | vertical lines at each masked timestamp, legend,      |             |                            |
|        | diagnostics box).                                     |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Define ``apply_lee_filter_1d(series, window_size=3)`` | C10         | HLR-06                     |
| R-15** | per Section 8.4 (local mean, local mean of squares,   |             |                            |
|        | variance clamped ≥ 0,                                 |             |                            |
|        | ``noise_var = mean(var) + 1e-6``, weight, filtered    |             |                            |
|        | output).                                              |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Apply it to ``df_qc['s1_vv_db']`` with                | C10         | HLR-06, HLR-14             |
| R-16** | ``window_size=3``, store as ``s1_vv_lee``; print raw  |             |                            |
|        | and filtered sample variance (4 decimals).            |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Plot 2 per Section 13.2 (raw VV, Lee VV, diagnostics  | C12         | HLR-13                     |
| R-17** | box with variance values and percentage reduction).   |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Compute ``split_idx = int(len(df_qc)*0.8)``;          | C14         | HLR-07                     |
| R-18** | ``train_slice = iloc[:split_idx]``,                   |             |                            |
|        | ``test_slice = iloc[split_idx:]``.                    |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Compute ``train_mean``, ``train_std`` (pandas, ddof = | C14         | HLR-08                     |
| R-19** | 1) of ``s1_vv_lee`` on ``train_slice``; set           |             |                            |
|        | ``s1                                                  |             |                            |
|        | _vv_normalized = (s1_vv_lee − train_mean)/train_std`` |             |                            |
|        | for all rows.                                         |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print the “Data Leakage Audit Report (Day 3)” (split  | C14         | HLR-14                     |
| R-20** | index, train/test frame counts, normalization         |             |                            |
|        | statistics, status line).                             |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Define ``feature_cols``; copy ``df_qc`` to            | C16         | HLR-07                     |
| R-21** | ``df_proc``; set ``SPLIT_RATIO = 0.8``;               |             |                            |
|        | ``split_index = int(len(df_proc)*SPLIT_RATIO)``;      |             |                            |
|        | ``train_df = df_proc.iloc[:split_index]``;            |             |                            |
|        | ``test_df = df_proc.iloc[split_index:]``.             |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print temporal split bounds with first/last dates     | C16         | HLR-14                     |
| R-22** | (``%Y-%m-%d``) of each window.                        |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | For each of ``s1_vv_lee, s1_vh_db, dem_elevation_m``: | C18         | HLR-08                     |
| R-23** | ``mean_val = train_df[col].mean()``;                  |             |                            |
|        | ``std_val = train_df[col].std() + 1e-6``; store in    |             |                            |
|        | ``train_stats``; add                                  |             |                            |
|        | ``<col>_zscore = (df_proc[col] − mean_val)/std_val``  |             |                            |
|        | to ``scaled_df``.                                     |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Compute ``ndvi_min``, ``ndvi_max`` over non-NaN       | C18         | HLR-08                     |
| R-24** | ``ndvi_masked`` in ``train_df``; store in             |             |                            |
|        | ``train_stats['ndvi_masked']``; add                   |             |                            |
|        | ``ndvi_minmax = (n                                    |             |                            |
|        | dvi_masked − ndvi_min)/(ndvi_max − ndvi_min + 1e-6)`` |             |                            |
|        | to ``scaled_df``. NaNs propagate.                     |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print scaler bounds dictionary.                       | C18         | HLR-14                     |
| R-25** |                                                       |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Plot 3 per Section 13.3 (two histograms, Z-score      | C20         | HLR-13                     |
| R-26** | diagnostics box, suptitle).                           |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Plot 4 per Section 13.4 (scaled VV, scaled NDVI,      | C22         | HLR-13                     |
| R-27** | dashed train/test boundary at                         |             |                            |
|        | ``df_proc.iloc[split_index]['timestamp']``).          |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Assert                                                | C24         | HLR-10                     |
| R-28** | ``scaled_df[['s1_vv_lee_zscore','s1_vh_db_zscore','d  |             |                            |
|        | em_elevation_m_zscore']].isnull().sum().sum() == 0``. |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Assert ``abs(train_z.mean()) < 1e-4`` and             | C24         | HLR-10                     |
| R-29** | ``abs(train_z.std() − 1.0) < 1e-2`` for               |             |                            |
|        | ``s1_vv_lee_zscore`` over the training rows.          |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Assert                                                | C24         | HLR-10                     |
| R-30** | ``len(train_df) + len(test_df) == len(scaled_df)``.   |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print the “Preprocessing Final Audit Report” with     | C24         | HLR-14, HLR-10             |
| R-31** | three PASSED lines (printed only if assertions pass). |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Create ``/kaggle/working/data_processed``             | C26         | HLR-11                     |
| R-32** | (``exist_ok=True``); write ``scaled_df`` to           |             |                            |
|        | ``preprocessed_telemetry.csv`` (``index=False``).     |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Build manifest dict with keys ``Project``,            | C26         | HLR-12                     |
| R-33** | ``engine``, ``notebook``, ``temporal_split_index``,   |             |                            |
|        | ``train_sample_count``, ``test_sample_count``,        |             |                            |
|        | ``feature_scaler_parameters``; write JSON             |             |                            |
|        | (``indent=2``) to ``scaler_manifest.json``.           |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+
| **LL   | Print completion banner with the two output paths and | C26         | HLR-14                     |
| R-34** | the “Ready for Notebook 03” line.                     |             |                            |
+--------+-------------------------------------------------------+-------------+----------------------------+

7.3 Derived Requirements (DR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Derived requirements are behaviors present in the code that are **not directly traceable** to an HLR text. In
DO-178C practice they must be reviewed for impact on the system-level assessment.

+-----+-------------------------------------------------------------+--------+------------------------------+
| ID  | Derived requirement (as implemented)                        | Cell   | Impact assessment            |
+=====+=============================================================+========+==============================+
| **D | ``uniform_filter`` operates with its default boundary mode  | C10    | Edge values (index 0 and 34) |
| R-0 | ``reflect``; edge samples therefore use mirrored neighbors. |        | are smoothed using a         |
| 1** |                                                             |        | duplicated sample. Low       |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | Local variance is clamped to ≥ 0 with ``np.maximum`` to     | C10    | Numerical safety. None       |
| R-0 | remove negative round-off.                                  |        |                              |
| 2** |                                                             |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | Lee noise variance σn² is estimated as                      | C10    | Introduces cross-partition   |
| R-0 | ``mean(local variance) + 1e-6`` over the **entire** series  |        | dependence (PR-03). **High** |
| 3** | (35 samples, both partitions).                              |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | A 1e-6 epsilon is added to every Z-score standard deviation | C18    | Prevents division by zero;   |
| R-0 | and to the Min-Max denominator.                             |        | yields Z-std marginally <    |
| 4** |                                                             |        | 1.0 and a constant-feature   |
|     |                                                             |        | Z-score of exactly 0         |
|     |                                                             |        | (PR-06). Low                 |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | Cloud-masked NDVI values remain NaN in ``ndvi_minmax``;     | C18    | 16 NaN in the exported file  |
| R-0 | they are neither dropped nor interpolated.                  |        | (PR-05). Medium              |
| 5** |                                                             |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | ``s1_vv_normalized`` (C14) is an additional exported        | C14,   | Redundant column in exported |
| R-0 | column, near-duplicate of ``s1_vv_lee_zscore``.             | C26    | artifact (PR-08). Low        |
| 6** |                                                             |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | ``s1_vh_db`` is **not** despeckled; Z-score is applied to   | C18    | Asymmetric treatment of      |
| R-0 | raw VH.                                                     |        | polarizations (PR-11).       |
| 7** |                                                             |        | Medium                       |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | ``s2_cloud_cover_pct`` and ``s2_b04_red``, ``s2_b08_nir``,  | C26    | Downstream must select the   |
| R-0 | ``ndvi`` (unmasked), ``s1_vv_db`` are passed through        |        | correct columns. Low         |
| 8** | unscaled to the export.                                     |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | Timestamps are timezone-naive although axes are labeled     | C04,   | Labeling ambiguity (PR-10).  |
| R-0 | UTC.                                                        | C08    | Low                          |
| 9** |                                                             |        |                              |
+-----+-------------------------------------------------------------+--------+------------------------------+
| **D | The split index is computed twice independently             | C14,   | Duplication; consistency     |
| R-1 | (``split_idx`` in C14, ``split_index`` in C16) with the     | C16    | holds only while both        |
| 0** | same formula.                                               |        | formulas stay identical      |
|     |                                                             |        | (PR-08). Low                 |
+-----+-------------------------------------------------------------+--------+------------------------------+

7.4 Non-Functional Requirements and Constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------+--------------------------------------------------------------------------+----------------------+
| ID       | Requirement / constraint                                                 | Status               |
+==========+==========================================================================+======================+
| **       | The notebook shall run with no internet access and no attached datasets. | Met [NB]             |
| NFR-01** |                                                                          |                      |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | The notebook shall run on CPU only.                                      | Met [NB]             |
| NFR-02** |                                                                          |                      |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | The notebook shall execute without raised exceptions in a fresh kernel   | Met in saved run (no |
| NFR-03** | when cells are run in order.                                             | error outputs) [NB]; |
|          |                                                                          | fresh-kernel run not |
|          |                                                                          | independently        |
|          |                                                                          | executed on Kaggle   |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | Output paths shall be writable under ``/kaggle/working``.                | Met on Kaggle; **not |
| NFR-04** |                                                                          | portable** to other  |
|          |                                                                          | hosts (PR-12)        |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | Runtime shall be negligible (N = 35; vectorized NumPy/pandas).           | Met (no timing       |
| NFR-05** |                                                                          | recorded)            |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | Cells shall be executed strictly in order (state shared via kernel       | Constraint           |
| NFR-06** | namespace).                                                              |                      |
+----------+--------------------------------------------------------------------------+----------------------+
| **       | Visual style shall use the project “Aerospace” dark theme.               | Met                  |
| NFR-07** |                                                                          |                      |
+----------+--------------------------------------------------------------------------+----------------------+

7.5 Interface Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

IF-01 — Input data contract (``df_raw``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+-----------------+---------------+-------------+-------------------------------------------+---------------+
| Column          | dtype         | Unit        | Generator / range                         | Notes         |
+=================+===============+=============+===========================================+===============+
| ``timestamp``   | datetime64    | (naive,     | 35 points 2026-08-01 → 2026-09-07         | step ≈ 26 h   |
|                 |               | labeled     | inclusive                                 | 07 min 03.5 s |
|                 |               | UTC)        |                                           |               |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``s1_vv_db``    | float64       | dB          | U(−18.0, −8.0)                            | Sentinel-1 VV |
|                 |               |             |                                           | backscatter   |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``s1_vh_db``    | float64       | dB          | U(−25.0, −14.0)                           | Sentinel-1 VH |
|                 |               |             |                                           | backscatter   |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``s2_cl         | float64       | %           | U(0.0, 90.0)                              | Sentinel-2    |
| oud_cover_pct`` |               |             |                                           | cloud cover   |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``s2_b04_red``  | float64       | reflectance | U(0.02, 0.18)                             | Band 4        |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``s2_b08_nir``  | float64       | reflectance | U(0.20, 0.52)                             | Band 8        |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``de            | float64       | m           | constant 18.5                             | elevation     |
| m_elevation_m`` |               |             |                                           |               |
+-----------------+---------------+-------------+-------------------------------------------+---------------+
| ``ndvi``        | float64       | –           | derived                                   | range [−1,    |
|                 |               |             |                                           | 1]; with      |
|                 |               |             |                                           | these draws   |
|                 |               |             |                                           | always        |
|                 |               |             |                                           | positive      |
+-----------------+---------------+-------------+-------------------------------------------+---------------+

IF-02 — Output data contract (``preprocessed_telemetry.csv``, 16 columns, 35 rows, in this order)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

== ========================== =========== =========================================== ============
#  Column                     Origin cell Meaning                                     NaN possible
== ========================== =========== =========================================== ============
1  ``timestamp``              C04         acquisition time                            no
2  ``s1_vv_db``               C04         raw VV (dB)                                 no
3  ``s1_vh_db``               C04         raw VH (dB)                                 no
4  ``s2_cloud_cover_pct``     C04         cloud cover (%)                             no
5  ``s2_b04_red``             C04         red reflectance                             no
6  ``s2_b08_nir``             C04         NIR reflectance                             no
7  ``dem_elevation_m``        C04         elevation (m)                               no
8  ``ndvi``                   C04         unmasked NDVI                               no
9  ``optical_qc_pass``        C06         boolean QC flag                             no
10 ``ndvi_masked``            C06         NDVI, NaN where QC failed                   **yes (16)**
11 ``s1_vv_lee``              C10         Lee-filtered VV (dB)                        no
12 ``s1_vv_normalized``       C14         VV-Lee Z-score using ddof=1 std, no epsilon no
13 ``s1_vv_lee_zscore``       C18         VV-Lee Z-score, std + 1e-6                  no
14 ``s1_vh_db_zscore``        C18         VH Z-score                                  no
15 ``dem_elevation_m_zscore`` C18         DEM Z-score (all 0.0)                       no
16 ``ndvi_minmax``            C18         NDVI Min-Max (train bounds)                 **yes (16)**
== ========================== =========== =========================================== ============

IF-03 — Scaler manifest (``scaler_manifest.json``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

   {
     "Project": "THE MRIDANSH",
     "engine": "AETHER-MRID1607X",
     "notebook": "02_preprocessing.ipynb",
     "temporal_split_index": 28,
     "train_sample_count": 28,
     "test_sample_count": 7,
     "feature_scaler_parameters": {
       "s1_vv_lee":       {"mean": -13.510027922701811, "std": 2.197309599467909},
       "s1_vh_db":        {"mean": -19.648007479125024, "std": 3.4012699200375653},
       "dem_elevation_m": {"mean": 18.5,                "std": 1e-06},
       "ndvi_masked":     {"min": 0.18364952752897318,  "max": 0.7692757597519014}
     }
   }

Values from the saved C18 output [NB]. Note that ``std`` already includes the +1e-6 epsilon (DR-04) and that
``ndvi_masked`` bounds are computed over the 14 QC-passed training frames [AN].

IF-04 — Intermediate raw artifact
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``/kaggle/working/data_raw/stac_telemetry_raw.csv``: the 8 columns of IF-01, 35 rows, no index column.

8. Software Design Description
------------------------------

8.1 Initialization (C02)
~~~~~~~~~~~~~~~~~~~~~~~~

-  Imports (LLR-01) and theme (LLR-02).
-  ``%matplotlib inline`` makes figures render in the output area.
-  Unused imports: ``sys``, ``scipy.ndimage.variance`` (PR-08). ``json`` is imported again in C26 (harmless).

8.2 Step 1 — Telemetry Provisioning (C03, C04)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Narrative claim [NB C03]:** loads ``stac_telemetry_raw.csv`` from Notebook 01. **Actual implementation [NB
C04]:** a seeded in-memory generator, with the comment *“Bypasses File Path Issues”*.

Algorithm:

1. ``np.random.seed(42)``.
2. Build timestamp vector (35 evenly spaced instants).
3. Draw five uniform vectors in the fixed order of LLR-06. **The order is part of the design**: changing it
   changes every downstream number.
4. Set DEM constant.
5. Compute NDVI.
6. Create directory, write CSV.
7. Print counts and ``head(3)``.

Reference output (first 3 rows) [NB]:

=== ====================== ========== ========== ========= ======== ======== ==== ========
idx timestamp              s1_vv_db   s1_vh_db   cloud %   b04      b08      dem  ndvi
=== ====================== ========== ========== ========= ======== ======== ==== ========
0   2026-08-01 00:00:00    −14.254599 −16.107629 69.502029 0.059887 0.507983 18.5 0.789083
1   2026-08-02 02:07:03.53 −8.492857  −21.649249 17.884411 0.085661 0.280570 18.5 0.532202
2   2026-08-03 04:14:07.06 −10.680061 −23.925607 0.496991  0.140888 0.359120 18.5 0.436456
=== ====================== ========== ========== ========= ======== ======== ==== ========

8.3 Step 2 — Sentinel-2 Cloud Quality Control (C05, C06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. math::

   \text{QC}_i = \begin{cases}\text{True} & c_i \le 50.0\\ \text{False} & c_i > 50.0\end{cases}\qquad
   \text{NDVI}^{\text{masked}}_i = \begin{cases}\text{NDVI}_i & \text{QC}_i\\ \text{NaN} & \text{otherwise}\end{cases}

where ``c_i`` is ``s2_cloud_cover_pct``. The mask removes information **by value**, not by row: all 35 rows
persist.

Observed result [NB]: **19 / 35 pass (54.3 %)**, **16 / 35 masked (45.7 %)**.

Design remark: the markdown calls this “SCL Bitmasking” (C01, C27), but no SCL band is read; the mask is a
scalar threshold on a pre-aggregated cloud-percentage (PR-02).

8.4 Step 3 — Sentinel-1 VV Lee Speckle Filter (C09, C10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specified formula (C01):

.. math:: \hat{I} = \bar{I} + W\,(I-\bar{I}),\qquad W=\frac{\operatorname{Var}(I)}{\operatorname{Var}(I)+\sigma_n^2}

Implemented algorithm ``apply_lee_filter_1d(series, window_size=3)``:

==== ===================== ===================================
Step Operation             Code
==== ===================== ===================================
1    Cast to float64 NumPy ``series.to_numpy(dtype=float)``
2    Local mean ``Ī``      ``uniform_filter(x, size=3)``
3    Local mean of squares ``uniform_filter(x**2, size=3)``
4    Local variance        ``var = mean_sq − mean**2``
5    Clamp                 ``var = np.maximum(var, 0)``
6    Noise variance        ``noise_var = np.mean(var) + 1e-6``
7    Weight                ``W = var / (var + noise_var)``
8    Output                ``mean + W * (x − mean)``
==== ===================== ===================================

Properties:

-  1-D **temporal** window of 3 samples (centered, boundary mode ``reflect``), not a 2-D spatial window.
-  Applied in **dB (logarithmic) domain** to VV only.
-  σn² is a single scalar for the whole series (≈ 5.8118 dB² [AN]); it is *not* derived from the number of
   looks (ENL).
-  Because the window is centered, the output at index *k* uses samples *k−1, k, k+1*.

Observed result [NB]: raw variance **9.0643** → filtered variance **5.7011**. Relative variance reduction =
(9.0643 − 5.7011)/9.0643 = **37.1 %** [AN, matches the figure annotation formula].

8.5 Step 4 — Day-3 Leakage Invariant Check (C13, C14)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. ``split_idx = int(35 × 0.8) = 28``.
2. ``train_slice = rows 0–27``, ``test_slice = rows 28–34``.
3. ``train_mean = −13.51``, ``train_std = 2.20`` (of ``s1_vv_lee``, train rows only).
4. ``s1_vv_normalized`` computed for all 35 rows.
5. Report printed. Line 5 is a **hard-coded string** ``PASSED (Zero Future Leakage)`` and is not computed from
   any check (PR-03, PR-07).

8.6 Part 2 — Temporal Split Definition (C15, C16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``split_index = 28``; train = 28 frames (2026-08-01 → 2026-08-30); test = 7 frames (2026-08-31 → 2026-09-07)
[NB].

The printed labels ``t <= 28`` (train) and ``t > 28`` (test) are **off by one** relative to the Python slicing
used: train covers indices 0…27 (``t < 28``), test covers 28…34 (``t ≥ 28``) (PR-04).

``feature_cols = ['s1_vv_lee','s1_vh_db','ndvi_masked','s2_cloud_cover_pct','dem_elevation_m']`` is defined
but never used (PR-08).

8.7 Step 5 — Zero-Leakage Feature Normalization (C17, C18)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Z-score for ``col ∈ {s1_vv_lee, s1_vh_db, dem_elevation_m}``:

.. math:: z = \frac{x-\mu_{\text{train}}}{\sigma_{\text{train}}+10^{-6}}

Min-Max for NDVI:

.. math:: \text{ndvi\_minmax}=\frac{\text{ndvi\_masked}-\min_{\text{train}}}{\max_{\text{train}}-\min_{\text{train}}+10^{-6}}

with ``min``/``max`` over non-NaN training values (14 values [AN]).

Observed parameters [NB]:

=================== ================= ==============================
Feature             Parameter 1       Parameter 2
=================== ================= ==============================
``s1_vv_lee``       mean = −13.510028 std = 2.197310
``s1_vh_db``        mean = −19.648007 std = 3.401270
``dem_elevation_m`` mean = 18.5       std = 1e-06 (constant feature)
``ndvi_masked``     min = 0.183650    max = 0.769276
=================== ================= ==============================

Behavioral notes:

-  Test-period NDVI is **not clipped**; it can fall outside [0, 1] for other data. With the present draws,
   test ``ndvi_minmax`` lies in [0.3519, 0.8927] [AN].
-  NaN positions of ``ndvi_masked`` carry through to ``ndvi_minmax`` (14 train + 2 test = 16) [AN].
-  ``dem_elevation_m_zscore`` is identically 0 because the feature is constant (PR-06).

8.8 Step 6 — Integrity Audit (C23, C24)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===== ================================================ ===============
Check Assertion                                        Observed
===== ================================================ ===============
1     nulls in 3 Z-score columns == 0                  PASSED
2a    ``abs(train_z.mean()) < 1e-4``                   PASSED
2b    ``abs(train_z.std() − 1.0) < 1e-2``              PASSED
3     ``len(train_df)+len(test_df) == len(scaled_df)`` PASSED (28 + 7)
===== ================================================ ===============

Failure behavior: ``AssertionError`` with message, halting cell execution; the “PASSED” lines after each
assertion are not reached.

Coverage limits of this audit:

-  ``ndvi_minmax`` (which contains NaN) is not checked.
-  Check 2 recomputes a property that is true by construction of Z-scoring on the same rows; it does **not**
   prove that the scaler was fitted without test data (PR-07).

8.9 Step 7 — Export (C25, C26)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create directory ``/kaggle/working/data_processed``.
2. ``scaled_df.to_csv(..., index=False)``.
3. Build and ``json.dump`` the manifest (NumPy ``float64`` values serialize because ``np.float64`` subclasses
   Python ``float``).
4. Print completion banner.

No post-write existence/size/readback check is performed.

8.10 Design Parameters (Complete Constant Table)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

====================== ================================== ======== =======
Parameter              Value                              Cell     Used by
====================== ================================== ======== =======
Random seed            42                                 C04      HLR-15
Record count           35                                 C04      HLR-01
Date range             2026-08-01 … 2026-09-07            C04      HLR-01
DEM constant           18.5 m                             C04      HLR-01
VV range               U(−18, −8) dB                      C04      HLR-01
VH range               U(−25, −14) dB                     C04      HLR-01
Cloud range            U(0, 90) %                         C04      HLR-01
Red range              U(0.02, 0.18)                      C04      HLR-01
NIR range              U(0.20, 0.52)                      C04      HLR-01
Cloud threshold        50.0 % (inclusive pass)            C06      HLR-04
Lee window             3 samples                          C10      HLR-06
Lee ε (noise variance) 1e-6                               C10      DR-03
Split ratio            0.8                                C14, C16 HLR-07
Scaling ε              1e-6                               C18      DR-04
Mean tolerance         1e-4                               C24      HLR-10
Std tolerance          1e-2                               C24      HLR-10
Raw dir                ``/kaggle/working/data_raw``       C04      HLR-03
Processed dir          ``/kaggle/working/data_processed`` C26      HLR-11
====================== ================================== ======== =======

9. Software Verification
------------------------

9.1 Verification Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~

-  **Requirements-based testing** by executing the notebook and comparing saved outputs against requirement
   statements (method T).
-  **Inspection** of source text for requirements that cannot be tested by output alone (method I).
-  **Analysis** for properties such as leakage (method A).
-  **Demonstration** for figures (method D).
-  Because the notebook contains **no test cell** other than three ``assert`` statements, additional offline
   analyses were performed [AN] and are clearly labeled.

9.2 Verification Cases and Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| ID  | Verification case             | Method     | Expected       | Observed       | Result     | Tag   |
+=====+===============================+============+================+================+============+=======+
| **V | Environment initializes       | T          | Banner         | Banner printed | **PASS**   | NB    |
| C-0 | without error                 |            | printed, no    |                |            |       |
| 1** |                               |            | error          |                |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Raw record count              | T          | 35             | “35 temporal   | **PASS**   | NB    |
| C-0 |                               |            |                | records”       |            |       |
| 2** |                               |            |                |                |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Determinism of first rows     | T/A        | Fixed values   | Row 0: VV      | **PASS**   | NB,   |
| C-0 |                               |            | for seed 42    | −14.254599,    |            | AN    |
| 3** |                               |            |                | cloud          |            |       |
|     |                               |            |                | 69.502029,     |            |       |
|     |                               |            |                | NDVI 0.789083  |            |       |
|     |                               |            |                | (reproduced    |            |       |
|     |                               |            |                | offline)       |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | QC pass/mask counts           | T          | pass + masked  | 19 (54.3 %) +  | **PASS**   | NB    |
| C-0 |                               |            | = 35           | 16 (45.7 %) =  |            |       |
| 4** |                               |            |                | 35             |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Masked NDVI NaN count equals  | A          | 16             | 16 NaN in      | **PASS**   | AN    |
| C-0 | QC failures                   |            |                | `              |            |       |
| 5** |                               |            |                | `ndvi_masked`` |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Lee filter reduces variance   | T          | filtered var < | 9.0643 →       | **PASS**   | NB,   |
| C-0 |                               |            | raw var        | 5.7011 (−37.1  |            | AN    |
| 6** |                               |            |                | %)             |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Partition sizes and           | T          | 28 / 7, train  | 28 / 7;        | **PASS**   | NB    |
| C-0 | chronology                    |            | dates precede  | 08-01→08-30    |            |       |
| 7** |                               |            | test dates     | and            |            |       |
|     |                               |            |                | 08-31→09-07    |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Step-4 and Step-5 train stats | A          | same mean/std  | −13.51 / 2.20  | **PASS**   | NB    |
| C-0 | consistent                    |            |                | vs −13.510028  |            |       |
| 8** |                               |            |                | / 2.197310     |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Train Z-mean ≈ 0, Z-std ≈ 1   | T          | tolerances     | assertions     | **PASS**   | NB    |
| C-0 |                               |            | 1e-4 / 1e-2    | passed         |            |       |
| 9** |                               |            |                |                |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | No nulls in Z-score columns   | T          | 0              | assertion      | **PASS**   | NB    |
| C-1 |                               |            |                | passed         |            |       |
| 0** |                               |            |                |                |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Partition row conservation    | T          | 35             | assertion      | **PASS**   | NB    |
| C-1 |                               |            |                | passed (28+7)  |            |       |
| 1** |                               |            |                |                |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Artifacts written             | T          | two files,     | paths printed  | **PASS     | NB    |
| C-1 |                               |            | paths printed  | (no existence  | (weak)**   |       |
| 2** |                               |            |                | check)         |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Four figures rendered         | D          | 4 figures      | 4              | **PASS**   | NB    |
| C-1 |                               |            |                | ``image/png``  |            |       |
| 3** |                               |            |                | outputs        |            |       |
|     |                               |            |                | present        |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Statistic offline             | A          | printed values | variances,     | **PASS**   | AN    |
| C-1 | reproduction                  |            | reproduce      | counts, scaler |            |       |
| 4** |                               |            |                | bounds         |            |       |
|     |                               |            |                | reproduce      |            |       |
|     |                               |            |                | exactly        |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | **Leakage independence** of   | A          | no change      | Raising raw VV | **FAIL**   | AN    |
| C-1 | SAR stage: changing a *test*  |            |                | at test index  |            |       |
| 5** | sample must not alter any     |            |                | 28 by +5 dB    |            |       |
|     | *train* feature               |            |                | changes train  |            |       |
|     |                               |            |                | feature        |            |       |
|     |                               |            |                | ``s            |            |       |
|     |                               |            |                | 1_vv_lee[27]`` |            |       |
|     |                               |            |                | by **+0.8188   |            |       |
|     |                               |            |                | dB**; also σn² |            |       |
|     |                               |            |                | uses all 35    |            |       |
|     |                               |            |                | samples        |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+
| **V | Completeness of exported      | A          | 0 NaN in       | `              | **FAIL /   | AN    |
| C-1 | NaN-free features             |            | exported model | `ndvi_minmax`` | infor      |       |
| 6** |                               |            | features       | has 16 NaN     | mational** |       |
|     |                               |            |                | (not covered   |            |       |
|     |                               |            |                | by audit)      |            |       |
+-----+-------------------------------+------------+----------------+----------------+------------+-------+

9.3 Requirements-Based Coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All 15 HLR and 34 LLR have at least one verification case or inspection (Section 10.3). Two HLR (HLR-09 and,
with limits, HLR-10) carry verification findings.

9.4 Structural Coverage
~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------+--------------------------------------------------+
| Measure                                                 | Result                                           |
+=========================================================+==================================================+
| Code cells executed                                     | 13 / 13 (execution counts 30–42) [NB]            |
+---------------------------------------------------------+--------------------------------------------------+
| Function coverage                                       | 1 / 1 function (``apply_lee_filter_1d``)         |
|                                                         | executed                                         |
+---------------------------------------------------------+--------------------------------------------------+
| Statement coverage                                      | not instrumented; code is essentially            |
|                                                         | straight-line and all code cells ran             |
+---------------------------------------------------------+--------------------------------------------------+
| Branch / MC/DC coverage                                 | not measured. The only data-dependent selection  |
|                                                         | is ``np.where`` (both outcomes exercised: 19     |
|                                                         | True / 16 False). Assertion failure paths (3)    |
|                                                         | were **not** exercised                           |
+---------------------------------------------------------+--------------------------------------------------+
| Dead code                                               | unused: ``sys``, ``variance``, ``feature_cols``, |
|                                                         | ``s1_vv_normalized`` (as a model input)          |
+---------------------------------------------------------+--------------------------------------------------+

9.5 Recommended Additional Verification (Not Yet Executed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+--------------+---------------------------------------------------------+----------------------------------+
| ID           | Proposed test                                           | Targets                          |
+==============+=========================================================+==================================+
| **VP-01**    | Boundary test of ``cloud == 50.0`` and ``50.0001``      | LLR-11                           |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-02**    | Negative tests forcing each of the 3 assertions to fail | LLR-28..30                       |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-03**    | Leakage test: perturb test rows, assert train features  | HLR-09                           |
|              | and scaler params bit-identical                         |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-04**    | ``ndvi_masked`` all-NaN training set → graceful error   | LLR-24                           |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-05**    | Constant-column test (``dem_elevation_m``) → documented | DR-04                            |
|              | behavior                                                |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-06**    | Lee filter reference test on a known synthetic signal   | LLR-15                           |
|              | (constant → unchanged; step edge → preserved)           |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-07**    | File existence, row/column count and ``read_csv``       | HLR-11, HLR-12                   |
|              | round-trip of both artifacts                            |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-08**    | Manifest schema validation and JSON-reload scaling      | HLR-12                           |
|              | reproduces ``scaled_df``                                |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-09**    | Fresh-kernel “Restart & Run All” regression with pinned | NFR-03, HLR-15                   |
|              | library versions                                        |                                  |
+--------------+---------------------------------------------------------+----------------------------------+
| **VP-10**    | Assert 16 columns and exact column order in the export  | IF-02                            |
+--------------+---------------------------------------------------------+----------------------------------+

10. Traceability
----------------

10.1 HLR → LLR → Cell → Verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

====== ====================================== ======================= ==========================
HLR    LLR                                    Cells                   Verification
====== ====================================== ======================= ==========================
HLR-01 LLR-05, 06, 07                         C04                     VC-02, VC-03
HLR-02 LLR-08                                 C04                     VC-03 (NDVI value), VC-14
HLR-03 LLR-09                                 C04                     VC-02 (path printed)
HLR-04 LLR-11, 12                             C06                     VC-04, VC-05
HLR-05 LLR-13                                 C06                     VC-04
HLR-06 LLR-15, 16                             C10                     VC-06, VC-14
HLR-07 LLR-18, 21                             C14, C16                VC-07
HLR-08 LLR-19, 23, 24                         C14, C18                VC-08, VC-09
HLR-09 LLR-15, 19, 23, 24 (and DR-03)         C10, C14, C18           VC-15 (**FAIL**)
HLR-10 LLR-28, 29, 30, 31                     C24                     VC-09, VC-10, VC-11, VC-16
HLR-11 LLR-32                                 C26                     VC-12
HLR-12 LLR-33                                 C26                     VC-12
HLR-13 LLR-02, 14, 17, 26, 27                 C02, C08, C12, C20, C22 VC-13
HLR-14 LLR-03, 10, 13, 16, 20, 22, 25, 31, 34 C02–C26                 VC-01 … VC-12
HLR-15 LLR-01, 04, 06                         C02, C04                VC-03, VC-14
====== ====================================== ======================= ==========================

10.2 Derived Requirement → Cell → Problem Report
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===== ======== =================
DR    Cell     Problem Report
===== ======== =================
DR-01 C10      — (informational)
DR-02 C10      —
DR-03 C10      PR-03
DR-04 C18      PR-06
DR-05 C18      PR-05
DR-06 C14, C26 PR-08
DR-07 C18      PR-11
DR-08 C26      —
DR-09 C04, C08 PR-10
DR-10 C14, C16 PR-08
===== ======== =================

10.3 Reverse Trace: Cell → Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

==== ============== =============
Cell LLR            DR
==== ============== =============
C02  LLR-01, 02, 03 —
C04  LLR-04 … 10    DR-09
C06  LLR-11, 12, 13 —
C08  LLR-14         DR-09
C10  LLR-15, 16     DR-01, 02, 03
C12  LLR-17         —
C14  LLR-18, 19, 20 DR-06, 10
C16  LLR-21, 22     DR-10
C18  LLR-23, 24, 25 DR-04, 05, 07
C20  LLR-26         —
C22  LLR-27         —
C24  LLR-28 … 31    —
C26  LLR-32, 33, 34 DR-06, 08
==== ============== =============

*Markdown cells C00, C01, C03, C05, C07, C09, C11, C13, C15, C17, C19, C21, C23, C25, C27, C28 carry
documentation only and trace to no executable requirement; their claims are audited in Section 12 and Appendix
B.*

10.4 Trace Completeness Check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Every HLR has ≥ 1 LLR: **yes**.
-  Every LLR has a parent HLR: **yes**.
-  Every code cell maps to ≥ 1 LLR: **yes** (13/13).
-  Every DR is documented: **yes** (10).
-  Every HLR has ≥ 1 verification case: **yes**.

11. Requirements Compliance Summary
-----------------------------------

================== ====== ==============================================
Status             Count  HLR IDs
================== ====== ==============================================
Met                11     HLR-02, 03, 05, 07, 08, 10, 11, 12, 13, 14, 15
Met with deviation 3      HLR-01, 04, 06
Partially met      1      HLR-09
Not met            0      none
**Total**          **15** 
================== ====== ==============================================

*Notes:* “Met” for HLR-10 and HLR-13 carries documented limitations (PR-05, PR-07, PR-09, PR-10); HLR-08 and
HLR-15 are Met for the scaler parameters and for seeded determinism respectively (PR-03, PR-15 apply to
related aspects). The authoritative per-requirement status is Section 7.1.

**Overall conclusion:** the notebook executes as designed and meets its functional intent on synthetic data.
It **does not** satisfy its own strongest claim (“Zero Future Leakage”, HLR-09) because the Lee filtering
stage precedes and ignores the temporal split.

12. Problem Reports and Open Issues
-----------------------------------

Severity: **High** = invalidates a stated scientific/safety claim; **Medium** = affects data quality or
maintainability; **Low** = cosmetic / hygiene.

+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| ID  | Sev.    | Cell    | Finding     | Evidence      | Recommended corrective action                    |
+=====+=========+=========+=============+===============+==================================================+
| **P | High    | C03,    | Narrative   | C04 comment   | Label data as synthetic in the title; add a      |
| R-0 |         | C04     | says raw    | “Bypasses     | switch ``USE_REAL_DATA`` that reads the Notebook |
| 1** |         |         | data is     | File Path     | 01 CSV; keep the generator as a test fixture     |
|     |         |         | loaded from | Issues”;      |                                                  |
|     |         |         | Notebook 01 | ``np.ran      |                                                  |
|     |         |         | (``stac     | dom.uniform`` |                                                  |
|     |         |         | _telemetry_ | calls         |                                                  |
|     |         |         | raw.csv``), |               |                                                  |
|     |         |         | but the     |               |                                                  |
|     |         |         | code        |               |                                                  |
|     |         |         | generates   |               |                                                  |
|     |         |         | **synthetic |               |                                                  |
|     |         |         | uniform     |               |                                                  |
|     |         |         | random**    |               |                                                  |
|     |         |         | data (seed  |               |                                                  |
|     |         |         | 42).        |               |                                                  |
|     |         |         | Results are |               |                                                  |
|     |         |         | not real    |               |                                                  |
|     |         |         | satellite   |               |                                                  |
|     |         |         | ob          |               |                                                  |
|     |         |         | servations. |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Medium  | C01,    | “SCL        | Code C06      | Rename to “cloud-percentage threshold QC”, or    |
| R-0 |         | C05,    | Bitmasking” |               | implement SCL class masking (e.g. classes 3, 8,  |
| 2** |         | C06,    | is claimed, |               | 9, 10)                                           |
|     |         | C27     | but no SCL  |               |                                                  |
|     |         |         | band is     |               |                                                  |
|     |         |         | read;       |               |                                                  |
|     |         |         | filtering   |               |                                                  |
|     |         |         | is a scalar |               |                                                  |
|     |         |         | ``cloud_    |               |                                                  |
|     |         |         | pct <= 50`` |               |                                                  |
|     |         |         | rule.       |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | *       | C10,    | The Lee     | VC-15: +5 dB  | Split first; filter each partition separately    |
| R-0 | *High** | C14     | filter runs | perturbation  | (or use a causal / trailing window); estimate    |
| 3** |         |         | on the      | at index 28   | σn² from the training partition only; compute    |
|     |         |         | **entire**  | changes       | the leakage status from a test (VP-03), not a    |
|     |         |         | series      | ``s1          | literal string                                   |
|     |         |         | before the  | _vv_lee[27]`` |                                                  |
|     |         |         | split. (a)  | by 0.8188 dB  |                                                  |
|     |         |         | The         |               |                                                  |
|     |         |         | centered    |               |                                                  |
|     |         |         | 3-sample    |               |                                                  |
|     |         |         | window      |               |                                                  |
|     |         |         | mixes test  |               |                                                  |
|     |         |         | sample 28   |               |                                                  |
|     |         |         | into train  |               |                                                  |
|     |         |         | feature 27. |               |                                                  |
|     |         |         | (b) σn² =   |               |                                                  |
|     |         |         | mean local  |               |                                                  |
|     |         |         | variance of |               |                                                  |
|     |         |         | all 35      |               |                                                  |
|     |         |         | samples.    |               |                                                  |
|     |         |         | The “Zero   |               |                                                  |
|     |         |         | Future      |               |                                                  |
|     |         |         | Leakage”    |               |                                                  |
|     |         |         | statements  |               |                                                  |
|     |         |         | (C08 figure |               |                                                  |
|     |         |         | text, C14   |               |                                                  |
|     |         |         | printout,   |               |                                                  |
|     |         |         | C27) are    |               |                                                  |
|     |         |         | therefore   |               |                                                  |
|     |         |         | not         |               |                                                  |
|     |         |         | strictly    |               |                                                  |
|     |         |         | true.       |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C16     | Printed     | Output C16    | Print ``t < 28`` and ``t >= 28``                 |
| R-0 |         |         | bounds      |               |                                                  |
| 4** |         |         | ``t <= 28`` |               |                                                  |
|     |         |         | /           |               |                                                  |
|     |         |         | ``t > 28``  |               |                                                  |
|     |         |         | are off by  |               |                                                  |
|     |         |         | one         |               |                                                  |
|     |         |         | relative to |               |                                                  |
|     |         |         | slicing     |               |                                                  |
|     |         |         | (``[:28]``, |               |                                                  |
|     |         |         | ``[28:]``). |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Medium  | C18,    | NaNs are    | AN            | Either interpolate using training-only           |
| R-0 |         | C22,    | neither     |               | information or document NaN as intentional;      |
| 5** |         | C24     | dropped nor |               | extend audit to ``ndvi_minmax``; correct the     |
|     |         |         | in          |               | annotation                                       |
|     |         |         | terpolated, |               |                                                  |
|     |         |         | yet Plot 4  |               |                                                  |
|     |         |         | states      |               |                                                  |
|     |         |         | “Optical QC |               |                                                  |
|     |         |         | Int         |               |                                                  |
|     |         |         | erpolation: |               |                                                  |
|     |         |         | Cloud NaNs  |               |                                                  |
|     |         |         | Handled”.   |               |                                                  |
|     |         |         | ``nd        |               |                                                  |
|     |         |         | vi_minmax`` |               |                                                  |
|     |         |         | has 16 NaN  |               |                                                  |
|     |         |         | (14 train,  |               |                                                  |
|     |         |         | 2 test) and |               |                                                  |
|     |         |         | is outside  |               |                                                  |
|     |         |         | the Step-6  |               |                                                  |
|     |         |         | audit.      |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C18     | ``dem_el    | Manifest      | Exclude constant features from scaling or flag   |
| R-0 |         |         | evation_m`` | values        | them in manifest                                 |
| 6** |         |         | is constant |               |                                                  |
|     |         |         | (18.5). Std |               |                                                  |
|     |         |         | = 0 →       |               |                                                  |
|     |         |         | stored as   |               |                                                  |
|     |         |         | 1e-06;      |               |                                                  |
|     |         |         | Z-score ≡   |               |                                                  |
|     |         |         | 0.          |               |                                                  |
|     |         |         | Meaningless |               |                                                  |
|     |         |         | feature,    |               |                                                  |
|     |         |         | and the     |               |                                                  |
|     |         |         | stored      |               |                                                  |
|     |         |         | ``std`` is  |               |                                                  |
|     |         |         | the         |               |                                                  |
|     |         |         | epsilon,    |               |                                                  |
|     |         |         | not a real  |               |                                                  |
|     |         |         | deviation.  |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Medium  | C14,    | The “audit” | Source        | Replace by a perturbation-based leakage test     |
| R-0 |         | C24     | is partly   |               | (VP-03); compare scaler parameters with those    |
| 7** |         |         | ta          |               | recomputed from ``train_df`` only                |
|     |         |         | utological. |               |                                                  |
|     |         |         | Train       |               |                                                  |
|     |         |         | Z-mean = 0  |               |                                                  |
|     |         |         | and Z-std ≈ |               |                                                  |
|     |         |         | 1 hold by   |               |                                                  |
|     |         |         | c           |               |                                                  |
|     |         |         | onstruction |               |                                                  |
|     |         |         | and cannot  |               |                                                  |
|     |         |         | detect      |               |                                                  |
|     |         |         | test-data   |               |                                                  |
|     |         |         | leakage.    |               |                                                  |
|     |         |         | The “PASSED |               |                                                  |
|     |         |         | (Zero       |               |                                                  |
|     |         |         | Future      |               |                                                  |
|     |         |         | Leakage)”   |               |                                                  |
|     |         |         | line is a   |               |                                                  |
|     |         |         | hard-coded  |               |                                                  |
|     |         |         | ``print``.  |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C02,    | Hygiene:    | Source        | Remove or use; single source of truth for split  |
| R-0 |         | C14,    | unused      |               | index; drop redundant column                     |
| 8** |         | C16     | imports     |               |                                                  |
|     |         |         | (``sys``,   |               |                                                  |
|     |         |         | ``v         |               |                                                  |
|     |         |         | ariance``), |               |                                                  |
|     |         |         | unused      |               |                                                  |
|     |         |         | ``feat      |               |                                                  |
|     |         |         | ure_cols``, |               |                                                  |
|     |         |         | duplicate   |               |                                                  |
|     |         |         | ``json``    |               |                                                  |
|     |         |         | import,     |               |                                                  |
|     |         |         | split index |               |                                                  |
|     |         |         | computed    |               |                                                  |
|     |         |         | twice       |               |                                                  |
|     |         |         | (``s        |               |                                                  |
|     |         |         | plit_idx``, |               |                                                  |
|     |         |         | ``spli      |               |                                                  |
|     |         |         | t_index``), |               |                                                  |
|     |         |         | redundant   |               |                                                  |
|     |         |         | ``s1_vv_n   |               |                                                  |
|     |         |         | ormalized`` |               |                                                  |
|     |         |         | vs          |               |                                                  |
|     |         |         | ``s1_vv_l   |               |                                                  |
|     |         |         | ee_zscore`` |               |                                                  |
|     |         |         | exported.   |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Medium  | C01,    | Claims with | Source search | Delete or substantiate each claim (Appendix B)   |
| R-0 |         | C15,    | no          |               |                                                  |
| 9** |         | C21,    | co          |               |                                                  |
|     |         | C22,    | rresponding |               |                                                  |
|     |         | C27     | cod         |               |                                                  |
|     |         |         | e/evidence: |               |                                                  |
|     |         |         | “Pr         |               |                                                  |
|     |         |         | ecipitation |               |                                                  |
|     |         |         | forcing”    |               |                                                  |
|     |         |         | (Plot 4     |               |                                                  |
|     |         |         | text),      |               |                                                  |
|     |         |         | “           |               |                                                  |
|     |         |         | SAR-Optical |               |                                                  |
|     |         |         | channels    |               |                                                  |
|     |         |         | aligned to  |               |                                                  |
|     |         |         | common      |               |                                                  |
|     |         |         | spatial     |               |                                                  |
|     |         |         | grid”,      |               |                                                  |
|     |         |         | Bhadr       |               |                                                  |
|     |         |         | ak/Balasore |               |                                                  |
|     |         |         | grid        |               |                                                  |
|     |         |         | coordinates |               |                                                  |
|     |         |         | (21.1378°   |               |                                                  |
|     |         |         | N, 86.6874° |               |                                                  |
|     |         |         | E),         |               |                                                  |
|     |         |         | “preserving |               |                                                  |
|     |         |         | h           |               |                                                  |
|     |         |         | ydrological |               |                                                  |
|     |         |         | ground      |               |                                                  |
|     |         |         | b           |               |                                                  |
|     |         |         | oundaries”, |               |                                                  |
|     |         |         | “100 %      |               |                                                  |
|     |         |         | verified,   |               |                                                  |
|     |         |         | sci         |               |                                                  |
|     |         |         | entifically |               |                                                  |
|     |         |         | audited”,   |               |                                                  |
|     |         |         | Step 4 text |               |                                                  |
|     |         |         | citing (μ,  |               |                                                  |
|     |         |         | σ) while    |               |                                                  |
|     |         |         | top math    |               |                                                  |
|     |         |         | cites       |               |                                                  |
|     |         |         | Min-Max.    |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C08,    | Label/typo  | Source        | Fix strings; use ``tz='UTC'`` in ``date_range``; |
| R-1 |         | C12,    | defects:    |               | retitle panel “LEE-FILTERED VV”                  |
| 0** |         | C20,    | ``'TIMESTA  |               |                                                  |
|     |         | C22     | MPS (UTC'`` |               |                                                  |
|     |         |         | (missing    |               |                                                  |
|     |         |         | ``)``),     |               |                                                  |
|     |         |         | legend      |               |                                                  |
|     |         |         | ``'…        |               |                                                  |
|     |         |         |  (Granular  |               |                                                  |
|     |         |         | Speckle'``, |               |                                                  |
|     |         |         | `           |               |                                                  |
|     |         |         | `'TIMESTAMM |               |                                                  |
|     |         |         | P (UTC)'``, |               |                                                  |
|     |         |         | ``'Scaled N |               |                                                  |
|     |         |         | DVI (Min-Ma |               |                                                  |
|     |         |         | x [0, 1'``, |               |                                                  |
|     |         |         | ``'TRain    |               |                                                  |
|     |         |         |  Scaled'``; |               |                                                  |
|     |         |         | axes        |               |                                                  |
|     |         |         | labeled     |               |                                                  |
|     |         |         | “UTC” but   |               |                                                  |
|     |         |         | timestamps  |               |                                                  |
|     |         |         | are         |               |                                                  |
|     |         |         | tz-naive;   |               |                                                  |
|     |         |         | Plot 3 left |               |                                                  |
|     |         |         | panel       |               |                                                  |
|     |         |         | titled “RAW |               |                                                  |
|     |         |         | SAR VV” but |               |                                                  |
|     |         |         | plots       |               |                                                  |
|     |         |         | L           |               |                                                  |
|     |         |         | ee-filtered |               |                                                  |
|     |         |         | ``s         |               |                                                  |
|     |         |         | 1_vv_lee``. |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Medium  | C10,    | Lee filter  | Source        | Convert dB→linear, filter, convert back; derive  |
| R-1 |         | C18     | simpl       |               | σn² from ENL; apply to VH or justify; or rename  |
| 1** |         |         | ifications: |               | to “temporal adaptive smoothing”                 |
|     |         |         | 1-D         |               |                                                  |
|     |         |         | temporal,   |               |                                                  |
|     |         |         | dB domain   |               |                                                  |
|     |         |         | (Lee theory |               |                                                  |
|     |         |         | assumes     |               |                                                  |
|     |         |         | linear      |               |                                                  |
|     |         |         | in          |               |                                                  |
|     |         |         | tensity/mul |               |                                                  |
|     |         |         | tiplicative |               |                                                  |
|     |         |         | noise),     |               |                                                  |
|     |         |         | global σn²  |               |                                                  |
|     |         |         | without     |               |                                                  |
|     |         |         | ENL, VH not |               |                                                  |
|     |         |         | filtered,   |               |                                                  |
|     |         |         | default     |               |                                                  |
|     |         |         | reflect     |               |                                                  |
|     |         |         | boundary.   |               |                                                  |
|     |         |         | Title text  |               |                                                  |
|     |         |         | says        |               |                                                  |
|     |         |         | “adaptive   |               |                                                  |
|     |         |         | Lee filter  |               |                                                  |
|     |         |         | preserving  |               |                                                  |
|     |         |         | structural  |               |                                                  |
|     |         |         | h           |               |                                                  |
|     |         |         | ydrological |               |                                                  |
|     |         |         | b           |               |                                                  |
|     |         |         | oundaries”. |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C04,    | Hard-coded  | Source        | Use a ``BASE_DIR`` config; derive/standardize    |
| R-1 |         | C26     | Kaggle      |               | notebook name                                    |
| 2** |         |         | paths;      |               |                                                  |
|     |         |         | manifest    |               |                                                  |
|     |         |         | field       |               |                                                  |
|     |         |         | `           |               |                                                  |
|     |         |         | `notebook`` |               |                                                  |
|     |         |         | =           |               |                                                  |
|     |         |         | ``02        |               |                                                  |
|     |         |         | _preprocess |               |                                                  |
|     |         |         | ing.ipynb`` |               |                                                  |
|     |         |         | while the   |               |                                                  |
|     |         |         | file is     |               |                                                  |
|     |         |         | ``02-       |               |                                                  |
|     |         |         | preprocessi |               |                                                  |
|     |         |         | ng.ipynb``. |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C26     | No readback | Source        | Add VP-07 checks                                 |
| R-1 |         |         | / existence |               |                                                  |
| 3** |         |         | v           |               |                                                  |
|     |         |         | erification |               |                                                  |
|     |         |         | of exported |               |                                                  |
|     |         |         | files.      |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | C04     | Timestamps  | AN            | Use actual acquisition datetimes per sensor and  |
| R-1 |         |         | are evenly  |               | an explicit temporal alignment step              |
| 4** |         |         | spaced at ≈ |               |                                                  |
|     |         |         | 26 h 07     |               |                                                  |
|     |         |         | min, not    |               |                                                  |
|     |         |         | actual      |               |                                                  |
|     |         |         | Sentinel    |               |                                                  |
|     |         |         | acquisition |               |                                                  |
|     |         |         | times       |               |                                                  |
|     |         |         | (S1/S2      |               |                                                  |
|     |         |         | revisits    |               |                                                  |
|     |         |         | are         |               |                                                  |
|     |         |         | irregular   |               |                                                  |
|     |         |         | and         |               |                                                  |
|     |         |         | sensor      |               |                                                  |
|     |         |         | -specific). |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+
| **P | Low     | all     | No pinned   | Metadata      | Record ``pip freeze`` / environment lock in the  |
| R-1 |         |         | library     |               | notebook header                                  |
| 5** |         |         | versions,   |               |                                                  |
|     |         |         | no          |               |                                                  |
|     |         |         | commit/tag, |               |                                                  |
|     |         |         | no          |               |                                                  |
|     |         |         | ``req       |               |                                                  |
|     |         |         | uirements`` |               |                                                  |
|     |         |         | listing.    |               |                                                  |
+-----+---------+---------+-------------+---------------+--------------------------------------------------+

13. Figure Specifications
-------------------------

All figures: Matplotlib, dark theme, Aerospace palette, rendered inline.

13.1 Figure 1 — Optical QC (C08) — LLR-14
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------+--------------------------------------------+
| Property                                                      | Value                                      |
+===============================================================+============================================+
| Size                                                          | 14 × 5 in                                  |
+---------------------------------------------------------------+--------------------------------------------+
| Series                                                        | Raw NDVI (``#556677``, dotted, ``x``       |
|                                                               | markers, α 0.7); QC-passed NDVI            |
|                                                               | (``#00FF66``, circles, lw 2.0)             |
+---------------------------------------------------------------+--------------------------------------------+
| Overlay                                                       | Dashed vertical lines (``#FF3355``, α 0.3) |
|                                                               | at each masked timestamp (16)              |
+---------------------------------------------------------------+--------------------------------------------+
| Title                                                         | ``AETHER PREPROCESSING                     |
|                                                               | // SENTINEL-2 CLOUD QC & OPTICAL MASKING`` |
+---------------------------------------------------------------+--------------------------------------------+
| Diagnostics box (axes coords 0.02, 0.15)                      | threshold text; “Retained Clean Frames:    |
|                                                               | 19/35 (54.3%)”; the sentence “Zero Cloud   |
|                                                               | Noise Leakage Guaranteed into Downstream   |
|                                                               | Array”                                     |
+---------------------------------------------------------------+--------------------------------------------+
| Defects                                                       | Label typos (PR-10)                        |
+---------------------------------------------------------------+--------------------------------------------+

13.2 Figure 2 — SAR Despeckling (C12) — LLR-17
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------+--------------------------------------------+
| Property                                                      | Value                                      |
+===============================================================+============================================+
| Size                                                          | 14 × 5 in                                  |
+---------------------------------------------------------------+--------------------------------------------+
| Series                                                        | Raw VV (``#FF3355``, dashed, squares, α    |
|                                                               | 0.6); Lee VV (``#00FFCC``, circles, lw     |
|                                                               | 2.0)                                       |
+---------------------------------------------------------------+--------------------------------------------+
| Diagnostics                                                   | raw variance 9.064 dB²; filtered 5.701     |
|                                                               | dB²; “Speckle Noise Suppression: 37.1 %    |
|                                                               | Variance Smoothness” (computed)            |
+---------------------------------------------------------------+--------------------------------------------+
| Defects                                                       | Typos (PR-10); the quantity “variance      |
|                                                               | reduction” is called “speckle suppression” |
|                                                               | although part of the reduction is genuine  |
|                                                               | signal smoothing                           |
+---------------------------------------------------------------+--------------------------------------------+

13.3 Figure 3 — Raw vs Scaled Distributions (C20) — LLR-26
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------+--------------------------------------------+
| Property                                                      | Value                                      |
+===============================================================+============================================+
| Size                                                          | 15 × 5 in, two panels                      |
+---------------------------------------------------------------+--------------------------------------------+
| Left                                                          | Histograms of ``s1_vv_lee`` for train (12  |
|                                                               | bins, ``#FF3355``) and test (8 bins,       |
|                                                               | ``#FFCC00``); titled “RAW SAR VV”          |
|                                                               | (mislabel, PR-10)                          |
+---------------------------------------------------------------+--------------------------------------------+
| Right                                                         | Histograms of train/test Z-score;          |
|                                                               | diagnostics box at (0.03, 0.65): Train     |
|                                                               | Z-Mean (~0.0), Train Z-Std (~1.0), “Zero   |
|                                                               | Future Leakage Confirmed” (unsupported,    |
|                                                               | PR-03/07)                                  |
+---------------------------------------------------------------+--------------------------------------------+
| Suptitle                                                      | ``AETHER PREPROCESSING //                  |
|                                                               |  ZERO-LEAKAGE FEATURE SCALING COMPARISON`` |
|                                                               | (y = 1.02)                                 |
+---------------------------------------------------------------+--------------------------------------------+

13.4 Figure 4 — Scaled Multi-Sensor Series (C22) — LLR-27
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+---------------------------------------------------------------+--------------------------------------------+
| Property                                                      | Value                                      |
+===============================================================+============================================+
| Size                                                          | 14 × 5 in                                  |
+---------------------------------------------------------------+--------------------------------------------+
| Series                                                        | Z-score VV (``#00FFCC``, circles); NDVI    |
|                                                               | Min-Max (``#00FF66``, triangles); NaN gaps |
|                                                               | appear as breaks                           |
+---------------------------------------------------------------+--------------------------------------------+
| Boundary                                                      | Red dashed vertical line at 2026-08-31     |
|                                                               | (first test timestamp)                     |
+---------------------------------------------------------------+--------------------------------------------+
| Diagnostics                                                   | split date; “Cloud NaNs Handled”           |
|                                                               | (inaccurate, PR-05); “Aligned to Common    |
|                                                               | Spatial Grid” (unsupported, PR-09)         |
+---------------------------------------------------------------+--------------------------------------------+

14. Execution and Reproduction Procedure
----------------------------------------

1. Open ``02-preprocessing.ipynb`` in a Kaggle (or compatible) Python 3.12 environment, NumPy ≥ 2, pandas,
   SciPy, Matplotlib installed.
2. Ensure ``/kaggle/working`` is writable (or change the paths; PR-12).
3. Restart the kernel and **Run All**; cells must run in order C02 → C26.
4. Verify console output against Section 9.2 (expected numbers: 35 records; 19/16 QC; variances 9.0643 →
   5.7011; split 28/7; mean −13.51, std 2.20).
5. Confirm both artifacts exist under ``/kaggle/working/data_processed/`` and that the CSV has 16 columns × 35
   rows (IF-02).
6. Archive: notebook file, both artifacts, environment lock (PR-15).

15. Open Actions for Owner (Prioritized)
----------------------------------------

+-----------------------------------------+--------------------------------+--------------------------------+
| Priority                                | Action                         | Closes                         |
+=========================================+================================+================================+
| 1                                       | Move Lee filtering after the   | PR-03, PR-07, HLR-09           |
|                                         | split, or make it causal and   |                                |
|                                         | train-only; add a perturbation |                                |
|                                         | leakage test                   |                                |
+-----------------------------------------+--------------------------------+--------------------------------+
| 2                                       | State clearly that data is     | PR-01, PR-14                   |
|                                         | synthetic or connect real      |                                |
|                                         | Notebook 01 output             |                                |
+-----------------------------------------+--------------------------------+--------------------------------+
| 3                                       | Align notebook claims with the | PR-02, PR-05, PR-09            |
|                                         | implementation (SCL, spatial   |                                |
|                                         | grid, interpolation,           |                                |
|                                         | coordinates, precipitation,    |                                |
|                                         | “100 % verified”)              |                                |
+-----------------------------------------+--------------------------------+--------------------------------+
| 4                                       | Extend integrity audit to all  | PR-05, HLR-10                  |
|                                         | exported model features        |                                |
|                                         | including ``ndvi_minmax``      |                                |
+-----------------------------------------+--------------------------------+--------------------------------+
| 5                                       | Pin environment and            | PR-12, PR-15                   |
|                                         | parametrize paths              |                                |
+-----------------------------------------+--------------------------------+--------------------------------+
| 6                                       | Clean-up pass for typos,       | PR-04, PR-06, PR-08, PR-10,    |
|                                         | unused code, redundant columns | PR-13                          |
+-----------------------------------------+--------------------------------+--------------------------------+

Appendix A — Mapping to DO-178C Life-Cycle Data Items
-----------------------------------------------------

+----------------------------------------------+-------------------------------------------------+----------+
| DO-178C data item (Section 11)               | Where addressed in this document                | Remark   |
+==============================================+=================================================+==========+
| PSAC / SDP / SVP / SCMP / SQAP               | Sections 0.2, 5.4, 6, 9.1 (condensed)           | Planning |
|                                              |                                                 | data not |
|                                              |                                                 | produced |
|                                              |                                                 | as       |
|                                              |                                                 | separate |
|                                              |                                                 | d        |
|                                              |                                                 | ocuments |
+----------------------------------------------+-------------------------------------------------+----------+
| Software Requirements Data (11.9)            | Section 7                                       | HLR,     |
|                                              |                                                 | LLR, DR, |
|                                              |                                                 | NFR,     |
|                                              |                                                 | in       |
|                                              |                                                 | terfaces |
+----------------------------------------------+-------------------------------------------------+----------+
| Design Description (11.10)                   | Section 8                                       | Archi    |
|                                              |                                                 | tecture, |
|                                              |                                                 | alg      |
|                                              |                                                 | orithms, |
|                                              |                                                 | pa       |
|                                              |                                                 | rameters |
+----------------------------------------------+-------------------------------------------------+----------+
| Source Code (11.11)                          | Notebook cells C02–C26                          | R        |
|                                              |                                                 | eference |
|                                              |                                                 | [R2]     |
+----------------------------------------------+-------------------------------------------------+----------+
| Executable Object Code (11.12)               | not applicable                                  | int      |
|                                              |                                                 | erpreted |
+----------------------------------------------+-------------------------------------------------+----------+
| Verification Cases and Procedures (11.13)    | Sections 9.1, 9.2, 9.5, 14                      |          |
+----------------------------------------------+-------------------------------------------------+----------+
| Verification Results (11.14)                 | Section 9.2, 9.4                                |          |
+----------------------------------------------+-------------------------------------------------+----------+
| Life Cycle Environment Config. Index (11.15) | Sections 4.2, 6                                 | versions |
|                                              |                                                 | in       |
|                                              |                                                 | complete |
+----------------------------------------------+-------------------------------------------------+----------+
| Software Configuration Index (11.16)         | Section 4                                       | no       |
|                                              |                                                 | version  |
|                                              |                                                 | control  |
+----------------------------------------------+-------------------------------------------------+----------+
| Problem Reports (11.17)                      | Section 12                                      | 15       |
|                                              |                                                 | reports  |
+----------------------------------------------+-------------------------------------------------+----------+
| Trace Data (11.21)                           | Section 10                                      | bidir    |
|                                              |                                                 | ectional |
+----------------------------------------------+-------------------------------------------------+----------+
| Software Accomplishment Summary (11.20)      | Section 11                                      | informal |
+----------------------------------------------+-------------------------------------------------+----------+

Appendix B — Notebook Claims vs. Verified Evidence (C27 Executive Summary)
--------------------------------------------------------------------------

+------------------------------------------+-------------------+--------------------------------------------+
| Claim in notebook                        | Verdict           | Evidence / comment                         |
+==========================================+===================+============================================+
| “Sentinel-2 SCL Cloud Quality Control    | Partially true    | Threshold on cloud %, not SCL (PR-02)      |
| filtering out observations with > 50 %   |                   |                                            |
| cloud mask”                              |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Isolated corrupted optical spectral     | True              | 16 NDVI values masked                      |
| index frames”                            |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Applied adaptive 1D Lee Filtering on    | True              | C10                                        |
| backscatter σ⁰VV”                        |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “preserving hydrological ground          | Unsupported       | No spatial data or boundary metric         |
| boundaries”                              |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Enforced strict 80/20 temporal split”   | True              | 28 / 7, chronological                      |
+------------------------------------------+-------------------+--------------------------------------------+
| “Fitted Z-Score and Min-Max scalers      | True              | C18                                        |
| exclusively on training frames”          |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “preventing future data contamination    | **Not fully       | Lee stage leaks across split (PR-03)       |
| into downstream models”                  | true**            |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Embedded real-time mathematical         | True              | 4 figures                                  |
| diagnostic annotations”                  |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Persisted preprocessed_telemetry.csv    | True              | C26 (printed; not read back)               |
| and scaler_manifest.json”                |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Target domain: Bhadrak/Balasore Spatial | Unsupported       | No coordinates or spatial grid in code     |
| Grid (21.1378° N, 86.6874° E)”           |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “100 % verified, scientifically audited” | Overstated        | Three assertions; two High/Medium findings |
|                                          |                   | (Section 12)                               |
+------------------------------------------+-------------------+--------------------------------------------+
| “SAR-Optical channels aligned to common  | Unsupported       | Single-point time series                   |
| spatial grid”                            |                   |                                            |
+------------------------------------------+-------------------+--------------------------------------------+
| “Zero Cloud Noise Leakage Guaranteed”    | Conditionally     | NDVI is masked; but the cloud-percentage   |
|                                          | true              | column itself remains in the export        |
+------------------------------------------+-------------------+--------------------------------------------+

Appendix C — Intellectual Property and Copyright Notice (carried from C28)
--------------------------------------------------------------------------

**PROJECT — THE MRIDANSH · CENTRAL ENGINE — AETHER-MRID1607X** *Multi-Domain Soil Intelligence & Geotechnical
Stability Engine*

============================= ========================================================================
**Copyright**                 © 2026 Gourgopal Mohapatra. All Rights Reserved.
**Developed & Maintained by** Gourgopal Mohapatra
**Lead Organization**         JCC HEADQUARTER
**Facility**                  JCC CAMPUS 2 — RS-SDA Division (Remote Sensing & Spatial Data Analytics)
============================= ========================================================================

This codebase, together with its neural architecture specifications (PINN / GCN), numerical formulations and
associated telemetry pipelines, constitutes proprietary intellectual property. Unauthorized copying,
redistribution, reverse engineering or commercial execution of this software package, in whole or in part, via
any medium, is strictly prohibited without prior written authorization from the lead researcher and JCC
RS-SDA.

*This documentation inherits the same classification and notice.*

*End of Document AETHER-MRID1607X-NB02-DOC-001, Version 1.0*
