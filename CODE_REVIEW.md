# LabelCheck Code Review

**Date:** 2026-02-10
**Scope:** Full codebase (~3,200 lines production code)
**Reviewers:** 3 parallel agents (backend, frontend, cross-cutting)

---

## Executive Summary

LabelCheck is in solid shape for a take-home/prototype. The architecture is clean, the compliance rule engine is well-designed, and the code generally follows the project's own CLAUDE.md standards. TypeScript strict mode is enabled and enforced. The backend pipeline is well-structured with clear separation of concerns.

**However, there are 3 bugs that will affect users, 4 security gaps worth documenting, and a handful of quality improvements that would matter for production.**

**Verification status:**
- Backend tests: 162 passed, 5 failed (pre-existing fixture mismatches in `test_generated_labels.py`)
- Frontend build: Passes cleanly (TypeScript strict mode, zero errors)

---

## Findings

### Critical

| ID | Category | File | Finding |
|----|----------|------|---------|
| B-001 | Bug | `frontend/src/pages/BatchUploadPage.tsx:48-50` | **fetchResults() called on every render.** The call `fetchResults()` at line 48-50 is in the component body (not in a useEffect), so it fires on every render when `progress.isComplete && results.length === 0 && batchId`. Since `fetchResults` calls `setResults`, this creates an infinite re-render loop until the API responds, then settles. |
| B-002 | Bug | `frontend/src/components/upload/FilePreview.tsx:14` | **Memory leak: `URL.createObjectURL()` never revoked.** A blob URL is created via `useMemo` but never released with `URL.revokeObjectURL()`. Each file preview leaks a blob URL. Needs a `useEffect` cleanup. |
| B-003 | Bug | `frontend/src/pages/UploadPage.tsx:37` | **`window.location.reload()` used for reset.** The "Upload Another" button does a full page reload instead of resetting React state. This destroys all client-side state, causes a flash, and is a poor UX pattern. Should reset hook state instead (requires exposing a `reset` function from `useAnalysis`). |

### High

| ID | Category | File | Finding |
|----|----------|------|---------|
| S-001 | Security | `backend/app/services/storage.py:18` | **No file size limit on uploads.** `await file.read()` reads the entire file into memory with no size cap. A malicious user could upload a multi-GB file and OOM the server. The nginx config has `client_max_body_size 10m` but this only applies in Docker — running the backend directly has no protection. |
| S-002 | Security | `backend/app/main.py:34-40` | **CORS allows all origins with credentials.** `allow_origins=["*"]` combined with `allow_credentials=True` is a security misconfiguration. Per the CORS spec, `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is actually blocked by browsers, so the credentials flag is misleading/dead code. For a government compliance tool, origins should be restricted. |
| S-003 | Security | `backend/app/routers/batch.py:89-105` | **No SSRF protection on batch processing.** While the current batch endpoint accepts file uploads (not URLs), the CSV parsing has no validation beyond stripping whitespace. If batch processing ever adds URL-based fetching, there's no SSRF protection. Currently low risk but worth noting. |
| S-004 | Security | `backend/requirements.txt` | **All dependencies use `>=` (floor) pinning.** No upper bounds or `==` pinning means `pip install` could pull breaking or vulnerable future versions. For reproducible builds, use `==` pinning or a lock file. |
| B-004 | Bug | `backend/tests/test_generated_labels.py` | **5 test failures in generated label tests.** `pillow_lowercase_warning.png` and `openai_proof_format.png` have mismatched expected warnings/verdicts. The `GOV_WARNING_FORMAT` rule fires a WARNING for lowercase "Government Warning:" text, but the fixture CSV expects no warnings. Either the fixture expectations or the regex sensitivity needs adjustment. |
| F-001 | Bug | `frontend/src/hooks/useAnalysis.ts` | **No polling timeout.** The polling interval runs indefinitely until the analysis completes or fails. If the backend hangs or crashes mid-analysis, the frontend polls forever. Should add a max timeout (e.g., 5 minutes) after which it stops and shows an error. |
| F-002 | Bug | `frontend/src/hooks/useAnalysis.ts:33-48` | **No cleanup on unmount for polling interval.** The hook doesn't return a cleanup function to clear the interval if the component unmounts during processing. If the user navigates away during polling, the interval keeps firing and calling `setAnalysis` on an unmounted component. |

### Medium

| ID | Category | File | Finding |
|----|----------|------|---------|
| Q-001 | Quality | `backend/app/services/compliance/bold_check.py:57` | **Potential mismatch in run-length pairing.** `_median_run_length` pairs starts and ends arrays by index, but if the binary image has edge effects (row starting with foreground), the arrays could be different lengths, producing incorrect run lengths. The zero-padding helps but doesn't guarantee equal-length arrays in all edge cases. |
| Q-002 | Quality | `backend/app/routers/analysis.py:24-31` | **`_parse_json` silently swallows all exceptions.** The broad `except Exception` means malformed JSON in the DB is silently dropped. This could mask data corruption. Should at least log a warning. |
| Q-003 | Quality | `backend/app/services/compliance/engine.py:125` | **LLM findings beyond requested rules are appended unfiltered.** Line 125 `merged_findings.extend(llm_by_rule.values())` adds any extra LLM findings that weren't in the original regex set. This means the LLM could inject arbitrary rule IDs into the report. Should filter to only expected rule IDs. |
| Q-004 | Quality | `backend/app/services/pipeline.py:57` | **Blocking `cv2.imread()` and `check_bold_opencv()` in async context.** The bold check does synchronous file I/O and CPU-bound OpenCV operations directly in an async function. Should use `asyncio.to_thread()` to avoid blocking the event loop. The comment says "<100ms" but this isn't guaranteed for large images. |
| Q-005 | Quality | `backend/app/routers/batch.py:113-114` | **Silently skips files with invalid MIME types in batch.** Files with unsupported MIME types are silently dropped (`continue`). The user gets no feedback about which files were rejected. The returned `total_labels` reflects only accepted files, but the user doesn't know which ones were skipped. |
| Q-006 | Quality | `backend/app/services/compliance/rules.py:189-205` | **`check_brand_name` is a text-length check, not a brand name check.** The function just checks if the label has >= 20 characters of text. It doesn't actually identify or validate a brand name. The function name and rule name are misleading. |
| Q-007 | Quality | `frontend/src/pages/BatchUploadPage.tsx` | **Component is 176 lines.** Exceeds the 100-line guideline in CLAUDE.md. The upload form, progress view, and results view could be extracted into sub-components. |
| Q-008 | Quality | `frontend/src/components/results/ResultDetail.tsx` | **Component file is 133 lines** (contains 3 components: `MatchBadge`, `parseExpectedValue`, `MatchingResults`, `ResultDetail`). While the main component is reasonable, the file exceeds 100 lines. The helper components could be extracted. |
| S-005 | Security | Codebase-wide | **No authentication or authorization.** Any network-accessible client can upload files, trigger analysis (consuming Azure API quota), view all historical results, and delete analyses. For a government compliance tool, this is a significant gap. Acceptable for a prototype but must be addressed before any deployment. |
| S-006 | Security | Codebase-wide | **No rate limiting.** No request rate limiting exists anywhere. Combined with no auth, this means anyone can flood the API, exhaust Azure API quotas, and fill disk with uploads. |
| G-001 | Gap | `frontend/` | **Zero frontend tests.** No test files exist in the frontend. The project's testing philosophy emphasizes "real tests, not mocks" but has no frontend test coverage at all. |
| G-002 | Gap | `backend/app/routers/analysis.py:138-151` | **`get_analysis_image` serves files from arbitrary stored paths.** The endpoint reads `stored_filepath` from the DB and serves it via `FileResponse`. If the DB is ever compromised, this could serve arbitrary files. Low risk since the path is set internally, but there's no validation that the path is within the uploads directory. |

### Low

| ID | Category | File | Finding |
|----|----------|------|---------|
| Q-009 | Quality | `backend/Dockerfile` | **Not a multi-stage build.** The frontend Dockerfile uses multi-stage (build + nginx), but the backend Dockerfile is single-stage. Not critical since it uses `python:3.12-slim`, but test dependencies (pytest) and test fixtures are copied into the production image unnecessarily. |
| Q-010 | Quality | `backend/Dockerfile:9` | **Test fixtures copied into production image.** `COPY tests/fixtures/ ./tests/fixtures/` includes test images in the production Docker image. This is needed for the sample labels feature but bloats the image. |
| Q-011 | Quality | `backend/app/routers/batch.py:172` | **Cross-module import of private function.** `from app.routers.analysis import _to_response` imports a private function (prefixed with `_`) from another module. Should be refactored to a shared utility. |
| Q-012 | Quality | `frontend/src/hooks/useBatchProgress.ts:40-42` | **SSE error handler silently closes.** The `onerror` callback just closes the EventSource with no user feedback. If the SSE connection drops, the user sees a frozen progress bar with no indication of failure. |
| Q-013 | Quality | `backend/app/dependencies.py:36-40` | **New service instances created per pipeline call.** `get_pipeline()` creates new `AzureVisionOCRService`, `AzureOpenAILLMService`, and `ComplianceEngine` instances on every call. These could be singletons since they hold no request-specific state. Minor perf impact. |
| Q-014 | Quality | `backend/app/main.py:19` | **Unused import aliases in lifespan.** `from app.models import analysis as _a, batch as _b, label as _l` uses underscore aliases to suppress unused-import warnings. The `# noqa: F401` is already there, so the aliases are redundant. |
| Q-015 | Quality | `frontend/nginx.conf` | **No security headers.** The nginx config doesn't set `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, or other security headers. Low priority for a prototype but notable. |

---

## CLAUDE.md Compliance Summary

| Standard | Status | Notes |
|----------|--------|-------|
| KISS | Pass | Architecture is straightforward, no over-engineering |
| DRY | Pass | Minimal duplication; `_to_response` cross-import (Q-011) is the only notable instance |
| YAGNI | Pass | No dead code, no speculative features |
| Python type hints | Pass | All functions have type annotations |
| Python function length | Pass | All functions under 30 lines |
| Python import ordering | Pass | stdlib -> third-party -> local consistently |
| TypeScript strict mode | Pass | `strict: true` with `noUncheckedIndexedAccess` |
| No `any` types | Pass | No `any` found in TypeScript source |
| Components under 100 lines | **Fail** | `BatchUploadPage.tsx` (176 lines), `ResultDetail.tsx` (133 lines) |
| No magic numbers | Pass | Constants are named (`POLL_INTERVAL_MS`, `MAX_CONCURRENT_ANALYSES`, etc.) |
| Meaningful variable names | Pass | Clear naming throughout |

---

## Prioritized Action Items

### Must Fix (before demo/deployment)
1. **B-001**: Fix `fetchResults()` infinite render loop in `BatchUploadPage.tsx` — wrap in `useEffect`
2. **B-002**: Fix blob URL memory leak in `FilePreview.tsx` — add cleanup `useEffect`
3. **F-002**: Add cleanup for polling interval in `useAnalysis.ts` — return cleanup from hook
4. **B-004**: Fix 5 failing tests in `test_generated_labels.py` — update fixture expectations or adjust regex

### Should Fix (for production readiness)
5. **S-001**: Add file size limit to `save_upload()` (e.g., 10MB to match nginx)
6. **B-003**: Replace `window.location.reload()` with proper state reset
7. **F-001**: Add polling timeout to `useAnalysis.ts`
8. **Q-004**: Wrap `check_bold_opencv()` in `asyncio.to_thread()`
9. **Q-005**: Return feedback about skipped files in batch upload response
10. **S-002**: Fix CORS configuration (remove `allow_credentials=True` or restrict origins)

### Nice to Have (quality improvements)
11. **Q-002**: Add logging to `_parse_json` error path
12. **Q-003**: Filter LLM findings to only requested rule IDs
13. **Q-007/Q-008**: Extract sub-components to meet 100-line guideline
14. **Q-011**: Move `_to_response` to a shared utility
15. **Q-012**: Add error feedback for SSE connection failures
16. **S-004**: Pin dependency versions with `==` or add a lock file
17. **G-001**: Add frontend tests (at minimum: component render tests, hook tests)
