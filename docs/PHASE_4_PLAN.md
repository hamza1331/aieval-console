# Implementation Plan: Phase 4 — Self-Hosting, Operational Hardening, CI/CD & Release Packaging

**Phase:** Phase 4 (Week 4 Milestone)  
**Target Release:** v0.1.0  
**Stack:** FastAPI Monolith + React 18 / Vite / Tailwind + Docker Compose + GitHub Actions CI + SQLite  
**References:** Aieval Console SRS v0.1, `aieval-py` Fixture Spec v1.0, `COMPREHENSIVE_IMPLEMENTATION_PLAN.md`

---

## 1. Executive Summary & Objectives

Phase 4 completes the transition of `aieval-console` from a local development environment into a production-ready, self-hosted developer tool. It unifies the frontend and backend into a single cohesive distribution, packages it into a containerized deployment with volume persistence, automates quality verification via GitHub Actions CI, produces comprehensive system documentation, and validates the end-to-end golden fixture execution loop with `aieval-py`.

### Primary Objectives:
1. **Unified Monolith Distribution (SRS Sec 9.1):** Configure FastAPI to serve the compiled React SPA static assets (`frontend/dist`) at `/` with HTML5 SPA fallback routing, while preserving `/api/v1/*` REST routes and `/health`.
2. **Containerization & Self-Hosting (SRS Sec 13.1, Sec 14):**
   - Provide a multi-stage `Dockerfile` (Node 20 builder + Python 3.12/3.14 slim runner).
   - Provide `docker-compose.yml` (and `docker/compose.yaml`) mounting a persistent SQLite volume (`./data:/app/data`) and local port binding (`127.0.0.1:8000:8000`).
   - Built-in container healthcheck against `/health`.
3. **Automated Database Bootstrapping:** Ensure the application automatically runs Alembic migrations on startup if the database file is fresh, or provides a seamless entrypoint script that executes migrations before starting `uvicorn`.
4. **CI/CD Quality Gate (`.github/workflows/ci.yml`):**
   - Backend pipeline: Python dependency installation, `ruff check`, `mypy`, and `pytest` suite.
   - Frontend pipeline: Node.js dependency installation, TypeScript type check (`tsc`), and `vite build`.
   - Docker build validation.
5. **Complete Documentation Suite (SRS Sec 15):**
   - Root `README.md`: Quickstart, architecture overview, screenshots/workflows, configuration, and API reference.
   - `docs/architecture.md`: In-depth monolith architecture, database schema, and component interactions.
   - `docs/contract-format.md`: Complete guide to authoring declarative validation contracts with supported checks allowlist.
   - `docs/self-hosting.md`: Production Docker Compose deployment, volume backups, reverse proxy setup (Nginx / Caddy), and environment variables.
   - `docs/contributing.md`: Developer guide, local workflow, testing guidelines, and commit standards.
6. **Cross-Repo End-to-End Interoperability Test:**
   - Seed database, run evaluation via console, export golden fixture to JSON, and execute `aieval run <fixture.json>` with `aieval-py` CLI to prove seamless cross-repo interoperability.

---

## 2. Architecture & Delivery Blueprint

### 2.1 Unified Production Container Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Docker Container (app:v0.1.0)                    │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │                 Uvicorn ASGI Monolith Server                 │     │
│   │                                                              │     │
│   │   /health              --> Health & Diagnostics Handler      │     │
│   │   /api/v1/*            --> FastAPI REST Routers              │     │
│   │                            - /contracts                      │     │
│   │                            - /evaluations                    │     │
│   │                            - /runs                           │     │
│   │                            - /reviews                        │     │
│   │                            - /fixtures                       │     │
│   │                            - /overview                       │     │
│   │   /*                   --> StaticFiles (frontend/dist/)      │     │
│   │                            - Fallback to index.html (SPA)    │     │
│   └──────────────────────┬───────────────────────────────────────┘     │
│                          │                                             │
│       ┌──────────────────▼───────────────────┐                         │
│       │        SQLAlchemy 2.0 Engine         │                         │
│       └──────────────────┬───────────────────┘                         │
│                          │                                             │
└──────────────────────────┼─────────────────────────────────────────────┘
                           │
                 Volume: ./data:/app/data
                           │
       ┌───────────────────▼───────────────────┐
       │         SQLite Database               │
       │       /app/data/aieval.db             │
       └───────────────────────────────────────┘
```

---

## 3. Detailed Component Implementation Breakdown

### Part 1: SPA Static Asset Serving in FastAPI
* **File:** `backend/app/main.py`
* **Behavior:**
  * When `frontend/dist` directory exists (in production or container), mount `StaticFiles(directory=static_dir, html=True)` at `/`.
  * Add a 404 catch-all route for non-API paths that returns `index.html` to support HTML5 browser pushState history navigation.
  * Ensure API routes (`/api/v1/*`), health checks (`/health`), and OpenAPI docs (`/docs`, `/openapi.json`) take precedence over the static files handler.
* **Testing:** Integration test asserting `GET /` returns HTML containing `<div id="root">`, while `GET /api/v1/health` continues returning JSON.

---

### Part 2: Multi-Stage Dockerfile & Docker Compose

#### A. Multi-Stage Dockerfile (`Dockerfile`)
* **Stage 1 (Frontend Builder):**
  * Base: `node:22-alpine`
  * Workdir: `/frontend`
  * Copy `frontend/package.json` and `frontend/package-lock.json`
  * Run `npm ci`
  * Copy frontend source and run `npm run build` (outputs `/frontend/dist`).
* **Stage 2 (Backend Runner):**
  * Base: `python:3.12-slim`
  * Environment variables: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `APP_DATA_DIR=/app/data`, `HOST=0.0.0.0`, `PORT=8000`.
  * Install dependencies: `pip install uv` or standard `pip install .` for backend.
  * Install `aieval-py` from adjacent wheel or local editable path if in monorepo, or install via standard wheel build.
  * Copy `/frontend/dist` from Stage 1 to `/app/frontend/dist`.
  * Create `/app/data` volume mount point.
  * Entrypoint script: runs `alembic upgrade head`, then starts `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

#### B. Docker Compose Configurations
* **Files:** `docker-compose.yml` (and `docker/compose.yaml`)
* **Service Definition:**
  ```yaml
  services:
    console:
      build:
        context: .
        dockerfile: Dockerfile
      container_name: aieval-console
      ports:
        - "127.0.0.1:8000:8000"
      volumes:
        - aieval-data:/app/data
      environment:
        - HOST=0.0.0.0
        - PORT=8000
        - DATABASE_URL=sqlite:////app/data/aieval.db
        - DATA_DIR=/app/data
      healthcheck:
        test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/health"]
        interval: 10s
        timeout: 5s
        retries: 3
        start_period: 5s
      restart: unless-stopped

  volumes:
    aieval-data:
      driver: local
  ```

---

### Part 3: Operational Hardening & Production Settings
* **File:** `backend/app/core/config.py`
* **Features:**
  * Support `DATABASE_URL` override (allowing custom SQLite path like `/app/data/aieval.db`).
  * Support `STATIC_DIR` pointing to `/app/frontend/dist` or relative path.
  * Support `AUTO_MIGRATE: bool = True` in settings: automatically executes Alembic upgrade on app startup lifecycle if database is fresh.
  * Verify payload size limits (500 KB default), CORS allow-origins list, and sanitized error responses.

---

### Part 4: GitHub Actions CI/CD Pipeline
* **File:** `.github/workflows/ci.yml`
* **Triggers:** Push to `main` and pull requests.
* **Jobs:**
  1. `backend-tests`:
     * Runs on `ubuntu-latest`, Python 3.11 & 3.12.
     * Installs backend & local `aieval-py`.
     * Runs `ruff check .`
     * Runs `mypy app`
     * Runs `pytest -v --cov=app`
  2. `frontend-build`:
     * Runs on `ubuntu-latest`, Node.js 20 & 22.
     * Installs frontend dependencies with `npm ci`.
     * Runs `npm run build` (typechecks with `tsc` and bundles with Vite).
  3. `docker-build`:
     * Validates that `docker build -t aieval-console:test .` succeeds without errors.

---

### Part 5: Comprehensive Documentation Suite

1. **Root `README.md`**:
   * Project elevator pitch & features overview.
   * Architecture overview diagram.
   * 5-Minute Quickstart (Local dev & Docker Compose).
   * Key workflows: Contracts, Workbench, Human Review, and Golden Fixture Export.
   * Environment configuration table.
   * Project roadmap status.
2. **`docs/architecture.md`**:
   * Architectural patterns (Monolith, Library as Single Source of Truth, Snapshot Guarantees).
   * Data models & database relationships (Mermaid diagram).
   * Directory structure explanation.
   * Request lifecycle walkthrough.
3. **`docs/contract-format.md`**:
   * Complete reference for declarative contract JSON schemas.
   * Supported checks catalog (`required_fields`, `enum`, `numeric_range`, `length_bounds`, `regex_match`, `valid_json`).
   * Field path resolution rules.
   * Severity levels (`info`, `warning`, `error`, `critical`).
   * Versioning semantics & immutability.
4. **`docs/self-hosting.md`**:
   * Production deployment guide with Docker Compose.
   * Reverse proxy recipes (Nginx and Caddy with SSL).
   * Database backups & maintenance (SQLite backup commands).
   * Security checklist (local-first binding, firewall rules, payload size caps).
5. **`docs/contributing.md`**:
   * Monorepo / adjacent repo setup instructions.
   * Running tests (`pytest`, `npm test`, `ruff`, `mypy`).
   * Git commit guidelines (Conventional Commits, author requirements).

---

### Part 6: Cross-Repo End-to-End Fixture Interoperability

* **Integration Verification:**
  1. Initialize SQLite database with `python -m app.db.seed`.
  2. Execute an evaluation run via `POST /api/v1/evaluations` against the Support Ticket contract with deliberate failures.
  3. Fetch golden fixture JSON from `GET /api/v1/runs/{id}/fixture`.
  4. Save fixture to `test_fixture.json`.
  5. Run `aieval run test_fixture.json` using the `aieval-py` CLI on branch `feat/field-constraints-and-spec-factory`.
  6. Verify that `aieval-py` CLI executes the fixture, verifies expected check outcomes, and exits with expected status.

---

## 4. Execution Step-by-Step Order

1. **Backend SPA Static Mounting:**
   - Update `app/main.py` and `app/core/config.py` to support serving `frontend/dist`.
   - Add test verifying static asset serving and SPA fallback.
2. **Automated DB Migration on Startup:**
   - Add programmatic Alembic runner in lifespan or startup script.
3. **Containerization & Deployment Scripts:**
   - Write `Dockerfile` and `.dockerignore`.
   - Write `docker-compose.yml` and `docker/compose.yaml`.
   - Write `scripts/start.sh` for container boot.
4. **CI/CD Configuration:**
   - Create `.github/workflows/ci.yml`.
5. **Documentation Suite:**
   - Create root `README.md`.
   - Create `docs/architecture.md`.
   - Create `docs/contract-format.md`.
   - Create `docs/self-hosting.md`.
   - Create `docs/contributing.md`.
6. **End-to-End Interoperability Test:**
   - Run seeder & export fixture.
   - Run `aieval run <fixture>` with `aieval-py` CLI.
7. **Verification & Commit:**
   - Run all backend tests, linting, frontend build, and commit Phase 4 under author `Hamza Ali <hamxa1331@gmail.com>`.

---

## 5. Definition of Done (DoD) for Phase 4

- [ ] `docker compose up` starts the entire system from scratch without external dependencies.
- [ ] Accessing `http://127.0.0.1:8000` serves the React frontend, and refreshing deep routes (`/contracts`, `/workbench`, `/runs`) correctly renders via SPA fallback.
- [ ] SQLite database file persists inside mounted volume `./data/` across container restarts.
- [ ] All 5 documentation files (`README.md`, `architecture.md`, `contract-format.md`, `self-hosting.md`, `contributing.md`) are complete and accurate.
- [ ] GitHub Actions workflow `.github/workflows/ci.yml` is defined and valid.
- [ ] Cross-repo verification succeeds: exported fixture from console runs cleanly in `aieval-py` CLI.
- [ ] 100% test pass rate in backend and 0 frontend build errors.

