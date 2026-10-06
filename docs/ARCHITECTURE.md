# SAR-AI Architecture

## Overview
SAR-AI is an end-to-end multi-agent pipeline designed to detect anomalous financial activity, gather evidence deterministically, and generate Suspicious Activity Reports (SARs) utilizing a combination of ML detection models and Large Language Models (LLMs).

## Core Philosophy
1. **Fact over Fiction:** LLMs are powerful but prone to hallucination. The architecture guarantees factual correctness by separating *evidence gathering* (deterministic Python logic) from *narrative generation* (LLM logic).
2. **Multi-Agent Orchestration:** Specialized agents handle distinct tasks: summarization, writing, and auditing, orchestrated by a Supervisor.
3. **Traceability:** Every action, evidence package, and generated report is logged deterministically into a SQLite database.

## System Components

### 1. Data Ingestion & Preprocessing (`data/`)
- **Ingestion:** Reads CSVs or HuggingFace datasets, automatically mapping schemas.
- **Preprocessing:** Handles numerical scaling, imputes missing values, and identifies required columns.

### 2. Feature Engineering (`features/`)
- Extracts advanced features like `is_burst_activity` and `historical_deviation` by comparing the transaction against customer baselines.

### 3. Detection (`detection/`)
- Utilizes statistical models (`ZScoreDetector`) and machine learning models (`IsolationForestDetector`) in a pipeline.
- Transactions flagged by these models are passed downstream for investigation.

### 4. Risk Scoring (`risk/`)
- Provides a transparent, composite 0-100 score based on anomaly signals, historical deviation, burst activity, and counterparty risks.

### 5. Typology Engine & Graph Analysis (`analysis/`)
- **Typologies:** Applies rules overlaid with ML signals to identify known money-laundering typologies (e.g., Structuring, Circular Transactions).
- **Network Analysis:** Builds a relationship graph to find cycles and complex entity relationships.

### 6. Evidence Engine (`evidence/`)
- The single source of truth. It compiles the transaction data, anomaly signals, and typologies into a strictly typed `EvidencePackage` Pydantic model. 

### 7. Multi-Agent System (`agents/`)
- **InvestigatorAgent:** Synthesizes the EvidencePackage into an investigative context.
- **SarWriterAgent:** Drafts the SAR narrative specifically constrained to the evidence provided.
- **AuditorAgent:** A two-pass auditor:
  - *Pass 1 (Deterministic):* Checks that exact amounts, dates, and IDs from the evidence are correctly stated in the narrative.
  - *Pass 2 (Semantic):* Uses an LLM to check for unsupported claims or hallucinations.
- **SupervisorAgent:** Orchestrates the flow. If the Auditor finds discrepancies, the Supervisor forces the Writer to revise until the report is clean.

### 8. Storage & Observability (`app/storage.py`)
- Provides a robust SQLite-backed repository.
- Tracks `investigations`, `sar_reports`, and `audit_logs` preserving the history, validation status, and generated outputs of every anomaly investigated.

### 9. Streamlit Dashboard (`ui/dashboard.py`)
- Provides a visual interface to upload data, view the multi-agent reasoning chain, and review/approve generated SARs.
