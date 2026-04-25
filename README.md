<div align="center">

<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Streamlit-1.54-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
<img src="https://img.shields.io/badge/LLM-Llama3%20via%20Ollama-7C3AED?style=for-the-badge" />
<img src="https://img.shields.io/badge/Status-Prototype-F59E0B?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge" />

# 🛡️ SAR-AI: Multi-Agent Suspicious Activity Report Generation System

**An AI-powered compliance automation system that detects suspicious financial transactions and generates regulatory Suspicious Activity Reports (SARs) using a multi-agent LLM architecture.**

*Built for the Barclays Hackathon · Designed for AML / Financial Crime Compliance*

[Features](#-features) · [Architecture](#-system-architecture) · [Quickstart](#-quickstart) · [Pipeline](#-multi-agent-pipeline) · [Dashboard](#-dashboard) · [Limitations](#-known-limitations--production-considerations) · [Roadmap](#-roadmap)

</div>

---

## 📌 Overview

Financial institutions process hundreds of millions of transactions daily. Detecting suspicious activity and generating the required regulatory reports (SARs) is a time-consuming, largely manual process — costly in both time and compliance risk.

**SAR-AI** automates this end-to-end workflow by combining:

- **Statistical anomaly detection** — identifies transactions that deviate significantly from expected patterns
- **Multi-factor risk scoring** — evaluates statistical, historical, and peer-group signals
- **Typology classification** — categorises suspicious patterns based on AML frameworks
- **Multi-agent LLM pipeline** — a Writer agent drafts the SAR narrative; an Auditor agent verifies it
- **Interactive compliance dashboard** — built on Streamlit for human-in-the-loop review
- **Tamper-evident audit logging** — every decision is logged to a structured audit trail

> ⚠️ **Disclaimer:** This is a research prototype built for a hackathon. It is not intended for production deployment in regulated environments without significant additional hardening, validation, and compliance review. See [Known Limitations](#-known-limitations--production-considerations).

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Anomaly Detection | Z-score based statistical flagging with configurable sensitivity |
| 📊 Risk Scoring Engine | Three-factor scoring: statistical anomaly + historical spike + peer comparison |
| 🏷️ Typology Classification | Categorises patterns as Structuring, High-Value Anomaly, or Threshold Breach |
| 🤖 Agent 1 — SAR Writer | Llama3-powered generation of formal, compliance-ready SAR narratives |
| 🕵️ Agent 2 — Auditor | Adversarial cross-check of narrative against raw transaction data |
| 📋 Schema-Agnostic Ingestion | Auto-detects column names across different CSV schemas |
| 📁 Audit Trail Logging | Append-only JSONL log of all flagged transactions and decisions |
| 🖥️ Streamlit Dashboard | Interactive UI for upload, investigation, review, download, and logging |
| 📥 SAR Download | Export compliance narratives as `.txt` files per transaction |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Transaction Dataset (CSV)                 │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Schema Detection & Data Cleaning                │
│         schema.py → identify_columns()                      │
│         utils.py  → safe_numeric_conversion()               │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Anomaly Detection                          │
│         detection.py → detect_suspicious_transactions()     │
│         Z = (amount − μ) / σ  →  flag if Z > threshold     │
└─────────────────────────┬───────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        Risk Scorer   Typology    Evidence
        scorer.py    typology.py  evidence.py
              └───────────┼───────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent 1: SAR Narrative Generator               │
│         narrative.py → build_prompt()                       │
│         llm_service.py → generate_sar()  [Llama3]          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent 2: Adversarial Auditor                   │
│         llm_service.py → run_adversarial_audit()           │
│         Output: VERIFIED ✓ or DISCREPANCY ✗                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Audit Trail Logging                            │
│         audit.py → log_audit()  →  audit_trail.jsonl       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Compliance Dashboard                  │
│         ui/dashboard.py  →  localhost:8501                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent Pipeline

### 🔍 Detection Agent — `detection.py`

Detects anomalies using Z-score deviation analysis across the transaction dataset.

```
Z = (transaction_amount − population_mean) / population_std
```

Transactions exceeding the configured Z-score threshold (default: 2.0) are flagged as suspicious and passed to the downstream pipeline.

> **Edge case handling:** If `std == 0` (all transactions identical), the function safely returns an empty list rather than crashing.

---

### 📈 Risk Scoring Agent — `scorer.py`

Computes a composite risk confidence score from three independent signals:

| Signal | Method | Max Contribution |
|---|---|---|
| Statistical Anomaly | Z-score magnitude × 10 | 40 pts |
| Historical Spike | Current amount vs. user's own average | 30 pts |
| Peer Comparison | Current amount vs. global population average | 20 pts |
| Base Floor | Applied to all flagged transactions | 10 pts |

**Final score is capped at 99.92** to avoid implying absolute certainty.

> ⚠️ **Known limitation:** A floor of `78.45` is applied to all scores below 75 for demonstration purposes. This must be removed in any production deployment.

---

### 🏷️ Typology Agent — `typology.py`

Classifies suspicious transactions against AML pattern categories based on deviation severity.

| Z-Score Deviation | Typology Classification |
|---|---|
| > 5.0 | High-Value Anomaly / Potential Wealth Transfer |
| > 3.0 | Significant Outlier / Possible Structuring |
| ≤ 3.0 | Standard Threshold Breach |

---

### ✍️ Agent 1: SAR Narrative Writer — `llm_service.py` + `narrative.py`

Uses **Llama3 via Ollama** (local inference) to generate a formal, professional SAR narrative from the structured evidence package. Running the model locally ensures that sensitive financial data never leaves the organisation's infrastructure — a critical requirement under GDPR and financial data protection regulations.

**Example output:**

> *"The transaction TXN48321, valued at £142,500.00, exhibits a Z-score deviation of 4.87, significantly exceeding the account holder's historical average. This pattern is consistent with anomalous wealth transfer behaviour and warrants immediate further investigation by the compliance team."*

---

### 🕵️ Agent 2: Adversarial Auditor — `llm_service.py`

A second independent LLM agent cross-references the generated SAR narrative against raw transaction data to detect factual inconsistencies or hallucinations.

**Output format:**

```
VERIFIED: Narrative accurately reflects the transaction data provided.
```
```
DISCREPANCY: Narrative states amount as £12,000 but data shows £142,500.
```

> ⚠️ **Important:** The auditor is also an LLM and can itself produce incorrect verifications. In production, deterministic code-based checks (exact string matching of IDs and amounts) should supplement or replace the LLM auditor.

---

## 🖥️ Dashboard

The Streamlit dashboard provides an end-to-end interactive compliance investigation interface.

**Workflow:**

1. **Upload** — Drag and drop any transaction CSV file
2. **Detect** — Adjust the Z-score sensitivity slider; suspicious transactions are highlighted instantly
3. **Visualise** — Scatter plot of all transactions with anomalies flagged in red
4. **Investigate** — Select any flagged transaction ID from the dropdown
5. **Execute Pipeline** — Launch the full multi-agent analysis with one click
6. **Review** — Inspect the reasoning chain, audit status, and AI-drafted SAR narrative
7. **Approve & Log** — Confirm and log to the audit trail, or download as `.txt`

---

## 📁 Project Structure

```
sar-ai-project/
│
├── app/                          # Core pipeline modules
│   ├── audit.py                  # Audit trail logging
│   ├── detection.py              # Z-score anomaly detection
│   ├── evidence.py               # Evidence package assembly
│   ├── llm_service.py            # Ollama/Llama3 LLM interface
│   ├── narrative.py              # SAR prompt construction
│   ├── schema.py                 # Schema-agnostic column detection
│   ├── scorer.py                 # Multi-factor risk scoring
│   ├── typology.py               # AML typology classification
│   ├── utils.py                  # Data cleaning utilities
│   └── main.py                   # CLI entry point
│
├── ui/                           # Dashboard
│   ├── dashboard.py              # Streamlit dashboard
│   └── assets/
│       └── security_icon.png
│
├── data/
│   └── sample_transactions.csv   # Sample dataset (not included in repo)
│
├── audit_trail.jsonl             # Auto-generated audit log (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚡ Quickstart

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/sar-ai-project.git
cd sar-ai-project
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and start Ollama + Llama3

Download Ollama from [https://ollama.com](https://ollama.com), then:

```bash
ollama pull llama3
ollama serve        # Start the local inference server
```

Verify it's working:

```bash
ollama run llama3
```

---

## 🚀 Running the Project

### Option A — CLI Pipeline

```bash
python main.py
```

This will load the dataset, run anomaly detection, generate SAR narratives for all flagged transactions, and update the audit log.

### Option B — Streamlit Dashboard (Recommended)

```bash
streamlit run ui/dashboard.py
```

Then open your browser at:

```
http://localhost:8501
```

Upload any compatible transaction CSV to begin analysis.

---

## 📄 Sample Input Format

The system auto-detects column schemas, but a typical input CSV looks like:

```csv
transaction_id,customer_id,amount,date,country
TXN001,CUST_44,2500.00,2024-03-01,UK
TXN002,CUST_12,142500.00,2024-03-01,UK
TXN003,CUST_81,3100.00,2024-03-02,UK
```

Required: a column containing `amount` or `value` in the name.  
Optional but recommended: `transaction_id`, `customer_id` / `customer_name` / `account_number`.

---

## 📋 Audit Log Format

All pipeline decisions are appended to `audit_trail.jsonl`. Each entry contains:

```json
{
  "timestamp": "2026-03-10T12:30:21.441872",
  "transaction_id": "TXN48321",
  "risk_level": 89.2,
  "typology": "Significant Outlier / Possible Structuring",
  "summary": "The transaction significantly exceeds historical averages for the account holder..."
}
```

---

## ⚠️ Known Limitations & Production Considerations

This prototype was built for a hackathon and has several known issues that must be addressed before any production deployment.

| Area | Current State | Production Requirement |
|---|---|---|
| **Risk floor** | Scores below 75 are hardcoded to 78.45 | Remove floor; use calibrated probabilistic scoring |
| **LLM auditor** | Auditor is an LLM and can hallucinate | Add deterministic code-based fact checks |
| **LLM interface** | `subprocess` call to Ollama | Use async REST API with retry/backoff/circuit breaker |
| **Audit storage** | Append-only JSONL flat file | PostgreSQL with tamper-evident write-once schema |
| **Anomaly detection** | Single-transaction Z-score only | Add temporal/sequence analysis to catch structuring |
| **Typology** | Based only on deviation score | Multi-signal typology using transaction networks |
| **Human review** | Optional in UI | Mandatory gated approval before any SAR filing |
| **Explainability** | Risk score partially opaque | Full SHAP/LIME explainability for regulatory defence |
| **Scale** | Batch CSV processing | Real-time streaming (Kafka / Kinesis) |
| **Model** | Generic Llama3 | Fine-tuned AML-specific model on labelled SAR corpus |

---

## 🗺️ Roadmap

- [ ] Replace Z-score with Isolation Forest / ECOD for non-Gaussian distributions
- [ ] Temporal sequence detection for structuring patterns
- [ ] Graph-based network analysis for connected entity fraud
- [ ] Deterministic hallucination checks in the auditor layer
- [ ] Fine-tuned open-source LLM on AML SAR corpora
- [ ] FastAPI backend + React frontend replacing Streamlit
- [ ] PostgreSQL audit trail with write-once compliance schema
- [ ] Real-time streaming ingestion via Kafka
- [ ] SHAP explainability layer for risk scores
- [ ] Integration with core banking API (ISO 20022)

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.10+ |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly |
| Dashboard | Streamlit |
| AI Model | Llama3 via Ollama (local inference) |
| Architecture | Multi-Agent AI (Writer + Auditor) |
| Logging | JSONL append-only audit trail |

---

## 🎯 Use Cases

- Anti-Money Laundering (AML) transaction monitoring
- Suspicious Activity Report (SAR) generation and review
- Financial compliance workflow automation
- AML analyst decision-support tooling
- RegTech / FinTech research and prototyping

---

## 🤝 Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## 👤 Author

**Akash Singh**  
Computer Science Student — SRM Institute of Science and Technology

Interests: Artificial Intelligence · Financial Technology · Backend Systems · Intelligent Automation

---

<div align="center">

If you found this project useful or interesting, consider giving it a ⭐

</div>
