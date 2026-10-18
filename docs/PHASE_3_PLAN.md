# Phase 3 Plan: Review Workflow, Fixture Management & React Frontend Dashboard

**Milestone:** Week 3 Delivery  
**Project:** Aieval Console  
**Target Architecture:** React + TypeScript + Vite + Tailwind CSS + FastAPI Endpoints (`/overview`, `/fixtures`)  
**References:** Aieval Console SRS v0.1 (Sections 6, 7, 8, 9, 11, 15), `aieval-py/FIXTURE_SPEC.md`  

---

## 1. Executive Summary & Phase 3 Objectives

Phase 3 delivers the user-facing developer experience of Aieval Console: an interactive single-page application built with React, Vite, and TypeScript paired with backend fixture export and overview metric endpoints.

### Key Phase 3 Deliverables
1. **Backend Endpoints for UI & Fixture Interoperability:**
   - `GET /api/v1/overview`: Aggregated statistics (total contracts, total runs, pass rate, pending reviews) and recent activity feed for the dashboard (FR-11).
   - `GET /api/v1/runs/{id}/fixture`: Export run as a standard versioned golden fixture JSON adhering to `FIXTURE_SPEC.md` (FR-10).
   - `POST /api/v1/fixtures/validate`: Safe structural validator for external fixture files without executing code (FR-16).
2. **React + TypeScript Frontend Application (`frontend/`):**
   - Clean Vite project structure with Tailwind CSS and Lucide icons.
   - Strongly typed API client (`src/api/client.ts`) reflecting all backend Pydantic models.
3. **Core Dashboard Views & Workflows:**
   - **Overview Dashboard:** Metrics cards (total contracts, runs, pass rate, unreviewed failures) and recent runs table.
   - **Contracts Management:** Interactive contract explorer, check builder/editor, version history, and soft archival.
   - **Evaluation Workbench:** Real-time test workbench allowing developers to paste input/output payloads against contracts and inspect structured failures.
   - **Run History & Failure Inspector:** Paginated run browser with contract/status/date filtering, failure inspection, and review notes workflow.
   - **Fixture Export & Validation:** Download golden fixtures with one click and validate fixtures against the specification.
4. **End-to-End Verification:**
   - Backend unit and API tests for overview and fixture endpoints.
   - Frontend production build verification (`npm run build`).
   - Cross-language execution verification: exported fixtures verified using `aieval-py` CLI (`aieval run <fixture>.json`).

---

## 2. Backend Enhancements for Phase 3

### 2.1 Overview Statistics Endpoint (`GET /api/v1/overview` - FR-11)
Provides aggregate metrics for the dashboard without requiring the frontend to query and process thousands of run records.

#### Response Schema (`OverviewResponse`):
```json
{
  "total_contracts": 5,
  "active_contracts": 4,
  "total_runs": 128,
  "passed_runs": 112,
  "failed_runs": 16,
  "pass_rate": 87.5,
  "unreviewed_failures": 6,
  "recent_runs": [
    {
      "id": "uuid",
      "contract_id": "uuid",
      "contract_name": "Support ticket classification",
      "contract_version_id": "uuid",
      "contract_version_number": 1,
      "status": "failed",
      "failed_checks": 1,
      "total_checks": 4,
      "duration_ms": 1.45,
      "review_status": "unreviewed",
      "created_at": "2026-10-18T23:50:00Z"
    }
  ]
}
```

### 2.2 Golden Fixture Export Endpoint (`GET /api/v1/runs/{id}/fixture` - FR-10)
Translates a persisted `EvaluationRun` and its referenced `ContractVersion` into a portable golden fixture JSON conforming strictly to `aieval-py/FIXTURE_SPEC.md`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "name": "fixture_run_43b337eb",
  "description": "Regression fixture exported from Aieval Console run 43b337eb (Contract: Support ticket classification v1)",
  "context": {
    "input": {
      "task": "classify_support_ticket",
      "ticket_id": "TICK-103"
    },
    "metadata": {
      "contract_name": "Support ticket classification",
      "contract_version": 1,
      "console_run_id": "43b337eb-7222-4782-b1f0-6178ee7246e7"
    }
  },
  "output": {
    "category": "technical",
    "priority": "super_urgent_now",
    "summary": "Database connectivity loss in production cluster."
  },
  "checks": [
    {
      "type": "required_fields",
      "fields": ["category", "priority", "summary"]
    },
    {
      "type": "enum",
      "field": "category",
      "allowed": ["billing", "technical", "account", "other"]
    },
    {
      "type": "enum",
      "field": "priority",
      "allowed": ["low", "normal", "high", "urgent"]
    },
    {
      "type": "max_length",
      "field": "summary",
      "max": 300
    }
  ],
  "expected": {
    "passed": false,
    "failures": [
      {
        "code": "ENUM_MISMATCH",
        "path": "priority",
        "severity": "error"
      }
    ]
  }
}
```

### 2.3 Fixture Validation Endpoint (`POST /api/v1/fixtures/validate` - FR-16)
Validates fixture payloads submitted by users:
- Verifies required attributes: `output`, `checks`.
- Validates all check specifications using `aieval.build_check_from_spec`.
- Verifies `expected` schema if present.
- Executes safely without arbitrary code execution.

---

## 3. Frontend Architecture & Directory Layout

The frontend resides in `aieval-console/frontend/` using Vite, React 18/19, TypeScript, and Tailwind CSS:

```text
frontend/
├── package.json
├── vite.config.ts                   # Proxies /api to http://127.0.0.1:8000
├── tsconfig.json
├── index.html
├── src/
│   ├── main.tsx                     # Entrypoint
│   ├── App.tsx                      # Root navigation shell & layout
│   ├── api/
│   │   ├── client.ts                # Typed fetch API client for all backend routes
│   │   └── types.ts                 # TypeScript interfaces matching backend models
│   ├── components/
│   │   ├── Navbar.tsx               # Top navigation bar with health indicator
│   │   ├── MetricCard.tsx           # Dashboard statistic card
│   │   ├── StatusBadge.tsx          # Passed (green) / Failed (red) / Reviewed (blue) badges
│   │   ├── JsonEditor.tsx           # Formatted JSON textarea with validation
│   │   ├── FailureList.tsx          # Structured failure items with path & code pills
│   │   └── Modal.tsx                # Accessible modal dialog
│   ├── pages/
│   │   ├── OverviewPage.tsx         # Dashboard summary & recent activity feed (FR-11)
│   │   ├── ContractsPage.tsx        # Contract list, create modal, status filter
│   │   ├── ContractDetailPage.tsx   # Contract metadata, versions list, new version modal
│   │   ├── WorkbenchPage.tsx        # Interactive evaluation runner (FR-04)
│   │   ├── RunHistoryPage.tsx       # Paginated runs list with filters (FR-08, FR-12)
│   │   └── RunDetailPage.tsx        # Run diagnostics, failure detail, review note & fixture export
│   └── utils/
│       ├── formatters.ts            # Date, duration, and string formatting
│       └── download.ts              # Trigger JSON file download in browser
```

---

## 4. Screen-by-Screen User Workflows

### 4.1 Overview Dashboard (`/`)
- **Key Metrics:**
  - Total Contracts (active vs archived)
  - Total Evaluation Runs
  - Evaluation Pass Rate (%)
  - Unreviewed Failures (actionable backlog counter)
- **Recent Activity Table:**
  - 10 most recent runs showing Contract Name, Version, Status Badge, Execution Duration, Review State, and Timestamp.
  - "Evaluate Output" quick-action button navigating to the workbench.

### 4.2 Contracts Screen (`/contracts` & `/contracts/:id`)
- **Contract List:**
  - Search filter by contract name.
  - Status toggle (`Active` vs `Archived`).
  - "+ New Contract" button opening a contract creation modal.
- **Contract Detail View:**
  - Header with contract name, description, status badge, and "Archive Contract" button.
  - Sequential version selector (v1, v2, v3).
  - Check specification inspector displaying active checks in a readable card format.
  - "+ New Version" button allowing developers to author updated checks.

### 4.3 Evaluation Workbench (`/workbench`)
- **Evaluation Controls:**
  - Contract selector dropdown (loads active contracts and versions).
  - Optional Input context JSON editor.
  - Output payload JSON editor (with formatting and validation).
  - "Run Evaluation" button with loading state.
- **Live Results Display:**
  - Large status indicator banner (PASSED / FAILED).
  - Execution summary: duration in ms, checks passed/failed, warnings.
  - Discrete failure breakdown cards highlighting:
    - Failure Code (e.g. `ENUM_MISMATCH`, `MISSING_REQUIRED_FIELD`)
    - Severity Pill (`error`, `warning`)
    - Target Field Path (`$.priority`, `summary`)
    - Error message and suggested repair.
  - Button: "View Recorded Run" linking directly to the persisted run record.

### 4.4 Run History & Review Inspector (`/runs` & `/runs/:id`)
- **Run Browser:**
  - Filter bar: Contract dropdown, Status filter (`All`, `Passed`, `Failed`), Date picker.
  - Pagination controls (`Previous`, `Next`, items per page).
- **Run Detail Inspector:**
  - Full audit trail: Run ID, Contract Version, Timestamp, Engine Duration, `aieval-py` version.
  - Dual-pane payload viewer: Evaluated Input vs Output with copy buttons.
  - Diagnostic failure analysis.
  - **Review Section (FR-09):**
    - Status toggle: `Unreviewed` / `Reviewed`.
    - Human annotation note textarea with "Save Review" button.
    - Persisted review updates via `PATCH /api/v1/runs/:id/review`.
  - **Export Action (FR-10):**
    - "Export Fixture" button: downloads canonical `golden_fixture_<run_id>.json`.

---

## 5. Implementation Step-by-Step Checklist

### Step 1: Backend Overview & Fixture Services
- [ ] Implement `app/services/overview_service.py` computing totals and recent runs.
- [ ] Implement `app/api/routes/overview.py` serving `GET /api/v1/overview`.
- [ ] Implement `app/services/fixture_service.py` exporting golden fixtures from runs and validating fixture JSON.
- [ ] Implement `app/api/routes/fixtures.py` serving `GET /api/v1/runs/{id}/fixture` and `POST /api/v1/fixtures/validate`.
- [ ] Register new routers in `app/api/router.py`.
- [ ] Add backend unit tests in `backend/tests/` for overview and fixture endpoints.

### Step 2: React/Vite Frontend Scaffolding
- [ ] Scaffold `frontend/` using Vite with React + TypeScript.
- [ ] Configure `vite.config.ts` with API proxy forwarding `/api` to `http://127.0.0.1:8000`.
- [ ] Install and configure Tailwind CSS and Lucide React icons.
- [ ] Build strongly typed API client `src/api/client.ts` and models in `src/api/types.ts`.

### Step 3: Shared UI Components
- [ ] `Navbar`: Logo, navigation links, and live backend connection badge.
- [ ] `MetricCard`: Numeric stats with icons and trend badges.
- [ ] `StatusBadge`: Consistent color-coded badges for pass/fail/review statuses.
- [ ] `JsonEditor`: Monospace textarea with JSON format and syntax validation.
- [ ] `FailureList`: Structured failure items displaying failure code, severity, path, and error message.

### Step 4: Screen Implementations
- [ ] `OverviewPage`: Key metric cards and recent runs table.
- [ ] `ContractsPage` & `ContractDetailPage`: Contracts listing, version selector, creation modal, and archival.
- [ ] `WorkbenchPage`: Interactive evaluation testing and real-time failure reporting.
- [ ] `RunHistoryPage` & `RunDetailPage`: Filterable run history, failure inspector, review note editor, and fixture export download.

### Step 5: Verification & Quality Assurance
- [ ] Test frontend build (`npm run build`) ensuring zero TypeScript errors.
- [ ] Verify complete user workflow in browser: Overview -> Create Contract -> Evaluate in Workbench -> Inspect Run -> Add Review -> Export Fixture.
- [ ] Verify exported fixture runs cleanly against `aieval-py` CLI (`aieval run golden_fixture_*.json`).
- [ ] Run full test suites: `pytest` on backend, `npm run build` on frontend.

---

## 6. Acceptance Criteria for Phase 3 Completion

1. **Dashboard Overview:** Displays live totals (contracts, runs, pass rate, pending reviews) and recent runs from `GET /api/v1/overview`.
2. **Contracts Management:** Users can view contracts, inspect definitions across versions, create new contracts, and archive existing ones via the UI.
3. **Evaluation Workbench:** Users can paste sample input/output, execute evaluation against chosen contracts, and view real-time normalized failure breakdowns with path indicators.
4. **Run History & Review:** Run history is browsable with contract and status filters; users can open any run, inspect failures, add human review notes, and toggle the reviewed status.
5. **Fixture Interoperability:** A developer can export any failed run as a golden fixture JSON with one click, and verify it executes identically via the `aieval-py` CLI.
6. **Clean Builds:** Backend passes all `pytest`, `ruff`, and `mypy` checks; frontend compiles cleanly with `vite build`.

