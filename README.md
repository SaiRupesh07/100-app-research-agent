# 100-App AI Research Agent

> A research and analysis pipeline for evaluating how practical it is to build AI-agent integrations across 100 SaaS applications.

## 🔗 Project Links

- **Live Case Study:** https://sairupesh07.github.io/100-app-research-agent/case-study/
- **GitHub Repository:** https://github.com/SaiRupesh07/100-app-research-agent

---

## 📌 Overview

The **100-App AI Research Agent** is an evidence-driven research pipeline designed to evaluate SaaS applications from an AI-agent integration perspective.

For each application, the project investigates key integration dimensions including:

- Authentication and credential models
- Access and onboarding requirements
- API breadth and available API types
- MCP availability
- Buildability for an AI-agent integration
- Primary integration blockers
- Evidence quality and source provenance
- Research confidence
- Human verification status

The project combines automated research, structured evidence collection, deterministic sampling, human verification, validation, and an interactive case-study dashboard.

---

## 🎯 Objective

The goal is not simply to collect API documentation.

The project answers a more practical product question:

> **How feasible is it to build an AI-agent integration for each SaaS application, and what barriers would an integration team encounter?**

The final analysis groups applications into three buildability categories:

| Category | Meaning |
|---|---|
| **Buildable now** | Self-serve access, clear API documentation, and no major integration blocker |
| **Buildable with friction** | Integration is feasible but requires approval, administrative access, limited APIs, or other additional effort |
| **Gated / Not Practical** | Partner-only access, no practical public API, or a fundamental integration blocker |

---

## 📊 Current Results

The current final dataset contains **100 SaaS applications**.

### Buildability

| Buildability | Apps | Share |
|---|---:|---:|
| Buildable now | 49 | 49.0% |
| Buildable with friction | 41 | 41.0% |
| Gated / Not Practical | 10 | 10.0% |
| **Total** | **100** | **100%** |

### Human Verification

A deterministic verification sample covering **20 applications** was reviewed across the key research fields.

- **Verification records:** 90
- **Completed reviews:** 90
- **Correct:** 90
- **Incorrect:** 0
- **Ambiguous:** 0
- **Verified accuracy:** **100.0%**

The verification results are stored in:

- `data/verification_results.json`
- `data/accuracy_report.json`

> **Verification note:** The 100% figure represents the completed human-review sample, not a claim that every field of all 100 applications was independently human-verified.

---

## 🧠 What the Research Evaluates

Each application is evaluated using a consistent schema.

### 1. Authentication

Examples include:

- OAuth2
- API keys
- JWT
- Bearer tokens
- Other documented authentication mechanisms

### 2. Access Model

Applications are classified according to practical access requirements:

- Self-serve
- Approval-required
- Paid-only
- Partner
- Contact sales

### 3. API Breadth

The research evaluates the breadth and practicality of the available APIs, including:

- REST
- GraphQL
- Webhooks
- Domain-specific APIs
- Other documented interfaces

### 4. MCP Availability

The dataset records whether a documented MCP implementation is available and, where applicable, records its type and source.

### 5. Buildability

Buildability combines access requirements, authentication, API coverage, integration blockers, and available evidence into a practical implementation verdict.

### 6. Evidence & Confidence

Research claims are linked to source evidence wherever possible.

Confidence levels are:

- **High** — strong evidence from multiple authoritative sources
- **Medium** — sufficient official evidence with additional supporting information
- **Low** — limited or primarily secondary evidence
- **Unknown** — insufficient evidence for a reliable conclusion

---

## 🏗️ Research Pipeline

The complete workflow is:

```text
Application List
      ↓
Source Discovery
      ↓
Evidence Extraction
      ↓
Classification
      ↓
Confidence Scoring
      ↓
First-Pass Research
      ↓
Verification Sampling
      ↓
Human Review
      ↓
Verification Results
      ↓
Final Dataset
      ↓
Interactive Case Study
```

The architecture is modular so that individual research stages can be inspected, tested, and extended independently.

---

## 🔬 Methodology

### Research Approach

The research pipeline prioritizes authoritative sources, especially:

1. Official API documentation
2. Official authentication documentation
3. Official pricing/access documentation
4. Official GitHub or MCP documentation
5. Supporting third-party sources when necessary

The objective is to make each classification traceable to evidence rather than relying on unsupported assumptions.

### Verification Approach

The verification workflow uses a deterministic sample of **20 applications**, with multiple research fields checked for each sampled application.

The current verification fields are:

- `auth_methods`
- `access_model`
- `api_breadth`
- `buildability`
- `mcp_available` where applicable

The completed verification dataset contains **90 review records**.

---

## 📁 Project Structure

```text
100-app-research-agent/
│
├── README.md
├── requirements.txt
│
├── data/
│   ├── apps.json
│   ├── final_dataset.json
│   ├── first_pass_research.json
│   ├── verification_sample.json
│   ├── human_review_template.json
│   ├── verification_results.json
│   └── accuracy_report.json
│
├── docs/
│   └── methodology.md
│
├── scripts/
│   ├── run_research.py
│   ├── verify_sample.py
│   ├── process_verification.py
│   ├── generate_case_study.py
│   └── validate_dataset.py
│
├── src/
│   ├── config.py
│   ├── research_agent.py
│   ├── process_verification.py
│   └── research/
│       ├── extraction.py
│       ├── classification.py
│       ├── evidence.py
│       ├── confidence.py
│       ├── source_discovery.py
│       └── verification.py
│
├── case-study/
│   └── index.html
│
└── index.html
```

---

## ⚙️ Requirements

- Python 3.11+
- Internet access for live research
- Dependencies listed in `requirements.txt`

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/SaiRupesh07/100-app-research-agent.git
cd 100-app-research-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the research pipeline

To run research across the application dataset:

```bash
python scripts/run_research.py
```

Useful options:

```bash
python scripts/run_research.py --limit 5
python scripts/run_research.py --quiet
python scripts/run_research.py --sample-only
```

### 4. Generate the verification sample

```bash
python scripts/run_research.py --sample-only
```

This creates the verification sample and review template.

### 5. Complete human verification

Open:

```text
data/human_review_template.json
```

For every verification record:

1. Open the supplied official source.
2. Compare the agent's value with the official documentation.
3. Set `human_result` to:
   - `correct`
   - `incorrect`
   - `ambiguous`
   - `pending`
4. If incorrect, provide `human_verified_value`.
5. Add `human_notes` explaining the decision.
6. Record the verification date and verifier where applicable.

### 6. Process verification results

After completing the human review:

```bash
python scripts/process_verification.py
```

This generates:

```text
data/verification_results.json
data/accuracy_report.json
```

### 7. Generate the case study

```bash
python scripts/generate_case_study.py
```

The dashboard is generated at:

```text
case-study/index.html
```

### 8. Validate the dataset

```bash
python scripts/validate_dataset.py
```

Expected validation:

```text
Records count: 100
All IDs unique
All app names unique
All structural checks passed
```

---

## 📈 Interactive Case Study

The live case study provides a recruiter-friendly view of the research.

### Overview

- 100-app research summary
- Buildability distribution
- Access model analysis
- MCP availability
- Confidence distribution

### Key Findings

- Buildability patterns
- Authentication patterns
- Integration barriers
- Easy integration opportunities
- Outreach candidates
- Category-level trends

### Interactive Table

The dashboard supports:

- Search by application name
- Category filtering
- Buildability filtering
- Confidence filtering
- MCP filtering
- Detailed application views
- Evidence/source inspection
- Verification status

### Verification Section

The dashboard reports the current verification state, including:

- 20 sampled applications
- 90 verification checks
- Completed human review
- Correct/incorrect/ambiguous counts
- Verified accuracy

---

## 📦 Key Data Files

### `data/final_dataset.json`

The final structured dataset containing the 100 researched applications.

### `data/first_pass_research.json`

Raw/first-pass research output generated by the research pipeline.

### `data/verification_sample.json`

Deterministically selected sample of applications used for verification.

### `data/human_review_template.json`

Human-review template containing the verification records and review fields.

### `data/verification_results.json`

Processed human-verification results.

### `data/accuracy_report.json`

Summary of completed verification checks and accuracy statistics.

---

## 🧾 Dataset Schema

A typical application record contains fields such as:

```json
{
  "id": "app_001",
  "app_name": "App Name",
  "category": "Category",
  "description": "Application description",
  "auth_methods": ["OAuth2", "API Key"],
  "credential_model": "Self-serve",
  "self_serve": true,
  "access_model": "Self-serve",
  "access_notes": "Access details",
  "api_types": ["REST", "GraphQL"],
  "api_breadth": "Broad",
  "api_notes": "API coverage notes",
  "mcp_available": false,
  "mcp_type": null,
  "mcp_url": null,
  "buildability": "Buildable now",
  "main_blocker": null,
  "buildability_reason": "Reason for the buildability verdict",
  "evidence": [],
  "confidence": "High",
  "research_status": "success"
}
```

Additional verification fields may be present depending on the research stage.

---

## 🛡️ Design Principles

### 1. Evidence Over Assumptions

Research conclusions should be grounded in documented evidence whenever possible.

### 2. Accuracy Over Cosmetics

The dashboard is intended to communicate research results clearly, but visual presentation does not replace evidence quality.

### 3. Honest Verification

Human verification is tracked separately from automated research.

A record remains pending until a reviewer actually checks it.

### 4. Reproducibility

The pipeline, sampling process, classification rules, and configuration are structured so the research can be rerun and audited.

### 5. Modular Architecture

Research stages are separated into modules for:

- Discovery
- Extraction
- Evidence
- Classification
- Confidence
- Verification

This makes the system easier to extend and debug.

---

## 🧪 Testing & Validation

### Test the research pipeline on a small sample

```bash
python scripts/run_research.py --limit 5
```

### Validate the final dataset

```bash
python scripts/validate_dataset.py
```

### Generate the verification sample

```bash
python scripts/run_research.py --sample-only
```

### Process completed verification

```bash
python scripts/process_verification.py
```

### Regenerate the dashboard

```bash
python scripts/generate_case_study.py
```

---

## 🔍 Verification & Quality Control

The project separates three concepts:

### Automated Research

The research agent gathers and structures information from available sources.

### Evidence

Each research claim can be associated with source information and source type.

### Human Verification

A deterministic sample is manually reviewed against official documentation.

This separation prevents the verification layer from being confused with the automated research layer.

---

## 📊 Current Verification Snapshot

```text
Applications researched:        100
Verification sample:            20
Verification checks:             90

Completed reviews:               90
Correct:                          90
Incorrect:                         0
Ambiguous:                         0

Verified accuracy:            100.0%
```

The accuracy figure applies to the **90 completed verification checks in the sampled set**.

---

## 🗂️ Reproducibility

A complete research cycle can be reproduced with:

```bash
python scripts/run_research.py
python scripts/run_research.py --sample-only
```

After human review:

```bash
python scripts/process_verification.py
python scripts/generate_case_study.py
python scripts/validate_dataset.py
```

The resulting artifacts are stored under `data/` and the generated dashboard is stored under `case-study/`.

---

## 🧭 Troubleshooting

### `ImportError: No module named 'config'`

Make sure commands are executed from the project root:

```bash
cd 100-app-research-agent
```

### Dashboard shows outdated data

Regenerate it:

```bash
python scripts/generate_case_study.py
```

Then refresh the browser or open the page in a private/incognito window.

### Verification report shows pending reviews

Check:

```text
data/human_review_template.json
```

Ensure all intended review records have a valid `human_result`, then run:

```bash
python scripts/process_verification.py
```

### Dataset validation fails

Run:

```bash
python scripts/validate_dataset.py
```

and inspect the reported structural issue before modifying the dataset.

---

## 📚 Documentation

- **Methodology:** `docs/methodology.md`
- **Phase 1 Audit:** `PHASE_1_AUDIT.md`
- **Final Audit:** `FINAL_AUDIT_REPORT.md`
- **Completion Summary:** `COMPLETION_SUMMARY.md`
- **Source Code:** `src/`
- **Research Scripts:** `scripts/`

---

## 📌 Project Status

### Completed

- [x] Research pipeline
- [x] 100-app dataset
- [x] Evidence collection
- [x] Buildability classification
- [x] Confidence scoring
- [x] Verification sample generation
- [x] Human review workflow
- [x] 90 verification checks
- [x] Verification results and accuracy report
- [x] Dataset validation
- [x] Interactive case-study dashboard
- [x] GitHub Pages deployment
- [x] Source repository publication

### Current Deliverables

- **100-app structured research dataset**
- **90 completed verification checks**
- **Interactive live case study**
- **Reproducible research pipeline**
- **Auditable evidence and verification artifacts**

---

## 📄 License

This project is provided as-is for educational and research purposes.

---

## 👤 Author

**Sai Rupesh**

Computer Science & Engineering Graduate  
NIT Patna — 2026

---

## 🔗 Links

- Live Case Study: https://sairupesh07.github.io/100-app-research-agent/case-study/
- GitHub Repository: https://github.com/SaiRupesh07/100-app-research-agent

---

**Last Updated:** August 18, 2026  
**Project Status:** Complete  
**Research Scope:** 100 SaaS applications  
**Verification Scope:** 20-app sample / 90 checks
