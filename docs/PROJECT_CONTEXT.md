# SAR-AI Project Context

## 1. Project Overview
SAR-AI (Suspicious Activity Report Generation System) is an AI-powered compliance automation platform designed to detect suspicious financial transactions and generate regulatory SARs using a multi-agent LLM architecture. It is built for AML / Financial Crime Compliance teams to serve as a locally runnable, realistic, modular research platform and decision-support tool.

## 2. Core Objectives
- Automate detection using statistical and ML anomaly methods.
- Provide a multi-factor transparent risk scoring engine.
- Categorize patterns using rule-based and ML-based AML typologies.
- Build a structured Evidence Engine to prevent LLM hallucination.
- Utilize a Multi-Agent architecture (Investigator, SAR Writer, Auditor, Supervisor).
- Support local LLM execution (Ollama/Llama3) and cloud LLMs (Gemini) via provider abstractions.
- Ensure deterministic validation to catch LLM factual errors.
- Keep the system modular, understandable, and locally runnable.

## 3. Current Architecture
The current architecture is in a transitional state. 
- **Legacy Prototype:** The `app/main.py` and `ui/dashboard.py` files are currently wired to legacy modules inside the `app/` directory (e.g., `app/scorer.py`, `app/typology.py`, `app/llm_service.py`).
- **New Modular Architecture:** A new, highly modular architecture has been implemented in dedicated directories (`data/`, `features/`, `detection/`, `risk/`, `analysis/`, `evidence/`, `agents/`, `llm/`) representing Chunks 1-9 of the development plan. 

The new architecture follows this flow conceptually:
Ingestion (`data/ingestion`) -> Preprocessing (`data/preprocessing`) -> Feature Engineering (`features/engineer.py`) -> Detection (`detection/detector_pipeline.py`) -> Risk Scoring (`risk/scorer.py`) -> Graph/Typologies (`analysis/typologies.py`, `network.py`) -> Evidence Engine (`evidence/engine.py`) -> Multi-Agent Workflow (`agents/supervisor_agent.py`) -> LLM Execution (`llm/factory.py`).

## 4. Current Data Pipeline
The new data pipeline is implemented across several modules:
1. `data/ingestion/dataset_registry.py` & `huggingface_loader.py` & `schema_mapper.py`: Loads CSVs or HuggingFace datasets and maps their schemas automatically.
2. `data/preprocessing/preprocessor.py`: Handles missing values and scales numeric columns.
3. `data/profiling/profiler.py`: Generates dataset statistics and quality reports.
4. `features/engineer.py`: Extracts temporal, behavioral, and counterparty features (e.g., `historical_deviation`, `is_burst_activity`).

## 5. Dataset
- **Source:** Supports local CSV files (e.g., `data/sample_transactions.csv`, `bank_transactions_data_2.csv`) and Hugging Face dataset integration (via `huggingface_loader.py`).
- **Schema:** Schema-agnostic ingestion automatically identifies columns like `amount`, `transaction_id`, `customer_id`, etc.
- **Preprocessing:** Handles missing values and numeric conversion safely.

## 6. ML / Detection Pipeline
- **Implemented in:** `detection/`
- **Methods:** Z-Score deviation (`zscore.py`) and Isolation Forest (`isolation_forest.py`).
- **Pipeline:** `detector_pipeline.py` combines these detectors and flags anomalies.

## 7. Risk Scoring
- **Implemented in:** `risk/scorer.py`
- **Implementation:** Computes a composite 0-100 score based on weighted signals:
  - Anomaly Score (30%)
  - Historical Deviation (30%)
  - Burst Activity (20%)
  - Counterparty Risk (20%)
- **Risk Levels:** Low (0-29.99), Medium (30-59.99), High (60-79.99), Critical (80-100).
- **Explainability:** Returns a dictionary explaining the contribution of each signal. The artificial floor of 78.45 has been removed in the new modular scorer.

## 8. Typology Detection
- **Implemented in:** `analysis/typologies.py`
- **Typologies:** High-value anomaly, Unusual transaction burst, Multiple-counterparty behavior, Structuring, Circular transaction pattern.
- **Logic:** Combines rule-based checks (e.g., $9,000-$9,999.99 for structuring) with ML signals (anomaly score > 0.8). 

## 9. Graph / Entity Analysis
- **Implemented in:** `analysis/network.py`
- **Implementation:** Basic relationship analysis to detect circular patterns (cycles) and analyze entity counterparties.

## 10. Evidence Engine
- **Implemented in:** `evidence/engine.py`
- **Structure:** `EvidencePackage` (Pydantic model) ensuring deterministic payload for LLMs.
- **Content:** Transaction details, customer history (past 10 transactions), anomaly signals, risk score/explanations, typologies, related transactions, and network signals (circular patterns).
- **Provenance:** Guaranteed by extracting facts directly from the dataframe prior to LLM interaction.

## 11. Multi-Agent Architecture
- **Implemented in:** `agents/` using a state machine (`InvestigationState`).
- **Investigator (`investigator_agent.py`):** Summarizes suspicious signals from the evidence package.
- **SAR Writer (`sar_writer_agent.py`):** Drafts the formal compliance narrative.
- **Auditor (`auditor_agent.py`):** Audits the narrative for hallucination or omission against the evidence package.
- **Supervisor (`supervisor_agent.py`):** Orchestrates the loop, allowing revisions up to a max limit if the Auditor finds discrepancies.

## 12. LLM Architecture
- **Implemented in:** `llm/`
- **Abstraction:** `LLMProvider` base class.
- **Providers:** `OllamaProvider` (local inference, e.g., Llama 3), `GeminiProvider` (Google Gemini via API), and `MockProvider` (for testing).
- **Configuration:** Managed via `LLM_PROVIDER` environment variable in `factory.py`.

## 13. Deterministic Validation
- **Status:** Fully implemented in `agents/validators.py`.
- **Architecture:** The `AuditorAgent` runs a deterministic factual validation suite *before* utilizing the LLM for semantic review. 
- **Validators:** Include strict checks for `validate_transaction_id`, `validate_amount`, `validate_currency`, `validate_date`, `validate_customer_id`, and `validate_typology_evidence`.
- **Audit Result Schema:** Uses a structured Pydantic `AuditResult` model containing `overall_passed`, `checks_run`, `discrepancies`, `unsupported_claims`, and `missing_evidence`.
- **LLM Relationship:** The deterministic engine ensures exact factual consistency (amounts, IDs, dates). The LLM is strictly used for semantic coherence and narrative tone.

## 14. SAR Generation
- **Implemented in:** `agents/sar_writer_agent.py` (new architecture) and `app/llm_service.py` (legacy).
- **Output:** Generates a professional SAR narrative based purely on the structured `EvidencePackage`.

## 15. Human Review
- **Status:** Integrated via the Streamlit UI (legacy `ui/dashboard.py`). The user reviews the multi-agent reasoning chain and must manually "Approve & Log" to accept the SAR.

## 16. Persistence
- **Status:** Handled via JSONL appending in `app/audit.py` (legacy). A structured SQLite implementation may be required based on original plans, but currently uses `audit_trail.jsonl`.

## 17. Streamlit Application
- **Implemented in:** `ui/dashboard.py`
- **Features:** File upload, Z-score slider, scatter plot visualization, transaction selection, multi-agent pipeline execution trigger, side-by-side agent reasoning display, SAR review, Audit Logging, and text export. Note: This currently uses the legacy `app/` modules.

## 18. Project Structure
- `agents/`: Multi-agent orchestration and state.
- `analysis/`: Typologies and graph network logic.
- `app/`: Legacy prototype implementation.
- `data/`: Ingestion, schema mapping, profiling, and preprocessing.
- `detection/`: Outlier and anomaly detection models.
- `evidence/`: Evidence package assembly.
- `features/`: Feature engineering (temporal, counterparty).
- `llm/`: Provider abstractions (Ollama, Gemini).
- `risk/`: Transparent risk scoring.
- `tests/`: Pytest suite for the new architecture.
- `ui/`: Streamlit dashboard.

## 19. Dependencies
- `pandas`, `numpy`: Data manipulation.
- `scikit-learn`: Isolation Forest anomaly detection.
- `pydantic`: Structured data validation for evidence.
- `streamlit`: Web dashboard.
- `plotly`: Interactive visualizations.
- `google-generativeai`: Gemini LLM provider.
- `networkx`: (Assuming used in `network.py` for cycle detection).

## 20. Environment Variables
- `LLM_PROVIDER`: 'ollama' or 'gemini'
- `OLLAMA_MODEL`: Default 'llama3'
- `OLLAMA_HOST`: Default 'http://localhost:11434'
- `GEMINI_API_KEY`: Required if using Gemini
- `GEMINI_MODEL`: Default 'gemini-1.5-pro'

## 21. Testing
- **Suite:** Resides in `tests/` (`test_agents.py`, `test_analysis.py`, `test_detection.py`, `test_evidence.py`, `test_ingestion.py`, `test_llm.py`, `test_pipeline.py`, `test_risk.py`).
- **Status:** Extensive test suite exists for all newly created modules (Chunks 1-9).

## 22. Evaluation
- Not explicitly implemented as a standalone evaluation framework module yet, apart from unit tests.

## 23. Completed Chunks
| Chunk | Status | What was implemented |
|------|--------|----------------------|
| 1 | Complete | Project Setup, Config, Logging, Environment structure |
| 2 | Complete | LLM Provider Abstraction (`llm/` directory with Ollama/Gemini/Mock) |
| 3 | Complete | Data Ingestion, Schema Normalization, Profiling (`data/` directory) |
| 4 | Complete | Feature Engineering (`features/engineer.py`) |
| 5 | Complete | ML / Statistical Detection Pipeline (`detection/`) |
| 6 | Complete | Risk Scoring Engine (`risk/scorer.py`) |
| 7 | Complete | Graph/Typology Detection (`analysis/`) |
| 8 | Complete | Structured Evidence Engine (`evidence/engine.py`) |
| 9 | Complete | Multi-Agent Orchestration (`agents/`) |

## 24. Partially Completed Work
- **Persistence:** Currently uses JSONL (`app/audit.py`). Advanced SQLite logging (Phase 11) needs implementation.

## 25. Known Bugs / Technical Debt
- **Integration Debt:** The legacy `app/` directory and `ui/dashboard.py` are completely disjointed from the new architecture (`agents/`, `evidence/`, `risk/`, etc.). 
- **Duplication:** Logic in `app/scorer.py` and `app/typology.py` is now redundant and superseded by the new modular architecture.

## 26. Important Design Decisions
- **LLM Abstraction:** Decoupled business logic from LLM implementations via `llm/factory.py` to allow easy swapping between Ollama and Gemini.
- **Evidence Provenance:** The `EvidenceEngine` strictly separates facts from LLM interpretation. The LLM only receives a deterministically constructed Pydantic object.
- **Multi-Agent State:** Used a state machine (`InvestigationState`) in `SupervisorAgent` to manage routing, eliminating complex chaining logic.
- **Avoided Complexity:** Resisted adding Kafka, Kubernetes, or microservices, keeping the project locally runnable and conceptually clean.

## 27. Original Requirements Still To Implement
- Advanced SQLite persistence (Phase 11).
- Final pipeline testing and evaluation (Phase 13).

## 28. Current Development Position
**COMPLETED THROUGH:** 
Phase 14 (Final Documentation)

**CURRENT CHUNK:** 
FINAL (Full Engineering Audit)

**NEXT TASK:** 
Conduct a comprehensive review of the code, architecture, and compliance standards.

## 29. Future Development Rules
- Do not rewrite working modules unnecessarily.
- Do not duplicate existing functionality.
- Do not introduce unnecessary enterprise infrastructure.
- Do not invent metrics or dataset statistics.
- Do not fabricate regulatory claims.
- Do not allow LLMs to invent transaction facts.
- Preserve deterministic validation concepts.
- Keep the application locally runnable.
- Test after major changes.
- Update this context file after every completed chunk.

## 30. Session Continuation Protocol
When returning after a long break:
1. Read `docs/PROJECT_CONTEXT.md` first.
2. Inspect the current repository.
3. Compare the documented state with the actual code.
4. Identify the last completed chunk.
5. Identify the next incomplete chunk.
6. Check git status/diff if available.
7. Do not assume the documentation is newer than the code.
8. Resolve discrepancies in favor of the actual code.
9. Update `PROJECT_CONTEXT.md` if necessary.
10. Only then continue implementation.
