# TCGA-BRCA Differential Gene Expression Pipeline
Designed for reproducibility across TCGA projects and GEO datasets beyond BRCA
A modular, scalable MapReduce pipeline for stratified differential gene expression analysis across age groups, built on TCGA-BRCA clinical and RNA-seq data from the GDC Data Portal.



## Scientific Motivation

Age is a major modifier of breast cancer biology, yet most transcriptomic studies treat patient cohorts as age-homogeneous. This pipeline was designed to ask a specific and reproducible question:

> **For a given primary diagnosis, which genes are differentially expressed between age groups for each sex?**

The system operationalizes age stratification as a first-class analysis variable rather than a covariate, enabling systematic discovery of age-associated transcriptomic signatures within diagnosis-defined subcohorts.



## Data Sources

| Data Type | Source | Format | Notes |
|---|---|---|---|
| Clinical metadata | GDC Data Portal (TCGA-BRCA) | TSV | `cases.case_id`, `demographic.age_at_index`, `diagnoses.primary_diagnosis` |
| Gene expression | GDC STAR Counts (per-sample) | TSV | `tpm_unstranded` across 60,666 features per sample |

Expression files are individual per-sample GDC downloads. Rows where `gene_id` begins with `N_` (ambiguous, intergenic, or unmapped read categories) are filtered at ingestion. The first comment line (`#`) is handled via `comment='#'` in `pd.read_csv`.



## Pipeline Architecture

The pipeline is organized into nine conceptual layers, each with a defined input contract, transformation logic, and output contract. This separation of concerns allows any layer to be swapped for a dataset with different structure, as long as the user updates the configuration.

```
clinical.tsv                          GDC expression TSVs (per sample)
     │                                          │
     ▼                                          ▼
┌─────────────┐                     ┌───────────────────┐
│  PART 1     │                     │  PART 2           │
│  Cohort     │                     │  Expression       │
│  Definition │                     │  Assembly         │
└──────┬──────┘                     └────────┬──────────┘
       │                                     │
       └──────────────────┬──────────────────┘
                          ▼
               ┌─────────────────────┐
               │  PART 3             │
               │  Integration Layer  │
               │  (ID intersection)  │
               └──────────┬──────────┘
                          ▼
               ┌─────────────────────┐
               │  PART 4             │
               │  Differential       │
               │  Expression Logic   │
               └──────────┬──────────┘
                          ▼
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
      PART 5          PART 6          PART 7
   Generalization    MapReduce       Reporting
      Layer         Efficiency        (JSON)
                                        │
                                        ▼
                                    PART 8
                                  Visualization
                                        │
                                        ▼
                                    PART 9
                              Full Pipeline Integration
```



## Part 1 — Cohort Definition Layer ✅ Complete

**Input:** `clinical.tsv` (GDC manifest format)  
**Output:** `cleaner_clinical.tsv` — 1,062 unique patients, 55 diagnosis × age group combinations

### Processing Steps

- Column subsetting and renaming via config-driven field mapping
- Age converted to numeric; non-parseable values dropped
- `, NOS` suffix removed from primary diagnosis strings (e.g., `Infiltrating duct carcinoma, NOS` → `Infiltrating duct carcinoma`) to unify diagnosis groups
- Deduplication on `Case ID` prior to binning
- Age group assignment using `pd.cut` with closed-left bins: `0–20`, `21–40`, `41–60`, `61–80`, `81–100`
- Exclusion of sentinel strings: `not reported`, `diagnosis`, `'--`

### Files

| File | Role |
|---|---|
| `config.py` | Frozen dataclass (`Config`) holding all field names, bin edges, bin labels, chunk size, and separator — immutable after instantiation via `@dataclass(frozen=True)` |
| `cleaner.py` | One-time cleaning script; produces `cleaner_clinical.tsv` |
| `chunker.py` | Generator that yields fixed-size chunks from any TSV using `pd.read_csv(chunksize=...)` |
| `mapper.py` | Per-chunk transformation: column selection, age coercion, NOS stripping, age group assignment |
| `reducer.py` | Concatenates mapped chunks, deduplicates on `Case ID`, groups by `Diagnosis × AGE_GROUP`, emits counts |
| `pipeline.py` | Composes all components using a `Pipe` class with `__or__` operator overloading |

---

## Part 2 — Expression Assembly Layer 🔧 In Progress

**Input:** 1,000+ per-sample STAR Counts TSVs; `files_2026-02-25.json` (GDC file-to-case mapping)  
**Output:** `combined_expression.tsv` — long-format table with columns `Case ID`, `gene_id`, `gene_name`, `gene_type`, `tpm_unstranded`

### Design Constraint

Each per-sample file contains ~60,000 rows. Accumulating all samples in memory simultaneously would exceed available RAM on constrained hardware. The assembler therefore writes each patient's data to disk immediately using `mode='a'` (append) with `header=True` on first write only, avoiding any in-memory accumulation pattern.

---

## Part 3 — Integration Layer

Intersects `Case ID` values between the cohort table (Part 1) and the expression matrix (Part 2). Samples present in one source but absent in the other are dropped. Output is a matched pair: a filtered count matrix and a filtered design table with identical sample ordering.

---

## Part 4 — Differential Expression Logic Layer

For each primary diagnosis, and separately for each sex:

1. Subset samples to that sex
2. Partition into age group A vs. age group B
3. Compute per-group mean TPM for each gene 
4. Compute log₂ fold change: `log₂(mean_B / mean_A)`
5. Rank genes by absolute log₂FC and DeSeq2 integration

This layer does not apply a statistical model in its current form. It is designed as a ranked-list generator that can be extended with DESeq2-style negative binomial modeling or limma-voom if count-level data replaces TPM as the expression unit.

---

## Part 5 — Generalization Layer

The system is schema-agnostic. No column name is hardcoded in any processing script. All field names, file paths, bin definitions, and filter criteria are specified in a frozen configuration object. To apply this pipeline to a non-BRCA TCGA project, a GEO dataset, or a custom clinical cohort, the user edits the config and supplies the appropriate input files — no logic changes are required.

---

## Part 6 — MapReduce Efficiency Layer

The map phase processes one gene or one chunk at a time and emits partial group summaries (partial sums and counts). The reduce phase aggregates partial summaries to compute final group means and fold changes. This design is O(n) in memory with respect to number of samples and is theoretically scalable to datasets with tens of thousands of samples without architectural changes.

---

## Part 7 — Reporting Layer

Ranked gene lists are serialized to structured JSON, organized by:

```
diagnosis → sex → age_group_comparison → ranked gene list
```

Each entry includes `gene_id`, `gene_name`, `mean_group_A`, `mean_group_B`, `log2FC`.

---

## Part 8 — Visualization Layer *(planned)*

Planned outputs: volcano plots (log₂FC vs. magnitude), heatmaps of top-ranked genes per group, age-group expression distribution plots. Target libraries: `matplotlib`, `seaborn`.

---

## Part 9 — Full Pipeline Integration *(planned)*

A single entry point (`pipeline_full.py`) that chains all layers using the `Pipe` operator pattern, so the entire analysis from raw GDC downloads to ranked gene report runs with one command.

---

## Technical Stack

| Concern | Implementation |
|---|---|
| Language | Python 3 |
| Data manipulation | `pandas` |
| Configuration | `dataclasses.dataclass(frozen=True)` with `typing.Final` and `typing.Tuple` |
| File I/O | `pathlib.Path`, `pd.read_csv`, `pd.to_csv` |
| Memory management | Generator-based chunking; write-to-disk immediately pattern |
| Pipeline composition | Custom `Pipe` class using `__or__` operator overloading |
| Logging | `logging` module throughout |
| Verification | `assert` statements at reducer output and pipeline boundaries |
| Error handling | Structured `try/except/raise` with typed exceptions |

---

## Repository Structure

```
Project 1/
├── config.py                  # Immutable pipeline configuration
├── cleaner.py                 # One-time clinical data cleaning
├── cleaner_clinical.tsv       # Cleaned cohort (1,062 patients)
├── chunker.py                 # Chunked TSV reader (generator)
├── mapper.py                  # Per-chunk transformation logic
├── reducer.py                 # Aggregation and verification
├── pipeline.py                # Part 1 pipeline entry point
│
└── Project 1b/
    ├── expression_config.py   # Expression-specific config
    ├── expression_chunker.py  # Per-sample file reader
    ├── expression_mapper.py   # Per-sample transformation
    ├── combiner_exp.py        # Expression assembly (write-to-disk)
    └── pipeline2.py           # Part 2 pipeline entry point
```

---

## Current Status

| Part | Status | Notes |
|---|---|---|
| 1 — Cohort Definition | ✅ Complete | 1,062 patients, 55 diagnosis × age group combinations |
| 2 — Expression Assembly | 🔧 In progress | Rewriting to eliminate memory accumulation |
| 3 — Integration | ⬜ Pending | Awaiting Part 2 output |
| 4 — DE Logic | ⬜ Pending | Design finalized |
| 5 — Generalization | ⬜ Pending | Architecture defined |
| 6 — MapReduce | ⬜ Pending | Architecture defined |
| 7 — Reporting | ⬜ Pending | |
| 8 — Visualization | ⬜ Pending | |
| 9 — Full Integration | ⬜ Pending | |

---

## Author

**Aumunique**  
Self-directed project — TCGA-BRCA transcriptomic analysis  
Built from scratch as part of a self-directed bioinformatics curriculum.

---

## Data Availability

Expression data and clinical metadata were obtained from the NCI Genomic Data Commons (GDC) Data Portal under TCGA-BRCA project accession. Raw data are subject to GDC data access policies.
