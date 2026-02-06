# LabelCheck — Project Instructions

## Project Overview

AI-powered alcohol label verification tool for TTB compliance agents. See `prd.md` for full requirements and architecture. See `takehome.md` for original stakeholder interviews and deliverables.

## Tech Stack

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy (async) + SQLite
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **AI Services:** Azure Vision (OCR), Azure OpenAI / Anthropic Claude (LLM)
- **Deployment:** Docker Compose (local), Azure Container Apps (production)

## Coding Principles

Follow these strictly, in order of priority:

### KISS (Keep It Simple, Stupid)
- Write the simplest code that solves the problem. If a junior dev can't read it in 30 seconds, simplify it.
- No clever tricks, no premature abstractions, no "just in case" complexity.
- Prefer flat over nested. Prefer explicit over implicit.
- 3 similar lines of code > a premature abstraction.

### DRY (Don't Repeat Yourself)
- Extract shared logic only when it's duplicated in 3+ places and the duplication is truly identical.
- Don't force DRY when the repetition is coincidental — similar-looking code with different intent should stay separate.
- Shared constants, config values, and type definitions should have a single source of truth.

### YAGNI (You Aren't Gonna Need It)
- Do not build features, abstractions, or flexibility that isn't required right now.
- No feature flags, no plugin systems, no "future-proofing" layers unless the PRD explicitly calls for it.
- The Protocol pattern for OCR/LLM services IS justified (PRD requires provider swapping). Everything else should be concrete.
- Delete dead code immediately. No commented-out code. No `TODO: maybe later`.

## Code Standards

### Python (Backend)
- Use type hints on all function signatures.
- Use Pydantic models for all API boundaries (request/response).
- Use `async`/`await` consistently — no mixing sync and async IO.
- Imports: stdlib → third-party → local, separated by blank lines.
- Use `snake_case` for functions/variables, `PascalCase` for classes.
- Keep functions under 30 lines. If longer, break into well-named helpers.
- Handle errors at the appropriate level — don't swallow exceptions, don't over-catch.

### TypeScript (Frontend)
- Strict mode enabled. No `any` types — use proper interfaces from `types/`.
- Functional components only. Use hooks for state/effects.
- Props interfaces defined inline or co-located with the component.
- Use `camelCase` for variables/functions, `PascalCase` for components/types.
- Keep components under 100 lines. Extract sub-components when they have clear responsibilities.

### Both
- No magic numbers or strings — use named constants.
- Meaningful variable names. `label` not `l`. `analysisResult` not `ar`.
- One responsibility per file. One concept per function.

## Python Environment

Always use the project virtual environment for all Python work:

```bash
# Activate before running anything Python
source /home/ryan/FAFO/TTB_label/.venv/bin/activate

# Install backend dependencies into the venv
pip install -r backend/requirements.txt

# Run tests from within the venv
cd backend && pytest
```

- **Never** install packages globally or use system Python.
- **Never** run `pytest`, `uvicorn`, or any backend command without activating the venv first.
- If the venv is missing packages, install them into the venv — don't work around it.

## Testing Philosophy: Real Tests, Not Mocks

Tests must prove the system actually works, not just prove that mocks return what you told them to.

### Rules
- **No mock-only tests.** Every test must exercise real code paths — real regex matching, real database writes, real HTTP requests through the FastAPI test client, real file I/O.
- **Mocks are allowed ONLY for external paid APIs** (Azure Vision, Azure OpenAI, Anthropic). These are the only things we can't call for free in CI. Everything else must be real.
- **Use real test images.** Tests that verify OCR or label analysis must use actual label images stored in `backend/tests/fixtures/`. If a test needs a label image and none exists, **stop and ask the user to provide one** rather than generating fake data or skipping the test.
- **Use a real test database.** Tests should use a real SQLite database (in-memory or temp file), not a mocked session. Verify actual rows are written and read back.
- **Use the FastAPI TestClient** for API tests. Send real HTTP requests, verify real response bodies, check real status codes.
- **Compliance rule tests must use realistic label text** — copy-paste from real labels or the takehome.md examples, not made-up strings that happen to pass.

### What to do when test materials are missing
If you need a test fixture (label image, sample text, etc.) that doesn't exist yet:
1. **Ask the user** — "I need a photo of an alcohol label to write this test. Can you provide one or should I find a sample?"
2. **Do not** generate a placeholder and pretend the test is valid.
3. **Do not** skip writing the test. Flag it and wait.

### Test structure
```
backend/tests/
├── fixtures/              # Real label images, sample OCR text files
│   ├── sample_label.jpg   # Actual label photo (user-provided)
│   └── sample_ocr.txt     # Real OCR output text
├── conftest.py            # Fixtures: real test DB, real TestClient, mock ONLY for external APIs
├── test_compliance_rules.py   # Regex rules against realistic label text
├── test_pipeline.py           # Full pipeline with real DB, mock only external APIs
└── test_api.py                # Real HTTP requests via TestClient
```

## Validation Requirements

Every piece of work must be validated before considering it done:

### Backend Validation
- **Activate the venv first:** `source .venv/bin/activate`
- After writing any endpoint: test it with `curl` or `httpie` and confirm the response shape matches the Pydantic schema.
- After writing compliance rules: run `pytest backend/tests/test_compliance_rules.py` and confirm pass/fail cases work.
- After modifying models: verify the DB tables are created correctly by running the app and checking.
- After any change: run `pytest` from the `backend/` directory and confirm all tests pass.
- Tests must pass against real data, not just mocks.

### Frontend Validation
- After writing components: run `npm run build` in `frontend/` to catch TypeScript errors.
- After adding pages/routes: manually verify navigation works in the browser.
- After connecting to the API: verify the full upload → results flow end-to-end.

### Integration Validation
- After connecting frontend to backend: test the full flow with `docker-compose up`.
- Verify the 5-second performance budget with real (or mock) AI services.

### Pre-Commit Validation
- Run `pytest` (backend) and `npm run build` (frontend) before every commit.
- No commit should break the build.

## File Organization

Follow the project structure in `prd.md` exactly. When in doubt:
- Models go in `backend/app/models/`
- Schemas go in `backend/app/schemas/`
- Business logic goes in `backend/app/services/`
- Route handlers go in `backend/app/routers/`
- React components go in `frontend/src/components/{category}/`
- Pages go in `frontend/src/pages/`
- Shared types go in `frontend/src/types/`

## Git Conventions

- Commit messages: imperative mood, concise (`Add compliance regex rules`, not `Added some rules`)
- Commit logical units of work, not file-by-file
- Don't commit `.env`, `__pycache__`, `node_modules`, `.db` files, or uploaded label images
