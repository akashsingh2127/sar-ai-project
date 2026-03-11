#  SAR-AI: Multi-Agent Suspicious Activity Report Generation System

An AI-powered system that detects suspicious financial transactions and automatically generates regulatory **Suspicious Activity Reports (SARs)** using a **multi-agent architecture and Large Language Models (LLMs)**.

This project simulates how financial institutions can automate compliance workflows such as **AML monitoring, fraud detection, and SAR generation**.

---

#  Overview

Financial institutions process millions of transactions daily. Detecting suspicious activity and generating regulatory reports is often time-consuming and manual.

**SAR-AI** automates this pipeline by combining:

- Statistical anomaly detection
- Multi-agent reasoning
- AI-generated SAR narratives
- Automated compliance auditing
- Audit trail logging
- Interactive dashboard for investigation

The system identifies suspicious transactions and produces **compliance-ready SAR narratives verified by an AI auditor agent**.

---

#  System Architecture

```
Transaction Dataset
        │
Schema Detection & Data Cleaning
        │
Anomaly Detection (Z-Score)
        │
Risk Scoring Engine
        │
Typology Classification
        │
Evidence Package Generation
        │
Agent 1: SAR Narrative Generator (LLM)
        │
Agent 2: Adversarial Auditor
        │
Audit Trail Logging
        │
Streamlit Compliance Dashboard
```

---

#  Multi-Agent Pipeline

### Detection Agent
Detects anomalies using **Z-score deviation analysis**.

```
Z = (transaction_amount - mean) / std
```

Transactions above the threshold are flagged as suspicious.

---

### Risk Scoring Agent

Calculates a risk score based on:

- Statistical anomaly
- Historical user behavior spike
- Peer group comparison

Final output is a **risk confidence score (0–100%)**.

---

###  Typology Agent

Classifies suspicious activity patterns.

| Deviation | Typology |
|--------|--------|
| >5 | High-Value Anomaly / Potential Wealth Transfer |
| >3 | Significant Outlier / Possible Structuring |
| <3 | Standard Threshold Breach |

---

### Narrative Agent (LLM)

Uses **Llama3 via Ollama** to generate a professional **Suspicious Activity Report narrative** based on the evidence package.

Example:

> The transaction significantly exceeds historical averages for the account holder and demonstrates characteristics consistent with anomalous financial behavior, warranting further investigation.

---

###  Adversarial Auditor Agent

This agent verifies the SAR narrative against raw transaction data to detect hallucinations or inconsistencies.

Output format:

```
VERIFIED: Narrative accurately reflects transaction data.
```

or

```
DISCREPANCY: Narrative contains incorrect transaction information.
```

---

#  Dashboard Features

The project includes a **Streamlit dashboard** for interactive investigation.

Features include:

- Upload transaction dataset
- Suspicious transaction detection
- Risk visualization
- Multi-agent reasoning display
- SAR narrative review
- Download SAR reports
- Compliance audit logging

---

# Project Structure

```
sar-ai-project
│
├── app
│   ├── audit.py
│   ├── detection.py
│   ├── evidence.py
│   ├── llm_service.py
│   ├── narrative.py
│   ├── schema.py
│   ├── scorer.py
│   ├── typology.py
│   └── main.py
│   └── utils.py
│
├── data
│   └── sample_transactions.csv
│
├── ui
│   ├── dashboard.py
│   └── assets
│       └── security_icon.png
│
├── .gitignore
├── audit_trail.jsonl
├── requirements.txt
└── README.md
```

---

#  Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/sar-ai-project.git
cd sar-ai-project
```

Create virtual environment:

```bash
python -m venv venv
```

Activate environment

**Windows**

```
venv\Scripts\activate
```

**Mac/Linux**

```
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

#  Install Ollama + Llama3

Install Ollama from:

https://ollama.com

Then download the model:

```bash
ollama pull llama3
```

Verify installation:

```bash
ollama run llama3
```

---

#  Running the Project

### Run CLI Pipeline

```bash
python main.py
```

This will:

- load the dataset
- detect suspicious transactions
- generate SAR narratives
- log the audit trail

---

### Run Streamlit Dashboard

```bash
streamlit run ui/dashboard.py
```

Open in browser:

```
http://localhost:8501
```

Upload a transaction dataset to start analysis.

---

#  Example Audit Log

The system logs decisions in:

```
audit_trail.jsonl
```

Example entry:

```json
{
 "timestamp": "2026-03-10T12:30:21",
 "transaction_id": "TXN48321",
 "risk_level": 89.2,
 "typology": "Significant Outlier / Possible Structuring",
 "summary": "The transaction significantly exceeds historical averages..."
}
```

---

# Technologies Used

| Category | Tools |
|--------|--------|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Visualization | Plotly |
| Dashboard | Streamlit |
| AI Model | Llama3 (Ollama) |
| Architecture | Multi-Agent AI |
| Logging | JSONL |

---

#  Use Cases

This system can be used for:

- Anti-Money Laundering (AML) monitoring
- Fraud detection
- Suspicious Activity Report generation
- Financial compliance automation
- Transaction risk analysis

---

#  Future Improvements

- Graph-based fraud detection
- Network transaction analysis
- Real-time streaming detection
- Integration with banking APIs
- Fine-tuned AML-specific LLM models

---

#  Author

**Akash Singh**

Computer Science Student  
SRM Institute of Science and Technology

Interests:

- Artificial Intelligence
- Financial Technology
- Backend Systems
- Intelligent Automation

---

If you found this project interesting, consider giving it a star.