# PRD: LabelCheck — AI-Powered Alcohol Label Verification App

## Context

This is a take-home project for TTB (Alcohol and Tobacco Tax and Trade Bureau). The goal is a **standalone "second screen" web tool** that compliance agents use alongside their existing COLA system to perform rapid, AI-powered first-pass checks on alcohol beverage labels. It does NOT replace human judgment or integrate with COLA.

**Source:** `takehome.md` — all requirements below are traced to specific stakeholder interviews and sections.

**Guiding principle** (takehome.md line 113): *"A working core application with clean code is preferred over an over-engineered solution that tries to do everything."*

---

## Requirements Traceability

| Requirement | Source (takehome.md) | Priority |
|---|---|---|
| Single label upload + analysis | Sarah Chen: "checking that stuff is there" (line 17) | P0 |
| Results in ~5 seconds | Sarah Chen: "If we can't get results back in about 5 seconds, nobody's going to use it" (line 19) | P0 |
| Government warning check (exact text, all caps header) | Jenny Park: "word-for-word, GOVERNMENT WARNING in all caps and bold" (line 57) | P0 |
| Check all 7 mandatory elements | "Additional Context" section (lines 69-77) | P0 |
| Extremely simple UI | Sarah: "my mother could figure out" (line 21); Dave: "a button that says 'check this label'" (line 49) | P0 |
| Batch upload (50+ labels) | Sarah: "handle batch uploads...Janet has been asking for years" (line 23) | P1 |
| Results history | User's requirement for checks/evaluations on correct labels | P1 |
| Non-English label detection | Jenny: "Even just flagging 'hey, this might not be in English'" (line 59) | P2 (nice-to-have) |
| Application details matching (mandatory) | Core workflow: agents submit COLA application details + label image, system verifies match | P0 |
| Batch upload with CSV matching | Batch: CSV (required) maps filenames to application details for comparison | P1 |
| Deployed URL | Deliverables section (line 102) | P0 |
| README with setup instructions | Deliverables section (lines 98-100) | P0 |
| Tool aids agents, doesn't replace judgment | Dave: "don't tell me it's going to replace my judgment" (line 49) | Design principle |

---

## Tech Stack Decisions

| Layer | Choice | Rationale |
|---|---|---|
| **Backend** | Python + FastAPI | Fast async framework, great for AI service integrations, clean API design |
| **Frontend** | React + TypeScript + Vite | Type-safe, component-based, fast dev iteration with Vite HMR |
| **Styling** | Tailwind CSS | Utility-first, consistent clean design, no custom design system needed for MVP |
| **OCR** | Azure AI Vision 4.0 (Image Analysis API) | Purpose-built for "in-the-wild" images like product labels. Fast synchronous API. Free tier available for testing. |
| **Compliance Analysis** | LLM via abstract interface | Azure OpenAI (GPT-4o) as primary, Anthropic Claude as alternate. Interface pattern allows swapping providers. |
| **Database** | SQLite + SQLAlchemy async | Zero infrastructure for MVP. Same ORM models migrate to PostgreSQL by changing one connection string. |
| **Deployment** | Azure Container Apps (Docker) | Docker-based, supports the testable URL deliverable, aligns with Azure services already in use |
| **Service Abstraction** | Python Protocol pattern | OCR and LLM providers are behind interfaces so they can be swapped without changing business logic |

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────────────────────────────┐
│   React SPA     │────▶│  FastAPI Backend                         │
│   (Nginx)       │     │                                          │
│                 │◀────│  /api/analysis/single   (single label)   │
│  - Upload Page  │     │  /api/batch/upload      (batch labels)   │
│  - History Page │     │  /api/batch/{id}/stream  (SSE progress)  │
│  - Result Page  │     │  /api/analysis/          (history)       │
└─────────────────┘     │                                          │
                        │  ┌─────────────────────────────────┐     │
                        │  │  Analysis Pipeline               │     │
                        │  │                                   │     │
                        │  │  1. OCR Service (Azure Vision)    │     │
                        │  │     ↓  extracted text             │     │
                        │  │  2. Compliance Engine             │     │
                        │  │     - Regex rules (instant)       │     │
                        │  │     - LLM analysis (2-3 sec)      │     │
                        │  │     ↓  merged findings            │     │
                        │  │  3. Store results (SQLite)        │     │
                        │  └─────────────────────────────────┘     │
                        └──────────────────────────────────────────┘
```

### Application Details Matching Flow

```
Single Upload:
  Agent fills application details form (required) ──┐
  Agent uploads label image ────────────────────────┤
                                                    ▼
  Pipeline: OCR → Compliance Check + Application Matching → Store

Batch Upload:
  Agent uploads N label images ──────────────────┐
  Agent uploads CSV with application details (required) ──┤
                                                          ▼
  For each image: match CSV row → OCR → Compliance Check + Matching → Store
```

**Performance budget (must total < 5 seconds):**
- File save: < 200ms
- Azure Vision OCR: 1-2 sec
- LLM compliance analysis: 2-3 sec
- DB writes: < 50ms

---

## Project Structure

```
TTB_label/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                     # FastAPI app, CORS, router includes
│   │   ├── config.py                   # Pydantic Settings (env vars)
│   │   ├── dependencies.py             # DI: get_db, get_ocr_service, get_llm_service, get_pipeline
│   │   │
│   │   ├── models/                     # SQLAlchemy ORM
│   │   │   ├── base.py                 # DeclarativeBase + TimestampMixin
│   │   │   ├── label.py                # Label table
│   │   │   ├── analysis.py             # AnalysisResult table
│   │   │   └── batch.py                # BatchJob table
│   │   │
│   │   ├── schemas/                    # Pydantic request/response models
│   │   │   ├── label.py
│   │   │   ├── analysis.py
│   │   │   ├── batch.py
│   │   │   └── compliance.py           # ComplianceFinding, ComplianceReport
│   │   │
│   │   ├── routers/                    # API endpoints
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── labels.py               # POST /api/labels/upload
│   │   │   ├── analysis.py             # POST /api/analysis/single, GET /api/analysis/{id}, GET /api/analysis/
│   │   │   └── batch.py                # POST /api/batch/upload, GET /api/batch/{id}, GET /api/batch/{id}/stream
│   │   │
│   │   ├── services/
│   │   │   ├── ocr/
│   │   │   │   ├── base.py             # OCRServiceProtocol
│   │   │   │   ├── azure_vision.py     # Azure AI Vision 4.0 implementation
│   │   │   │   └── mock.py             # Mock for testing
│   │   │   ├── llm/
│   │   │   │   ├── base.py             # LLMServiceProtocol
│   │   │   │   ├── azure_openai.py     # Azure OpenAI implementation
│   │   │   │   ├── anthropic.py        # Claude implementation (alternate)
│   │   │   │   └── mock.py             # Mock for testing
│   │   │   ├── compliance/
│   │   │   │   ├── engine.py           # Hybrid regex + LLM compliance checker
│   │   │   │   ├── rules.py            # Deterministic regex rules
│   │   │   │   └── prompts.py          # LLM prompt templates
│   │   │   ├── pipeline.py             # Orchestrator: OCR → compliance → store
│   │   │   └── storage.py              # File storage service
│   │   │
│   │   └── db/
│   │       ├── session.py              # Async engine + session factory
│   │       └── init_db.py              # Create tables on startup
│   │
│   └── tests/
│       ├── conftest.py                 # Fixtures: test client, mock services
│       ├── test_compliance_rules.py    # Regex rule unit tests
│       ├── test_pipeline.py            # Pipeline with mocks
│       └── test_api.py                 # Endpoint integration tests
│
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx                     # Router: /, /batch, /history, /results/:id
        ├── api/
        │   ├── client.ts              # Axios instance
        │   └── analysis.ts            # uploadSingle, uploadBatch, getAnalysis, getHistory
        ├── components/
        │   ├── layout/                # Header, Layout
        │   ├── upload/                # DropZone, FilePreview, UploadButton, ApplicationDetailsForm
        │   ├── results/               # ComplianceCard, ComplianceSummary, ResultDetail
        │   ├── batch/                 # BatchProgress, BatchResultsList
        │   ├── history/               # HistoryTable
        │   └── common/                # LoadingSpinner, StatusBadge, ErrorMessage
        ├── pages/
        │   ├── UploadPage.tsx         # Single label: upload → form → process → results
        │   ├── BatchUploadPage.tsx    # Batch: multi-file + CSV → process → results
        │   ├── HistoryPage.tsx        # Past analyses table
        │   └── ResultPage.tsx         # Single result detail view
        ├── hooks/
        │   ├── useAnalysis.ts         # Upload + poll for single results
        │   └── useBatchProgress.ts    # SSE subscription for batch
        └── types/
            └── analysis.ts            # TypeScript interfaces
```

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analysis/single` | Upload + analyze one label with optional application details (returns analysis_id, client polls) |
| `GET` | `/api/analysis/{id}` | Get analysis result (poll until status=completed) |
| `GET` | `/api/analysis/` | History with pagination + filters |
| `POST` | `/api/batch/upload` | Upload multiple labels with optional CSV of application details (returns batch_id) |
| `GET` | `/api/batch/{id}` | Get batch details + all results |
| `GET` | `/api/batch/{id}/stream` | SSE stream for real-time batch progress |

---

## Data Models

**Label** — stores uploaded image metadata
- `id` (UUID), `original_filename`, `stored_filepath`, `file_size_bytes`, `mime_type`, `batch_id` (nullable FK), `created_at`

**AnalysisResult** — stores OCR + compliance results
- `id` (UUID), `label_id` (FK), `status` (pending/processing_ocr/processing_compliance/completed/failed)
- OCR: `extracted_text`, `ocr_confidence`, `ocr_duration_ms`
- Compliance: `compliance_findings` (JSON), `overall_verdict` (pass/fail/warnings), `compliance_duration_ms`
- Application matching: `application_details` (JSON, nullable) — stores the COLA application details submitted for comparison
- Metadata: `detected_beverage_type`, `detected_brand_name`, `error_message`, `total_duration_ms`

**BatchJob** — tracks batch processing
- `id` (UUID), `status`, `total_labels`, `completed_labels`, `failed_labels`, `created_at`

---

## Compliance Engine Design

**Hybrid approach:** deterministic regex checks + LLM analysis, merged together.

### Regex rules (instant, < 1ms) — cover the 3 most objective checks:
1. **Government Warning** — regex for "GOVERNMENT WARNING:" header (must be caps) + 8 key phrases from the warning text. Handles OCR errors with fuzzy matching (pass if header + 6/8 phrases found).
2. **Alcohol Content** — patterns for "XX% Alc./Vol.", "XX% ABV", "XX Proof"
3. **Net Contents** — patterns for "750 mL", "12 FL OZ", "1 Liter", etc.

### LLM analysis (2-3 sec) — covers nuanced checks:
4. **Brand Name** — is one identifiable?
5. **Class/Type** — e.g., "Kentucky Straight Bourbon Whiskey"
6. **Name & Address** — producer/bottler/importer
7. **Country of Origin** — required for imports, "not applicable" for domestic
8. **Gov Warning Format** — is "GOVERNMENT WARNING:" in all caps?
9. **Gov Warning Complete** — both required clauses present?

**Merge strategy:** Regex findings take precedence for rules they cover. LLM findings supplement with additional rules. This gives speed + nuance.

### Application Details Matching (when provided)
When an agent submits application details alongside a label image, the LLM also compares each provided field against the OCR text:
- **BRAND_MATCH** — Does the label brand match the application's brand_name?
- **CLASS_TYPE_MATCH** — Does the label class/type match the application's class_type?
- **ALCOHOL_MATCH** — Does the label alcohol content match the application's alcohol_content?
- **NET_CONTENTS_MATCH** — Does the label net contents match the application's net_contents?
- **NAME_ADDRESS_MATCH** — Does the label name/address match the application's bottler_name_address?
- **ORIGIN_MATCH** — Does the label country of origin match the application's country_of_origin?

Each matching finding has severity `pass` (match) or `fail` (mismatch) with a message showing expected vs. found values.

**LLM output format:** Structured JSON with `response_format={"type": "json_object"}`. Each finding has: `rule_id`, `rule_name`, `severity` (pass/warning/fail/info), `message`, `extracted_value`, `regulation_reference`.

---

## Frontend Design

**4 pages** (per Dave: "I don't need seventeen tabs and a dashboard" — batch is separate to keep single upload simple):

### Page 1: Upload Page (`/`) — single label workflow
Single-page state machine:
1. **Empty state** → large drag-and-drop zone + "Choose File(s)" button
2. **File selected** → thumbnail preview + application details form (required) + "Analyze Label" button
3. **Processing** → spinner with status text
4. **Results** → compliance cards with pass/fail/warning badges, matching results (if details provided) + "Upload Another" button

### Page 2: Batch Upload Page (`/batch`) — batch workflow
1. **Upload** → two zones: multi-file images + CSV of application details (required)
2. **Preview** → table of matched filenames → details
3. **Processing** → progress bar
4. **Results** → list of results with verdict badges

### Page 3: History Page (`/history`)
- Paginated table of past analyses
- Filter by verdict, beverage type
- Click row → detail view

### Page 4: Result Detail Page (`/results/:id`)
- Full findings list, extracted text panel, label image thumbnail

**UX principles** (from stakeholder interviews):
- Large click targets, big text, high contrast colors
- Green/red/yellow color coding for pass/fail/warning
- No jargon — "Government Warning: Found" not "GOV_WARNING_PRESENT: PASS"
- Immediate visual feedback at every step

---

## Implementation Sequence

### Phase 1: Backend Foundation
1. Initialize `/backend` with FastAPI, config, health endpoint
2. Create SQLAlchemy models + async DB session
3. Create Pydantic schemas
4. Create OCR/LLM service protocols + mock implementations
5. Build compliance regex rules
6. Build analysis pipeline with mocks
7. Create all API routers
8. **Verify:** `curl POST /api/analysis/single` returns mock results

### Phase 2: Frontend Core
1. Scaffold React app with Vite + TypeScript
2. Install Tailwind CSS, react-router, axios, react-dropzone
3. Build Layout, DropZone, UploadButton components
4. Build ComplianceCard, ComplianceSummary, ResultDetail components
5. Build UploadPage state machine with useAnalysis hook
6. **Verify:** Full upload → mock results flow works end-to-end

### Phase 3: Real AI Integration
1. Implement AzureVisionOCRService
2. Implement AzureOpenAIService (or AnthropicLLMService)
3. Write and tune LLM compliance prompt
4. Test with real/generated label images, iterate on accuracy
5. **Verify:** Real labels analyzed in < 5 seconds

### Phase 4: Batch + History
1. Batch upload endpoint + sequential processing pipeline
2. SSE streaming for batch progress
3. BatchProgress + BatchResultsList components
4. HistoryPage with pagination
5. **Verify:** Upload 5+ labels, see progress, view history

### Phase 5: Deploy + Polish
1. Docker Compose for local dev
2. Dockerfiles for backend (Python) + frontend (Nginx)
3. Deploy to Azure Container Apps
4. Error handling, loading states, edge cases
5. Write README with setup/run instructions + approach documentation
6. **Verify:** Deployed URL works, evaluators can test it

---

## Deployment

### Local Development
- `docker-compose.yml` with `backend` (FastAPI + uvicorn) and `frontend` (Vite dev server) services
- `.env` file for Azure API keys

### Production (Azure Container Apps)
- **Backend container:** Python 3.12-slim, uvicorn, port 8000, internal ingress
- **Frontend container:** Multi-stage build (Node build → Nginx serve), port 80, external ingress
- Nginx proxies `/api/*` to backend container
- Environment variables for Azure Vision + Azure OpenAI keys

---

## Testing Strategy

**Priority order** (most important first):
1. **Compliance rules unit tests** — regex patterns against known label text (pass/fail cases)
2. **Pipeline integration tests** — mock OCR + mock LLM → verify findings merge correctly
3. **API endpoint tests** — upload flow, history pagination, batch creation
4. **Frontend manual testing** — upload flow, batch progress, history navigation

---

## Deliverables Checklist (from takehome.md lines 96-102)

- [ ] Source code in GitHub repository
- [ ] README with setup and run instructions
- [ ] Brief documentation of approach, tools used, assumptions made
- [ ] Deployed application URL (Azure Container Apps)

## Evaluation Criteria Mapping (takehome.md lines 106-112)

| Criteria | How We Address It |
|---|---|
| Correctness and completeness | All 7 mandatory elements checked, government warning with exact text validation |
| Code quality and organization | Clean service layer architecture, Protocol pattern, clear separation of concerns |
| Appropriate technical choices | Azure Vision for label OCR, LLM for nuanced analysis, SQLite for MVP simplicity |
| User experience and error handling | 3-page UI, large targets, clear pass/fail badges, loading states, error messages |
| Attention to requirements | 5-sec target, batch uploads, simple UI, standalone tool — all traced to stakeholder quotes |
| Creative problem-solving | Hybrid regex+LLM compliance engine, service abstraction for provider swapping |
