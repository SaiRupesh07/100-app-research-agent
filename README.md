# 100-App AI Research Agent

A comprehensive research project evaluating AI-agent buildability across 100 SaaS applications. This repository contains:

- **Research Pipeline**: Automated agent-driven research with evidence collection and confidence scoring
- **100-App Dataset**: Fully researched applications with buildability classification, authentication methods, API details, and verification status
- **Interactive Dashboard**: Case study visualization with filtering, analysis, and pattern insights
- **Verification Workflow**: Human-in-the-loop verification methodology ensuring accuracy and honesty

## 📋 Quick Start

### Installation

1. **Clone or download** this repository
2. **Ensure Python 3.11+** is installed ([python.org](https://python.org))
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Research Pipeline

Execute the full research on all 100 apps:

```bash
python scripts/run_research.py
```

**Options:**
- `--limit N`: Test mode - research only N apps (e.g., `--limit 5`)
- `--quiet`: Suppress detailed logging
- `--sample-only`: Generate verification sample without full research
- `--output FILE`: Save results to custom file

**Output:**
- `data/first_pass_research.json` - Full research results
- `data/verification_sample.json` - 20-app sample for human review
- `data/human_review_template.json` - Template for manual verification

### Verification & Accuracy Reporting

After human verification is complete, calculate accuracy:

```bash
python scripts/verify_sample.py --process
```

**Output:**
- `data/verification_results.json` - Completed reviews with accuracy comparison
- `data/accuracy_report.json` - Overall accuracy metrics and improvements

### Generate Interactive Dashboard

Create the case study HTML with analysis and insights:

```bash
python scripts/generate_case_study.py
```

**Output:**
- `case-study/index.html` - Interactive dashboard (open in any browser)

### Validate Dataset

Verify the 100-app dataset integrity:

```bash
python scripts/validate_dataset.py
```

## 🏗️ Project Structure

```
100-app-research-agent/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── PHASE_1_AUDIT.md                   # Initial audit findings
│
├── data/
│   ├── final_dataset.json            # Source of truth: 100 apps
│   ├── first_pass_research.json      # First-pass research output
│   ├── verification_sample.json       # 20-app verification sample
│   ├── human_review_template.json    # Human review template (80 records)
│   ├── verification_results.json      # Human review results (generated)
│   └── accuracy_report.json          # Accuracy metrics (generated)
│
├── docs/
│   └── methodology.md                 # Detailed methodology & classification rules
│
├── scripts/
│   ├── run_research.py               # Main research pipeline orchestrator
│   ├── verify_sample.py              # Verification & accuracy reporting
│   ├── generate_case_study.py        # Dashboard HTML generation
│   └── validate_dataset.py           # Dataset validation
│
├── src/
│   ├── config.py                      # Central configuration & constants
│   ├── research_agent.py              # Main research coordinator
│   └── research/
│       ├── extraction.py              # Data extraction logic
│       ├── classification.py          # Buildability & confidence classification
│       ├── evidence.py                # Evidence management & validation
│       ├── confidence.py              # Confidence scoring
│       └── verification.py            # Verification workflow
│
└── case-study/
    └── index.html                     # Interactive dashboard (generated)
```

## 📊 Dashboard & Analysis

The interactive case study (`case-study/index.html`) includes:

### Overview Statistics
- Total apps researched
- Buildability breakdown (now / friction / gated)
- Self-serve access percentage
- MCP availability
- Research confidence distribution

### Key Findings
- Buildability patterns across all 100 apps
- Authentication method distribution
- Access model insights
- Easy integration wins
- Outreach candidates

### Interactive Data Table
- Search by app name or category
- Filter by buildability, category, confidence, MCP status
- Click any row to view full details:
  - Description and category
  - Authentication methods and API details
  - Buildability verdict with reasoning
  - Evidence URLs with source types
  - Human verification status

### Analysis Sections
- **Easy Wins**: Buildable now + self-serve + broad API + no blockers (~10 apps)
- **Common Blockers**: Frequency-ranked integration barriers
- **Outreach Candidates**: Gated or partnership-required apps
- **Category Analysis**: Buildability and access patterns by category

### Charts & Visualizations
- Buildability distribution (doughnut chart)
- Category coverage (horizontal bar chart)
- Top authentication methods (bar chart)
- Confidence levels (doughnut chart)

## 🔬 Research Methodology

### Pipeline Overview

```
Discovery → Extraction → Classification → Evidence Collection →
Confidence Scoring → First-Pass Research → Verification Sample →
Human Review → Final Dataset → Dashboard
```

### Classification Rules

**Buildability Categories:**
- **Buildable now**: Self-serve access, clear API documentation, no major blockers
- **Buildable with friction**: Requires approval/admin access, limited API, but feasible
- **Gated / Not Practical**: Partner integration only, no public API, or fundamentally not suitable

**Confidence Levels:**
- **High**: Multiple official sources (API docs + auth docs + pricing/examples)
- **Medium**: At least one official source plus additional verification
- **Low**: Primarily third-party information with some official reference
- **Unknown**: Insufficient evidence

**Access Models:**
- **Self-serve**: Credentials available without human approval
- **Approval-required**: Human review needed (admin/team lead)
- **Paid-only**: Requires active subscription
- **Partner**: Direct vendor partnership required
- **Contact sales**: Enterprise/custom arrangements

### Evidence Quality Scoring

Evidence is classified by source type and weighted:
- **Official API docs**: Highest priority (0.4)
- **Official auth docs**: High priority (0.3)
- **Official pricing**: Medium priority (0.3)
- **Official GitHub/MCP**: Medium priority (0.2)
- **Third-party sources**: Lower priority (included for coverage)

### Verification Workflow

1. **First-Pass Research**: Agent researches all 100 apps with evidence collection
2. **Sample Selection**: Deterministic 2-per-category sampling (20 apps reproducible)
3. **Human Review Template**: Generated with 80 verification records (4 fields per app × 20 apps)
4. **Manual Verification**: Reviewers verify against official documentation
5. **Status Tracking**: Marked as correct/incorrect/ambiguous (never fabricated)
6. **Accuracy Report**: Computed accuracy improvements and error patterns

## 📈 Dataset Schema

Each app record in `final_dataset.json` contains:

```json
{
  "id": "app_001",
  "app_name": "App Name",
  "category": "Category Name",
  "description": "Brief description",
  "auth_methods": ["OAuth2", "API Key"],
  "credential_model": "Self-serve",
  "self_serve": true,
  "access_model": "Self-serve",
  "access_notes": "Notes about access",
  "api_types": ["REST", "GraphQL"],
  "api_breadth": "Broad",
  "api_notes": "API coverage notes",
  "mcp_available": false,
  "mcp_type": "standard/custom",
  "mcp_url": "https://...",
  "buildability": "Buildable now",
  "main_blocker": null,
  "buildability_reason": "Explanation of verdict",
  "evidence": [
    {
      "claim": "OAuth2 authentication supported",
      "url": "https://api.example.com/docs",
      "source_type": "official_api_docs"
    }
  ],
  "confidence": "High",
  "research_status": "success",
  "last_checked": "2024-01-15",
  "human_verified": false,
  "verification_status": "pending",
  "verification_notes": ""
}
```

## 🛡️ Design Principles

### 1. **Accuracy Over Cosmetics**
- Evidence is verified against official documentation
- Classification logic is explicit and documented
- Claims are never fabricated
- Verification status remains "pending" until actually completed

### 2. **Reproducibility**
- All research stages are automated and logged
- Sampling for verification is deterministic (2 per category)
- Research agent code is open and auditable
- Configuration and rules are centralized

### 3. **Honesty in Metrics**
- Confidence reflects actual evidence quality
- Buildability verdicts are based on documented criteria
- Human verification is tracked separately from agent research
- Accuracy reports compare first-pass vs final results

### 4. **Modular Architecture**
- Each stage (extraction, classification, evidence, confidence) is testable
- Pipeline orchestration is clear and auditable
- Configuration centralizes constants and rules
- New sources or classification logic can be added without rewriting

## 🔄 Workflow: Running a Full Cycle

### Scenario: Updating with New Research

1. **Run Research** (first-pass on all 100 apps):
   ```bash
   python scripts/run_research.py
   ```

2. **Generate Verification Sample** (deterministic 20 apps):
   ```bash
   python scripts/run_research.py --sample-only
   ```

3. **Manual Verification** (human-in-the-loop):
   - Open `data/human_review_template.json`
   - Verify each record against official documentation
   - Update `human_result`, `human_verified_value`, etc.
   - Save completed template

4. **Calculate Accuracy**:
   ```bash
   python scripts/verify_sample.py --process
   ```

5. **Generate Dashboard**:
   ```bash
   python scripts/generate_case_study.py
   ```

6. **Review Results**:
   - Open `case-study/index.html` in browser
   - Check `data/accuracy_report.json` for metrics

## 📚 Files & Outputs

### Input Files
- **data/final_dataset.json** (100 pre-validated apps, source of truth)

### Generated During Research
- **first_pass_research.json** (agent research results)
- **verification_sample.json** (20-app sample with metadata)
- **human_review_template.json** (80 records for manual review)

### Generated After Human Review
- **verification_results.json** (completed reviews with accuracy)
- **accuracy_report.json** (accuracy metrics and improvements)

### Generated Dashboard
- **case-study/index.html** (interactive analysis dashboard)

## ⚙️ Configuration

Central configuration is in `src/config.py`:

- **BUILDABILITY_CATEGORIES**: Classification categories and descriptions
- **CONFIDENCE_LEVELS**: Confidence tiers and score thresholds
- **AUTH_METHODS**: List of recognized authentication methods
- **API_TYPES**: Recognized API types (REST, GraphQL, etc.)
- **SOURCE_PRIORITY**: Evidence source type rankings
- **COMMON_BLOCKERS**: Recognized integration barriers

## 🧪 Testing

### Test Research on 5 Apps
```bash
python scripts/run_research.py --limit 5
```

### Validate Dataset Integrity
```bash
python scripts/validate_dataset.py
```

### Dry-Run Verification Template
```bash
python scripts/run_research.py --sample-only --quiet
```

## 🛠️ Troubleshooting

### ImportError: No module named 'config'
- Ensure you're running from project root: `cd 100-app-research-agent`
- Both script location and src/ package location should be in Python path

### Human Review Template Not Generated
- Run: `python scripts/run_research.py --sample-only`
- Template will be created at `data/human_review_template.json`

### Dashboard Not Showing Updated Data
- Re-run: `python scripts/generate_case_study.py`
- Clear browser cache or open in incognito mode
- Check for JavaScript console errors (F12 → Console)

### Accuracy Report Shows 0% If Empty
- Ensure human reviews are marked with `human_result` value (not null/pending)
- Run: `python scripts/verify_sample.py --process`
- Check `data/human_review_template.json` for completed records

## 📋 Verification Status

**✅ Complete:**
- First-pass research on 100 apps
- Verification sample generation
- Human review template creation

**⏳ In Progress:**
- Manual verification of 20-app sample
- Accuracy report generation

**Next Steps:**
1. Complete manual verification in `data/human_review_template.json`
2. Run `python scripts/verify_sample.py --process`
3. Review accuracy improvements in `data/accuracy_report.json`

## 📖 Learn More

- **[Methodology](docs/methodology.md)** - Detailed classification rules and research methodology
- **[Phase 1 Audit](PHASE_1_AUDIT.md)** - Initial gap analysis and audit findings
- **[Source Code](src/)** - Complete research pipeline implementation

## 📄 License

This research project is provided as-is for educational and research purposes.

## 👥 Contributing

For improvements, bug reports, or methodology questions, please refer to the [GitHub repository](https://github.com/yourusername/100-app-research-agent).

---

**Last Updated**: January 2024  
**Research Stage**: First-pass complete, human verification in progress  
**Confidence**: Evidence-based classification with high-quality official documentation sources
