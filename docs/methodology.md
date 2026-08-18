# Research Methodology & Classification Guide

## Research Objective

Evaluate the **AI-agent buildability** of 100 SaaS applications – that is, whether an AI agent can realistically call the application's API to perform useful actions with minimal friction and maximum autonomy.

This involves determining:
1. Can a developer obtain API credentials?
2. Does the API exist and is it documented?
3. Is the API surface broad enough to be useful?
4. How much friction is involved in the integration?
5. Can decisions be made autonomously or are approvals needed?

---

## 🔬 Research Pipeline

### Stage 1: Discovery
- Load 100 application names and categories
- Establish baseline research parameters
- Initialize evidence tracking

### Stage 2: Extraction
Systematic research of each application:
- **Authentication Methods**: OAuth2, API Key, JWT, Basic Auth, etc.
- **Credential Model**: Self-serve signup vs approval-required
- **Access Model**: Free tier, Paid required, Partner-only, etc.
- **API Types**: REST, GraphQL, SDK, CLI, Webhooks, etc.
- **API Breadth**: Coverage of core business functions
- **MCP Availability**: Model Context Protocol server existence
- **Rate Limits & Quotas**: Any significant constraints

### Stage 3: Classification
Apply consistent rules to classify:
- **Buildability** (now / friction / gated)
- **Confidence** (high / medium / low / unknown)
- **Access Model** (self-serve / approval / paid / partner)
- **Primary Blocker** (if any)

### Stage 4: Evidence Collection
Document findings with:
- **Claim**: What we determined (e.g., "OAuth2 authentication supported")
- **URL**: Where we found evidence
- **Source Type**: Category of source (official_api_docs, third_party, etc.)

### Stage 5: Confidence Scoring
Rate how confident we are in each finding:
- **Evidence Quality**: Are sources official or third-party?
- **Coverage**: How complete is the information?
- **Consistency**: Do multiple sources agree?
- **Recency**: When was the documentation last updated?

### Stage 6: First-Pass Research
Generate `first_pass_research.json` containing all 100 apps with agent findings

### Stage 7: Verification Sample
Deterministically select 20 representative apps (2 per category) for human review

### Stage 8: Human Review
Manual verification against official documentation, marking:
- ✅ Correct
- ❌ Incorrect
- ⚠️ Ambiguous
- 🤷 Unverifiable

### Stage 9: Accuracy Report
Compute accuracy metrics and improvements from human feedback

---

## 📊 Dataset Schema

Each record in `final_dataset.json` contains:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | String | Unique identifier | "app_001" |
| `app_name` | String | Application name | "Slack" |
| `category` | String | One of 10 categories | "Communication" |
| `description` | String | One-sentence description | "Team messaging platform" |
| **Authentication** |
| `auth_methods` | Array | List of auth mechanisms | `["OAuth2", "API Key"]` |
| `credential_model` | String | How credentials are obtained | "Self-serve" |
| `self_serve` | Boolean | Can dev get credentials independently? | `true` |
| **API Details** |
| `access_model` | String | Type of access required | "Self-serve Free" |
| `access_notes` | String | Additional access info | "Free tier limited to 25 users" |
| `api_types` | Array | API technologies available | `["REST", "WebSocket"]` |
| `api_breadth` | String | Coverage of core functions | "Broad" |
| `api_notes` | String | Details about API coverage | "Covers channels, messages, users" |
| **MCP** |
| `mcp_available` | Boolean | Model Context Protocol available? | `false` |
| `mcp_type` | String | Type of MCP (if available) | "Official" |
| `mcp_url` | String | URL to MCP implementation | "https://..." |
| **Buildability Assessment** |
| `buildability` | String | One of 3 categories | "Buildable now" |
| `main_blocker` | String/null | Primary obstacle (if any) | "Admin approval required" |
| `buildability_reason` | String | Explanation of verdict | "Clear API with free tier..." |
| **Evidence & Confidence** |
| `evidence` | Array | Supporting documentation | See Evidence Model below |
| `confidence` | String | One of 4 levels | "High" |
| **Research Tracking** |
| `research_status` | String | success, failed, unknown | "success" |
| `last_checked` | Date | ISO 8601 date of research | "2024-01-15" |
| `human_verified` | Boolean | Was this manually verified? | `false` |
| `verification_status` | String | correct, incorrect, ambiguous | "pending" |
| `verification_notes` | String | Verifier comments | "" |

### Evidence Model

Each evidence object contains:

```json
{
  "claim": "OAuth2 authentication supported",
  "url": "https://api.example.com/docs/auth",
  "source_type": "official_api_docs"
}
```

**Source Type Priority (Highest to Lowest):**

1. **official_api_docs**: Official API documentation
2. **official_auth_docs**: Official authentication guide
3. **official_pricing**: Official pricing/access page
4. **official_github**: Official GitHub repository
5. **official_mcp**: Official MCP server repository
6. **third_party_github**: Third-party GitHub project
7. **third_party_blog**: Tech blog or tutorial
8. **third_party_forum**: Community forum or Q&A
9. **third_party_sdk**: Unofficial SDK documentation

---

## 🏗️ Buildability Classification

### Decision Tree

```
Is there a public API?
├─ No → GATED / NOT PRACTICAL
└─ Yes:
   ├─ Can credentials be self-served?
   │  ├─ No (partner/contact sales required) → GATED / NOT PRACTICAL
   │  └─ Yes:
   │     ├─ API breadth is Broad or Moderate?
   │     │  ├─ No (Narrow/Very Narrow) → BUILDABLE WITH FRICTION
   │     │  └─ Yes:
   │     │     ├─ Are there major blockers?
   │     │     │  ├─ Yes (admin approval, limited scopes) → BUILDABLE WITH FRICTION
   │     │     │  └─ No → BUILDABLE NOW
```

### Category Definitions

**Buildable Now** 🟢
- Public API with clear documentation
- Self-serve credential acquisition
- Sufficient API breadth (Broad or Moderate)
- No major approval requirements
- Developer can integrate independently and immediately
- Examples: Slack, GitHub, OpenAI

**Buildable with Friction** 🟡
- API exists but requires:
  - Approval workflow (OAuth approval, admin handshake)
  - Paid plan for certain features
  - Limited API scope (Narrow breadth)
  - Rate limits or quota constraints
- Integration is feasible but requires extra steps
- May require human involvement or paid subscription
- Examples: Salesforce (requires approval), Stripe (requires paid account)

**Gated / Not Practical** 🔴
- Partner integration required (direct vendor arrangement)
- No meaningful public API
- Closed ecosystem (enterprise-only)
- "Contact sales" as primary access method
- Fundamentally not designed for third-party integration
- Examples: Proprietary enterprise systems, white-labeled solutions

### Main Blockers (When Applicable)

When buildability is not "Buildable now", identify the primary blocker:

| Blocker | Description | Typical Buildability |
|---------|-------------|----------------------|
| Partner approval | Requires direct vendor arrangement | Gated |
| Contact sales | Enterprise/custom arrangements | Gated |
| Admin approval | OAuth approval or admin workflow | Friction |
| Limited API | API scope doesn't cover core functions | Friction |
| Paid plan | Free tier lacks API access | Friction |
| Rate limits | Very restrictive quota limits | Friction |
| No API | No public API at all | Gated |

---

## 🔐 Authentication Methods

### Recognized Methods

- **OAuth2**: Industry standard, delegated access
- **OAuth 1.0**: Legacy standard
- **API Key**: Simple bearer token
- **JWT**: JSON Web Token (stateless)
- **Basic Auth**: Username + password (HTTP)
- **Webhook**: Server-to-server callbacks
- **CLI**: Command-line access (not API but useful)
- **SDK**: Native library (often wraps REST)
- **GraphQL**: Query language API
- **gRPC**: Binary protocol (less common)

### Credential Model

How a developer obtains credentials:

- **Self-serve**: Automatic via signup/dashboard (BEST for AI agents)
- **Approval-required**: Human review process
- **Paid-only**: Requires payment
- **Partner**: Direct arrangement
- **Mixed**: Varies by tier or feature

---

## 📡 API Classification

### API Types

The API technologies available:

- **REST**: Most common, JSON-based
- **GraphQL**: Query language for APIs
- **gRPC**: High-performance RPC
- **SDK**: Native library wrapper
- **CLI**: Command-line tools
- **Webhooks**: Server-to-server callbacks
- **MQTT/WebSocket**: Real-time messaging

### API Breadth

Coverage of core business functions:

| Breadth | Definition | Example Coverage |
|---------|-----------|------------------|
| **Broad** | Covers most/all major features | 80%+ of app functionality |
| **Moderate** | Covers major features but gaps | 50-80% of functionality |
| **Narrow** | Limited to specific features | 20-50% of functionality |
| **Very Narrow** | Only basic operations | <20% of functionality |
| **No Public API** | No API at all | 0% |
| **Unknown** | Unable to determine | Need more research |

---

## 📊 Confidence Scoring

### Scoring Rubric

**High Confidence** (0.7 - 1.0)
- Multiple official sources
- API documentation clearly supports claims
- Official auth documentation exists
- Recent updates (within 6 months)
- Clear, consistent information across sources
- Evidence count: 3+ official sources

**Medium Confidence** (0.4 - 0.7)
- At least one official source
- Good API documentation but gaps remain
- Some third-party verification
- Mix of official and community information
- Evidence count: 1-2 official + community verification

**Low Confidence** (0.1 - 0.4)
- Mostly third-party information
- Official sources are minimal
- Community forums or blogs are primary sources
- Some ambiguity or conflicting information
- Evidence count: Primarily third-party

**Unknown** (< 0.1)
- Insufficient evidence
- No official documentation found
- Contradictory information
- App has limited public information
- Evidence count: < 1 reliable source

### Confidence Factors

1. **Evidence Quality** (60% weight)
   - Official sources preferred over third-party
   - Source recency and relevance
   - Source authority and credibility

2. **Coverage** (30% weight)
   - How many aspects of buildability are documented?
   - Are critical fields (auth, API, access) well-covered?
   - Any major information gaps?

3. **Consistency** (10% weight)
   - Do multiple sources agree?
   - Any conflicting information?
   - Has the API changed recently?

---

## 🟢 MCP (Model Context Protocol) Analysis

### What is MCP?

Model Context Protocol is a standard for connecting AI models to tools and data sources. An MCP server wraps an application's API in a standardized protocol.

### MCP Types

- **Official MCP**: Published by the vendor
- **Community MCP**: Maintained by community members
- **Third-party MCP**: Provided by third-party integration service
- **Custom MCP**: Internally developed

### MCP Availability

Tracked as boolean field `mcp_available`:
- `true`: At least one MCP implementation exists
- `false`: No known MCP implementation

MCP is **not required** for buildability (most apps don't have it). It's a **bonus capability** that simplifies AI integration.

---

## ✅ Human Verification Process

### Sample Selection

- **Deterministic**: 2 apps per category (20 total)
- **Reproducible**: Always the same 20 apps
- **Representative**: Covers all categories and difficulty levels

### Verification Template

Each record in `human_review_template.json`:

```json
{
  "app_id": "app_001",
  "app_name": "Slack",
  "field": "auth_methods",
  "agent_value": ["OAuth2", "API Key"],
  "official_source": "https://api.slack.com/authentication",
  "human_result": "pending",
  "human_verified_value": null,
  "human_notes": "",
  "verification_date": null,
  "verifier_name": null
}
```

### Verification Status Values

- **pending**: Not yet reviewed
- **correct**: Agent finding matches official documentation
- **incorrect**: Agent finding contradicts official documentation
- **ambiguous**: Official documentation is unclear
- **unverifiable**: Cannot be verified from available sources

### Verification Workflow

1. **Reviewer opens** `data/human_review_template.json`
2. **For each record**:
   - Visit the `official_source` URL
   - Compare `agent_value` with official documentation
   - Set `human_result` to one of: correct/incorrect/ambiguous/unverifiable
   - If incorrect, fill `human_verified_value` with correct info
   - Add notes in `human_notes` if needed
   - Record `verification_date` and `verifier_name`
3. **Save completed template**
4. **Run accuracy calculation**: `python scripts/verify_sample.py --process`

### Accuracy Metrics

After human review is complete:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "verification_stage": "human_review_complete",
  "sample_size": 20,
  "total_records_reviewed": 80,
  "accuracy": {
    "correct": 76,
    "incorrect": 2,
    "ambiguous": 2,
    "unverifiable": 0,
    "accuracy_percentage": 95.0
  },
  "improvements_needed": [
    {
      "app_id": "app_005",
      "field": "auth_methods",
      "error": "Listed GraphQL as auth method (auth method != API type)"
    }
  ]
}
```

---

## 📋 Classification Rules Summary

### Access Model Classification

```python
if requires_partnership:
    access_model = "Partner / Contact Sales"
elif requires_paid_plan:
    access_model = "Paid Plan Required"
elif has_approval_workflow:
    access_model = "Admin / Approval Required"
elif self_serve:
    access_model = "Self-serve Free" or "Self-serve Paid"
else:
    access_model = "Unknown"
```

### Buildability Classification

```python
if not has_public_api:
    buildability = "Gated / Not Practical"
elif requires_partnership:
    buildability = "Gated / Not Practical"
elif not self_serve_available:
    buildability = "Gated / Not Practical"
elif api_breadth in ["Broad", "Moderate"] and no_major_blockers:
    buildability = "Buildable now"
else:
    buildability = "Buildable with friction"
```

### Confidence Classification

```python
official_source_count = count of evidence from official sources
if official_source_count >= 2:
    confidence = "High"
elif official_source_count == 1:
    confidence = "Medium"
elif total_evidence >= 2:
    confidence = "Medium"
elif total_evidence >= 1:
    confidence = "Low"
else:
    confidence = "Unknown"
```

---

## 🔍 Special Cases & Ambiguities

### When Official Docs Conflict

- Prioritize current API version documentation
- Check GitHub for recent changes
- Look for release notes or changelog
- Mark as "Medium" confidence if conflicting

### Free Tier API Limitations

- Classify based on free tier capabilities
- Note paid-tier advantages separately
- If free tier has API, mark as "Buildable now"
- If API only in paid tier, mark as "Buildable with friction"

### OAuth Approval Workflows

- OAuth approval is NOT the same as partner approval
- OAuth approval (standard flow) = "Buildable with friction"
- Partner arrangement required = "Gated"
- Document the specific approval process

### Deprecated vs. Current APIs

- Focus on current, supported API versions
- Note if legacy API still exists
- Mention migration paths if available
- Use current version for buildability verdict

---

## 📈 Dataset Statistics

### Expected Distributions

Based on 100 SaaS applications:

- **Buildable now**: 40-60% (most with established public APIs)
- **Buildable with friction**: 25-40% (approval/paid requirements)
- **Gated**: 10-20% (partnerships, enterprise-only)

- **High confidence**: 5-15% (official docs are rare)
- **Medium confidence**: 75-85% (most apps documented)
- **Low confidence**: 5-10% (hard to find info)
- **Unknown**: <5% (very few apps)

- **OAuth2**: 30-40% of apps
- **API Key**: 50-60% of apps
- **Self-serve**: 70-80% of apps

---

## 🔄 Continuous Improvement

### When to Re-Run Research

- Quarterly for major app ecosystem changes
- When planning new AI agent integrations
- After significant API updates
- When verification reveals systematic errors

### How to Add New Validation Rules

1. Document the rule in this methodology
2. Implement in `src/research/classification.py`
3. Add test cases
4. Re-run research on sample
5. Verify accuracy improvements

### Feedback Loop

1. Human reviewers identify errors
2. Errors are categorized
3. Classification rules are refined
4. Research agent is updated
5. Next cycle improves accuracy

---

## 📚 References

- [OAuth 2.0 Specification](https://tools.ietf.org/html/rfc6749)
- [OpenAPI Specification](https://spec.openapis.org/)
- [GraphQL Specification](https://graphql.org/learn/queries/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [REST API Best Practices](https://restfulapi.net/)

---

**Last Updated**: January 2024  
**Version**: 1.0  
**Maintained By**: Research Team
