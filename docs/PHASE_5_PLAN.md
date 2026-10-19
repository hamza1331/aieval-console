# Implementation Plan: Phase 5 (v0.2 Milestone) — Fixture Import & Replay, Contract Diffing, Advanced Filtering & Multi-Domain Presets

**Phase:** Phase 5 (Roadmap Milestone v0.2)  
**Target Release:** v0.2.0  
**Stack:** FastAPI Monolith + React 18 / TypeScript / Tailwind + SQLite / SQLAlchemy 2.0 + aieval-py  
**References:** Aieval Console SRS v0.1 (Sec 3.2, 4.1, 7 FR-16, 18 Roadmap v0.2), `FIXTURE_SPEC.md`

---

## 1. Executive Summary & Objectives

With the core v0.1 workflow fully delivered (Phase 1 library integration, Phase 2 database persistence, Phase 3 frontend dashboard & human reviews, and Phase 4 self-hosting & CI/CD), Phase 5 focuses on the **v0.2 roadmap commitments**: turning Aieval Console into a powerful regression prevention workbench.

### Primary Objectives:
1. **Fixture Import & Interactive Replay (FR-16, SRS Sec 18 v0.2):**
   - Provide `POST /api/v1/fixtures/import` to ingest an external golden test fixture conforming to `FIXTURE_SPEC.md`.
   - Provide `POST /api/v1/fixtures/replay` to execute the imported fixture immediately against `aieval-py`.
   - Compute **Parity & Regression Status**: compare actual evaluation results against the fixture's `expected` block (e.g. *Clean Pass*, *Expected Failure*, or *Regression Divergence*).
   - In the frontend UI: Add drag-and-drop fixture import and visual replay inspection.
2. **Contract Visual Diffing & Version Comparison (SRS Sec 18 v0.2):**
   - Backend endpoint `GET /api/v1/contracts/{id}/diff?from_version={v1}&to_version={v2}` computing structural check additions, deletions, and property modifications.
   - Frontend UI: Visual version comparison tab in Contract Detail view showing side-by-side differences with syntax highlighting and diff badges.
3. **Advanced Filtering, Date Range Filtering & Report Exporting:**
   - Extend `GET /api/v1/runs` with date range filters (`from_date`, `to_date`), latency filters (`min_duration_ms`, `max_duration_ms`), and failure code taxonomy filters (`failure_code`).
   - Add `GET /api/v1/runs/export` returning filtered runs as a downloadable CSV or JSON report summary.
   - Frontend: Date range selector, failure code filter dropdown, and one-click report export button.
4. **Multi-Domain Demonstration Suite (SRS Sec 3.2 & Appendix A):**
   - Package ready-to-use contracts, presets, and seeders for all three official SRS domains:
     1. **Support-Ticket Classification:** Category, priority, urgency score, summary length.
     2. **Recruitment Candidate Screening:** Candidate metadata, skills required fields, recommendation enum (`advance`, `hold`, `reject`), rating numeric range.
     3. **Invoice Data Extraction:** Invoice ID regex, currency enum (`USD`, `EUR`, `GBP`), total amount numeric range, date validation.
   - Commit golden fixtures for each domain in `fixtures/v1/` for CI conformance testing.
5. **Batch Evaluation Endpoint (Foundational for high-throughput testing):**
   - `POST /api/v1/evaluations/batch`: Ingests an array of output payloads (up to 50 items) for bulk validation against a contract version in a single HTTP request.

---

## 2. Architectural Blueprint & Data Flow

### 2.1 Fixture Import & Replay Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend / External CI                     │
│               Uploads fixture.json (FIXTURE_SPEC.md)            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ POST /api/v1/fixtures/replay
┌───────────────────────────────▼─────────────────────────────────┐
│                    FastAPI FixtureService                       │
│  1. Validate fixture structure with FixtureValidator            │
│  2. Map checks specs to aieval-py check instances               │
│  3. Execute evaluation via aieval-py engine                     │
│  4. Compare actual failures vs. expected failures:              │
│     - MATCH: Exact match with expected behavior                 │
│     - REGRESSION: New failure or unexpected passing             │
│  5. Persist run with source="imported_fixture"                  │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Returns ReplayDiagnostic
┌───────────────────────────────▼─────────────────────────────────┐
│                     Interactive UI Feedback                     │
│     Pill: "Regression Detected" OR "Passed (Expected)"          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Implementation Breakdown

### Part 1: Fixture Import & Replay Engine (FR-16)

#### A. Backend Schemas & Service
* **File:** `backend/app/schemas/fixture.py`
  * Add `FixtureReplayRequest`:
    ```python
    class FixtureReplayRequest(BaseModel):
        fixture: dict[str, Any]
        persist_run: bool = True
        contract_id: str | None = None
    ```
  * Add `FixtureReplayResponse`:
    ```python
    class FixtureReplayResponse(BaseModel):
        run_id: str | None
        status: str  # "passed" | "failed"
        expected_status: str  # "passed" | "failed"
        parity_status: str  # "match" | "regression" | "divergence"
        differences: list[str]
        actual_result: EvaluationResponse
        duration_ms: float
    ```
* **File:** `backend/app/services/fixture_service.py`
  * Implement `replay_fixture(fixture_dict: dict[str, Any], persist: bool)`:
    * Uses `AievalAdapter` to instantiate checks.
    * Invokes `aieval.runner.evaluate`.
    * Computes failure parity: compares actual failure codes and paths against `fixture["expected"]["failures"]`.
    * If `persist_run=True`, saves an `EvaluationRun` in database with metadata tag `{"source": "imported_fixture"}`.
* **File:** `backend/app/api/routes/fixtures.py`
  * Add `POST /api/v1/fixtures/replay`.
  * Add `POST /api/v1/fixtures/import` (creates contract and version from fixture checks if desired).

#### B. Frontend UI
* **Components:**
  * Add `FixtureImportModal.tsx`:
    * Tab 1: File Upload (drag-and-drop `.json` file).
    * Tab 2: Raw JSON Paste area with format validation preview.
    * Replay Action: One-click "Execute Replay".
  * In `RunHistoryPage.tsx` and `WorkbenchPage.tsx`: Add "Import & Replay Fixture" button.
  * In `RunDetailPage.tsx`: Show parity badge if the run originated from an imported fixture.

---

### Part 2: Contract Visual Diffing & Version Comparison

#### A. Backend Schemas & Service
* **File:** `backend/app/schemas/contract.py`
  * Add `ContractDiffResponse`:
    ```python
    class CheckDiffItem(BaseModel):
        type: str
        change_type: str  # "added" | "removed" | "modified" | "unchanged"
        old_spec: dict[str, Any] | None = None
        new_spec: dict[str, Any] | None = None
        details: list[str] = Field(default_factory=list)

    class ContractDiffResponse(BaseModel):
        contract_id: str
        from_version: int
        to_version: int
        added_count: int
        removed_count: int
        modified_count: int
        checks: list[CheckDiffItem]
    ```
* **File:** `backend/app/services/contract_service.py`
  * Implement `diff_versions(contract_id: str, v1: int, v2: int) -> ContractDiffResponse`:
    * Matches checks by check type and target `field`.
    * Identifies added checks, deleted checks, and modified configurations (e.g. allowed enums changed, range changed).
* **File:** `backend/app/api/routes/contracts.py`
  * Add `GET /api/v1/contracts/{id}/diff`.

#### B. Frontend UI
* **File:** `frontend/src/pages/ContractDetailPage.tsx`
  * Add "Version Comparison" mode/modal.
  * Select two versions to compare (e.g. v1 vs. v2).
  * Render visual diff cards:
    * Green badge for Added checks.
    * Red badge for Removed checks.
    * Amber badge for Modified checks with property-level diff highlights.

---

### Part 3: Advanced Filtering, Date Ranges & Report Export

#### A. Backend Extensions
* **File:** `backend/app/repositories/run_repo.py`
  * Add filter parameters to `list_runs`:
    * `from_date: datetime | None = None`
    * `to_date: datetime | None = None`
    * `failure_code: str | None = None`
    * `min_duration_ms: float | None = None`
* **File:** `backend/app/api/routes/runs.py`
  * Expose query parameters in `GET /api/v1/runs`.
  * Add `GET /api/v1/runs/export`:
    * Query parameter `format`: `"csv"` or `"json"`.
    * Streams filtered run summaries as a downloadable file with proper `Content-Disposition`.

#### B. Frontend Extensions
* **File:** `frontend/src/pages/RunHistoryPage.tsx`
  * Add date range selector (From Date, To Date).
  * Add failure code dropdown (e.g. `REQUIRED_FIELD_MISSING`, `ENUM_MISMATCH`, `RANGE_ERROR`).
  * Add "Export CSV Report" button.

---

### Part 4: Multi-Domain Demonstration Suite (SRS Sec 3.2)

#### A. Pre-Packaged Domain Contracts
1. **Support Ticket Classification (Appendix A)**:
   * Target fields: `category`, `priority`, `urgency_score`, `summary`.
2. **Recruitment Screening Demo (Sec 3.2)**:
   * Target fields: `candidate_name`, `years_experience`, `skills` (required), `recommendation` (`advance`, `hold`, `reject`), `score` (0–100 range).
3. **Invoice Data Extraction (Sec 3.2)**:
   * Target fields: `invoice_number` (pattern `^INV-[0-9]{5}$`), `currency` (`USD`, `EUR`, `GBP`), `total_amount` (min 0.01), `invoice_date`.

#### B. Seeder & Static Fixture Repository
* Update `backend/app/db/seed.py` to create contracts and realistic runs for all 3 domains.
* Commit standardized golden fixtures in `aieval-console/fixtures/v1/`:
  * `fixtures/v1/support_ticket_valid.json`
  * `fixtures/v1/support_ticket_invalid.json`
  * `fixtures/v1/recruitment_screening_valid.json`
  * `fixtures/v1/recruitment_screening_invalid.json`
  * `fixtures/v1/invoice_extraction_valid.json`
  * `fixtures/v1/invoice_extraction_invalid.json`
* Add one-click preset selector in `frontend/src/pages/WorkbenchPage.tsx` covering all 3 domains.

---

### Part 5: Batch Evaluation Endpoint

#### A. Backend Schemas & Service
* **File:** `backend/app/schemas/evaluation.py`
  * Add `BatchEvaluationRequest`:
    ```python
    class BatchEvaluationItem(BaseModel):
        item_id: str | None = None
        input: dict[str, Any] | None = None
        output: Any

    class BatchEvaluationRequest(BaseModel):
        contract_id: str | None = None
        contract_version_id: str | None = None
        items: list[BatchEvaluationItem] = Field(..., max_length=50)
    ```
  * Add `BatchEvaluationResponse`:
    ```python
    class BatchEvaluationResponse(BaseModel):
        total_items: int
        passed_count: int
        failed_count: int
        pass_rate: float
        total_duration_ms: float
        results: list[EvaluationResponse]
    ```
* **File:** `backend/app/api/routes/evaluations.py`
  * Add `POST /api/v1/evaluations/batch`.

---

## 4. Execution Order & Verification Steps

1. **Step 1: Backend Domain Models & Schemas**:
   * Implement batch evaluation schemas and routes.
   * Implement fixture replay schemas and endpoints.
   * Implement contract diff schemas and calculation service.
   * Implement advanced query filters and CSV/JSON export in `runs.py`.
2. **Step 2: Seeders & Packaged Conformance Fixtures**:
   * Update `app/db/seed.py` with the 3 SRS domains.
   * Add golden fixtures in `fixtures/v1/`.
3. **Step 3: Backend Unit & Integration Tests**:
   * Add `test_batch_evaluations.py`.
   * Add `test_fixture_replay.py`.
   * Add `test_contract_diff.py`.
   * Add `test_runs_advanced_filters.py`.
   * Verify all tests pass with 0 ruff and 0 mypy issues.
4. **Step 4: Frontend UI Enhancements**:
   * Update `client.ts` with new API methods.
   * Add `FixtureImportModal.tsx` and integrate into Workbench and Run History.
   * Add Version Diff Viewer to `ContractDetailPage.tsx`.
   * Add Date & Failure Code filters and CSV Export to `RunHistoryPage.tsx`.
   * Add domain preset switcher to `WorkbenchPage.tsx`.
   * Verify `npm run build` succeeds cleanly.
5. **Step 5: Release Verification & Git Commit**:
   * Verify git author identity is `Hamza Ali <hamxa1331@gmail.com>`.
   * Commit Phase 5 changes cleanly.

---

## 5. Acceptance Criteria & Definition of Done for Phase 5

- [x] A developer can upload or paste an external fixture JSON and receive an instant parity report showing whether model behavior matched expected outcomes or suffered a regression.
- [x] Contract version history includes a visual diff showing exactly what checks or rules changed between versions.
- [x] Evaluation runs can be filtered by date range and specific failure code taxonomy, and exported as CSV or JSON summaries.
- [x] All three official SRS demo domains (Support Tickets, Recruitment Screening, Invoice Extraction) are seeded and testable via one-click presets.
- [x] Batch evaluation endpoint processes up to 50 items and returns aggregate statistics.
- [x] 100% of tests pass, 0 linting errors, 0 type errors, clean production bundle build.

