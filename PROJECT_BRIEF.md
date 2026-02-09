# Project Brief

## What I Heard

Four stakeholders, four different concerns:

- **Sarah (Deputy Director):** 150K labels/year, 47 agents. Half their day is spent on matching — verifying the number on the form is the same as the number on the label. The last AI pilot took 30–40 seconds per label — agents went back to doing it by eye. **5 seconds or nobody uses it.** The interface needs to be something her 73-year-old mother could figure out — "clean, obvious, no hunting for buttons." Importers dump 200–300 applications at once during peak season; batch upload is a must.
- **Dave (Senior Agent, 28 years):** Skeptical — he's watched modernization projects come and go. The nuance matters: "STONE'S THROW" vs "Stone's Throw" is technically a mismatch but obviously the same brand. Not against new tools, but "don't make my life harder in the process."
- **Jenny (Junior Agent, 8 months):** Goes through a printed checklist for every label — brand name, ABV, warning statement — all by eye. The warning check is tricky: word-for-word, all caps, bold, and people try to get creative (smaller font, title case, burying it in tiny text). Also deals with poorly-shot label images — bad angles, glare, low lighting.
- **Marcus (IT Admin):** On Azure after a 2019 migration. Needs a standalone "second screen" proof-of-concept — no COLA integration for the prototype. FedRAMP and security can wait. Network blocks outbound traffic to many domains, but fine for prototype testing.

These shaped every major decision.

## Architecture: Why Regex-First, LLM-Second

Sarah's 5-second budget is the single hardest constraint. A naive approach — send every label to an LLM for full analysis — takes 3-5 seconds just for the LLM call, plus OCR time. That blows the budget on every label.

The solution: **run fast deterministic checks first, and only call the LLM when those checks can't give a confident answer.**

The pipeline:

1. **Azure Vision OCR** (1–2s) — extracts text and line-level bounding polygons from the label image
2. **OpenCV bold check** (<100ms) — measures whether "GOVERNMENT WARNING:" is in bold type using stroke-width analysis on the actual image pixels (see below)
3. **9 regex compliance rules** (<1ms) — pattern-matches against the OCR text for each mandatory label element
4. **LLM** (2–3s, **only if regex fails**) — re-checks only the specific rules that regex couldn't confirm
5. **Application matching** (<1ms) — compares OCR text against the agent-entered COLA application data

**Best case (all regex pass):** ~2 seconds total, zero LLM calls. **Worst case:** ~4–5 seconds, one focused LLM call. The LLM is never called more than once per label.

## What Each Check Actually Does

Every check runs against the raw OCR text. When a check fails, it goes to the LLM for a second opinion. Here's the logic:

**Government Warning — Presence:** Searches for "GOVERNMENT WARNING:" with flexible spacing (OCR sometimes inserts extra spaces). Case-insensitive. If found anywhere in the text → PASS.

**Government Warning — ALL CAPS:** Runs the same search twice: once case-sensitive, once case-insensitive. If the case-sensitive match hits → the header is confirmed ALL CAPS → PASS. If only the case-insensitive match hits → the text exists but isn't capitalized → WARNING.

**Government Warning — Completeness:** The full warning has two clauses (pregnancy risk, impairment risk). Rather than matching the entire paragraph verbatim — which OCR frequently garbles — the system checks for 4 key phrases per clause (e.g., "SURGEON GENERAL", "DURING PREGNANCY", "IMPAIRS YOUR ABILITY", "OPERATE MACHINERY"). **Threshold: 2 of 4 phrases per clause.** This tolerates OCR mangling 1–2 phrases while still confirming the warning is substantively there. If either clause falls below threshold → WARNING, and the LLM double-checks.

**Government Warning — Bold (OpenCV):** Jenny flagged this as tricky — people try to get creative with the warning format. 27 CFR 16.21 requires the header in bold type. Instead of asking the LLM (which would add ~3s and an API call), the system uses computer vision: it crops the "GOVERNMENT WARNING:" line and a nearby body text line from the original image using OCR bounding polygons, skeletonizes each crop to single-pixel-wide centerlines, measures the median stroke width via distance transform, and compares the ratio. **If the header's strokes are >= 1.25x thicker than body text → BOLD.** The 1.25 threshold was tuned empirically — standard bold fonts run 1.3–1.5x thicker, so 1.25 catches most bold text without false positives from normal weight variation. Falls back to the LLM's judgment when the image is too low-resolution or the text regions can't be isolated.

**Alcohol Content:** Matches common formats: "45% Alc./Vol.", "12.5% ABV", "90 Proof". If none found → FAIL.

**Net Contents:** Matches a number followed by a volume unit: mL, FL. OZ., Liter, cl, oz, etc. If none found → FAIL.

**Brand Name:** Brand names are too varied to pattern-match — regex can't distinguish "OLD TOM DISTILLERY" from any other text. Instead, uses a text-length proxy: if the OCR extracted >= 20 characters, there's enough content to plausibly contain a brand → PASS. If the text is shorter than that, the label is effectively blank or the OCR failed → FAIL, and the LLM evaluates. This is intentionally a weak gate — its job is to detect unreadable labels, not identify brands.

**Class/Type Designation:** Searches for any of ~50 known beverage type keywords (vodka, bourbon, cabernet, IPA, hard seltzer, mead, etc.) with word-boundary matching so "porter" doesn't match inside "importer". If no recognized type → FAIL, LLM tries to identify it from context.

**Name and Address:** Looks for the standard label pattern: a production verb ("Distilled", "Bottled", "Imported", "Produced", etc.) followed by "by" or "for", followed by a name and city/state. Catches "Bottled by Smith Distillery, Louisville, KY" and similar. If no match → FAIL.

**Country of Origin:** Looks for "Product of", "Imported from", "Made in", "Produced in", or "Producto de" followed by a country name. When absent, severity is **INFO** (not FAIL) — domestic products don't require it.

## How the LLM Fallback Works

When regex rules fail, the system doesn't send the entire label for a general review. It collects the specific rule IDs that failed and builds a **focused prompt**: "The regex scan couldn't confirm these items — please check only these." The LLM returns structured JSON findings that **replace** the failed regex results in the final report. Rules that passed regex keep their original result and never touch the LLM.

## Application Details Matching

When agents enter COLA application data (brand name, class/type, alcohol content, net contents, bottler/address, country of origin), the system compares each field against the OCR text:

1. **Exact match first** — case-insensitive word-boundary search for the expected value verbatim
2. **Fuzzy fallback** — tokenizes both expected and OCR text into word sets, checks if >= 70% of expected words appear in the label. This accounts for OCR misreads (a garbled character here and there) while requiring most of the expected text to be present

Results show "Expected: X. Found: approximate match (4/5 words)" so the agent can see exactly what matched and what didn't.

## UX: Don't Make It Harder

Dave's bar was simple: "don't make my life harder." Sarah's was "no hunting for buttons." The app is designed around that:

**Single upload:** Drag-and-drop (or click to browse) → optional application details form → "Upload Analysis" → full-screen processing indicator with stage-by-stage status ("Extracting text...", "Checking compliance...") → results page with pass/fail/warning verdict, individual finding cards with regulation citations, the raw OCR text, and the original label image.

**Batch upload (Sarah's request):** Select multiple images + upload a CSV of application details → "Analyze All" → progress bar showing "12/50 completed" with live updates → clickable results list with per-label verdicts → click any label to see full findings.

**History page:** Table of all past analyses, filterable by verdict (pass/fail/warnings), paginated, clickable rows.

The entire interface is 4 pages. No modals, no nested panels, no advanced options. Status badges use both color and text (not color-only) for accessibility. Processing duration is shown in results so agents can see it's under 5 seconds.

## Tools Used

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), SQLite |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| OCR | Azure AI Vision 4.0 (Image Analysis API) |
| LLM | Azure OpenAI GPT-4o-mini — called only when regex rules fail |
| Bold detection | OpenCV stroke-width analysis (skeletonization + distance transform) |
| Deployment | Docker Compose (local), Azure Container Apps (production) |
| Development | Claude Code as AI pair programmer |

## Assumptions

- **Application details are manually entered.** In production, these would come from the COLA database. For the prototype, agents fill out a form (or upload a CSV for batch).
- **SQLite for the prototype.** The SQLAlchemy async ORM means switching to PostgreSQL requires only a connection string change.
- **Azure Vision over open-source OCR.** Product labels with artistic backgrounds, curved text, and low-contrast designs need a more capable OCR engine than Tesseract.
- **Batch processing is sequential.** Parallelism is a production optimization — the prototype processes one label at a time to stay simple and debuggable.
- **The 2/4 phrase threshold for government warning completeness** was chosen to tolerate OCR errors while still confirming both clauses are present. Too low (1/4) would pass warnings with only a fragment; too high (4/4) would fail every label where OCR garbles a single phrase.
- **The 70% word-match threshold for application matching** balances OCR tolerance against false positives. It requires the majority of expected words to appear while forgiving one or two misreads.
- **The brand name check is a text-length proxy (>= 20 chars)**, not real brand detection. It catches blank/unreadable labels; the LLM handles actual brand identification when it's triggered.

## What's Deliberately Not Included

- **Handling poorly-shot images** (Jenny's pain point — bad angles, glare, low lighting) — the prototype relies on Azure Vision's built-in image processing. A production version could add pre-processing (deskewing, contrast enhancement) before OCR.
- **COLA system integration** (Marcus's constraint) — the prototype is a standalone "second screen" tool, as specified.
- **FedRAMP / security hardening** — Marcus said to skip it for the prototype.
- **Subjective compliance checks** (marketing claims, misleading imagery) and **case-sensitivity judgment** (Dave's example: "STONE'S THROW" vs "Stone's Throw" — technically a mismatch but obviously the same brand) — these require human judgment. The tool checks objective, mechanical items and leaves the nuanced calls to the agent.
- **Parallel batch processing** — labels process sequentially. Parallelism would improve throughput for Sarah's 200–300 label peak-season batches but adds complexity.

## Known Limitations

- **Bold detection** depends on OCR returning usable bounding polygons and requires enough pixel resolution to measure stroke width. Heavily stylized fonts, very low-resolution images, or labels where the warning is split across panels may return indeterminate.
- **Regex rules are English-only.** The ~50 beverage types, the name/address pattern, and the government warning phrase matching all assume English text.
- **The brand name regex can't actually identify brand names.** It passes any label with >= 20 characters of OCR text. This is a known weakness — the LLM fallback handles it, but means the fast path can't validate brand names without the LLM.
- **Application matching uses word-set intersection, not edit distance.** It handles OCR garbling whole words well, but misses cases where OCR splits one word into two or joins two words into one.
