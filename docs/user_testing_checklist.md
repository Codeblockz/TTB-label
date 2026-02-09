# LabelCheck — User Testing Checklist

Test against the running app via `docker compose up -d --build`.
Test labels are in `backend/tests/fixtures/`.

---

## 1. Upload Page — UI & Flow

### File Upload
- [ ] Drag-and-drop a label image onto the drop zone
- [ ] Click "Choose File" and select a label image
- [ ] Verify thumbnail preview appears after selecting a file
- [ ] Try uploading a non-image file — should show an error
- [ ] Try uploading a very large image (10+ MB) — should handle gracefully

### Application Details Form
- [ ] Form appears after file is selected
- [ ] All fields are present: Brand Name, Class/Type, Alcohol Content, Net Contents, Bottler Name & Address, Country of Origin
- [ ] Submit with all fields filled — should proceed
- [ ] Submit with some fields empty — should still proceed (fields are optional)

### Processing State
- [ ] Spinner / loading indicator appears after clicking "Analyze Label"
- [ ] Status text updates during processing (OCR → Compliance)
- [ ] Results appear within ~5 seconds

### Results Display
- [ ] Compliance findings show with color-coded badges (green/red/yellow)
- [ ] "Upload Another" button is visible and works

---

## 2. Riverstone Vodka — Compliance Results Correctness

**File:** `river_vodka.png`

### Compliance Checks (no form input needed)

| Check | Expected Result | Why |
|---|---|---|
| Government Warning Presence | PASS | Warning text is present on label |
| Government Warning Format | PASS | "GOVERNMENT WARNING" header is in all caps and bold |
| Government Warning Complete | PASS | Both clauses (1) pregnancy and (2) impairment are present |
| Alcohol Content | PASS | "40% ALC./VOL. (80 PROOF)" is on label |
| Net Contents | PASS | "750 mL" is on label |
| Brand Name | PASS | "RIVERSTONE" is clearly identifiable |
| Class/Type | PASS | "VODKA" is on label |
| Name & Address | PASS | "Distilled and Bottled by Riverstone Distilling Co., Austin, TX" |
| Country of Origin | INFO or PASS | Domestic product — no "Product of" statement required |

- [ ] Upload `river_vodka.png` with NO form details — verify all checks above match
- [ ] Overall verdict should be PASS (or pass with info)

### Application Matching — Correct Details

| Field | Input | Expected |
|---|---|---|
| Brand Name | `RIVERSTONE` | Match |
| Class/Type | `VODKA` | Match |
| Alcohol Content | `40% ALC./VOL. (80 PROOF)` | Match |
| Net Contents | `750 mL` | Match |
| Bottler Name & Address | `DISTILLED AND BOTTLED BY RIVERSTONE DISTILLING CO., AUSTIN, TX` | Match |

- [ ] Upload `river_vodka.png` with all fields above — all 5 show Match
- [ ] Expected column shows the value you entered for each row

### Application Matching — Deliberate Mismatches

| Field | Input | Expected |
|---|---|---|
| Brand Name | `SMIRNOFF` | Mismatch — "SMIRNOFF" is not on label |
| Alcohol Content | `50% ABV` | Mismatch — label says 40% |
| Net Contents | `1 Liter` | Mismatch — label says 750 mL |

- [ ] Upload `river_vodka.png` with wrong brand name `SMIRNOFF` — Brand Match shows FAIL
- [ ] Upload with wrong alcohol `50% ABV` — Alcohol Match shows FAIL
- [ ] Upload with wrong net contents `1 Liter` — Net Contents Match shows FAIL

---

## 3. Juniper & Co. Gin — Compliance Results Correctness

**File:** `juniper_co_gin.png`

### Compliance Checks (no form input needed)

| Check | Expected Result | Why |
|---|---|---|
| Government Warning Presence | PASS | Warning text present |
| Government Warning Format | PASS | "GOVERNMENT WARNING" in all caps and bold |
| Government Warning Complete | PASS | Both clauses present |
| Alcohol Content | PASS | "47% ALC./VOL." on label |
| Net Contents | PASS | "375 mL" on label |
| Brand Name | PASS | "JUNIPER & CO." identifiable |
| Class/Type | PASS | "DISTILLED GIN" on label |
| Name & Address | PASS | "Distilled by Juniper & Co. Distillers, Portland, OR" |
| Country of Origin | INFO or PASS | Domestic — no origin statement required |

- [ ] Upload `juniper_co_gin.png` with NO form details — verify all checks above match
- [ ] Overall verdict should be PASS

### Application Matching — Case Insensitive & Partial Input

| Field | Input | Expected | Why |
|---|---|---|---|
| Brand Name | `Juniper & Co.` | Match | Case-insensitive, exact words on label |
| Brand Name | `Gin` | Match | "GIN" is a standalone word on the label |
| Brand Name | `gin` | Match | Case-insensitive word boundary match |
| Class/Type | `Distilled Gin` | Match | Exact text on label |

- [ ] Upload with Brand Name `Juniper & Co.` — shows Match, Expected shows "Juniper & Co."
- [ ] Upload with Brand Name `Gin` — shows Match (standalone word on label)
- [ ] Upload with Brand Name `gin` (lowercase) — shows Match
- [ ] Upload with Class/Type `Distilled Gin` — shows Match

### Application Matching — Word Boundary Edge Cases

| Field | Input | Expected | Why |
|---|---|---|---|
| Brand Name | `Jun` | Mismatch | Substring of "JUNIPER", not a standalone word |
| Brand Name | `Gi` | Mismatch | Substring of "GIN", not a standalone word |
| Brand Name | `Port` | Mismatch | Substring of "PORTLAND", not standalone |

- [ ] Upload with Brand Name `Jun` — shows FAIL (substring, not a word)
- [ ] Upload with Brand Name `Gi` — shows FAIL (substring, not a word)
- [ ] Upload with Brand Name `Port` — shows FAIL (substring of PORTLAND)

---

## 4. Casa Lucero Tequila — Compliance Results Correctness

**File:** `casa_lucero_tequila.png`

### Compliance Checks (no form input needed)

| Check | Expected Result | Why |
|---|---|---|
| Government Warning Presence | PASS | Warning text present (note: has OCR typos) |
| Government Warning Format | PASS | "GOVERNMENT WARNING" in all caps and bold |
| Government Warning Complete | PASS or WARN | Typos in warning text may affect clause matching |
| Alcohol Content | PASS | "40% Alc./Vol." on label |
| Net Contents | PASS | "700 mL" on label |
| Brand Name | PASS | "CASA LUCERO" identifiable |
| Class/Type | PASS | "TEQUILA BLANCO" on label |
| Name & Address | PASS | "Imported by Lucero Spirits Imports, Miami, FL" |
| Country of Origin | PASS | "PRODUCT OF MEXICO" clearly stated |

- [ ] Upload `casa_lucero_tequila.png` with NO form details — verify results above
- [ ] Country of Origin should specifically show PASS (not just INFO) — "PRODUCT OF MEXICO" is on label

### Application Matching — Correct Details

| Field | Input | Expected |
|---|---|---|
| Brand Name | `CASA LUCERO` | Match |
| Class/Type | `TEQUILA BLANCO` | Match |
| Alcohol Content | `40% Alc./Vol.` | Match |
| Net Contents | `700 mL` | Match |
| Bottler Name & Address | `IMPORTED BY LUCERO SPIRITS IMPORTS, MIAMI, FL` | Match |
| Country of Origin | `PRODUCT OF MEXICO` | Match |

- [ ] Upload with all fields above — all 6 show Match

### Application Matching — Deliberate Mismatches

| Field | Input | Expected | Why |
|---|---|---|---|
| Brand Name | `Jose Cuervo` | Mismatch | Not on label |
| Class/Type | `Mezcal` | Mismatch | Label says "TEQUILA BLANCO" |
| Country of Origin | `Product of USA` | Mismatch | Label says Mexico |

- [ ] Upload with Brand Name `Jose Cuervo` — shows FAIL
- [ ] Upload with Class/Type `Mezcal` — shows FAIL
- [ ] Upload with Country of Origin `Product of USA` — shows FAIL

---

## 5. Batch Upload — Correctness

### Using test_labels.csv

**File:** Upload all 3 label images + `test_labels.csv`

- [ ] Preview table shows 3 rows matched to CSV data
- [ ] All 3 labels process successfully
- [ ] Riverstone Vodka result: overall PASS, all matching fields Match
- [ ] Juniper & Co. Gin result: overall PASS, all matching fields Match
- [ ] Casa Lucero Tequila result: overall PASS, all matching fields Match
- [ ] Click each result — navigates to detail view with correct findings

---

## 6. History Page (`/history`)

- [ ] After running tests above, all analyses appear in history table
- [ ] Table shows filename, verdict, beverage type, date
- [ ] Click a row — navigates to correct result detail page
- [ ] Pagination controls visible and functional (if enough results)

---

## 7. Result Detail Page (`/results/:id`)

- [ ] Full list of compliance findings displayed with correct pass/fail
- [ ] Extracted OCR text panel shows readable text from the label
- [ ] Label image thumbnail matches the uploaded image
- [ ] Application matching results show correct Expected/Found/Status for each field
- [ ] Navigate here from history — same data as from upload results

---

## 8. Government Warning Edge Cases

- [ ] Riverstone Vodka: all 3 gov warning checks (presence, format, completeness) show PASS — clean label
- [ ] Casa Lucero Tequila: presence PASS, but completeness may WARN due to OCR typos in warning text
- [ ] Bold check: Riverstone and Juniper labels have bold "GOVERNMENT WARNING" — bold check should PASS

---

## 9. Error Handling

- [ ] Kill the backend, try to upload — frontend shows a clear error message
- [ ] Upload a corrupted/non-image file — error message shown, app doesn't crash
- [ ] Navigate to `/results/nonexistent-id` — shows 404 or error state
- [ ] Refresh the page mid-analysis — handles gracefully

---

## 10. Cross-Browser / Responsive

- [ ] Test in Chrome
- [ ] Resize to tablet width (~768px) — layout still usable
- [ ] Resize to mobile width (~375px) — layout still usable

---

## 11. Performance

- [ ] Single label analysis completes in under 5 seconds
- [ ] UI remains responsive during processing (not frozen)
- [ ] Batch of 3 labels completes without timeouts
