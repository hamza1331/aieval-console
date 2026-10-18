# Aieval Console Architecture Specification

## 1. Core Architectural Principles

1. **Library as Source of Truth (FR-05):** `aieval-py` is the sole source of truth for check execution, failure codes, and severity semantics. The console adapter maps declarative contracts into public `aieval` check specifications without reimplementing evaluation logic.
2. **Modular Monolith:** A single FastAPI application serves API endpoints, business logic, persistence repositories, and static frontend assets in production.
3. **Contract Immutability (FR-03):** Contract versions are sequentially numbered, SHA-256 hashed, and immutable once evaluated against. Any changes to a contract generate a new sequential version.
4. **Snapshot Guarantee:** Historical evaluation runs store the serialized library result at evaluation time. Future upgrades of `aieval-py` do not retroactively modify stored historical outcomes.
5. **Local-First & Zero Secrets (NFR-09):** The application requires no cloud provider credentials, external databases, or network access to operate.

---

## 2. Entity-Relationship Data Model

```mermaid
erDiagram
    Contract ||--o{ ContractVersion : "has sequential versions"
    ContractVersion ||--o{ EvaluationRun : "evaluated against"
    EvaluationRun ||--o| Review : "human triage note"

    Contract {
        string id PK "UUIDv4"
        string name "Contract title"
        string description "Validation purpose"
        string status "active | archived"
        datetime created_at
        datetime updated_at
    }

    ContractVersion {
        string id PK "UUIDv4"
        string contract_id FK "References Contract.id"
        int version "Sequential version number (1, 2, ...)"
        json definition_json "Full checks specification JSON"
        string definition_hash "SHA-256 digest of normalized definition"
        datetime created_at
    }

    EvaluationRun {
        string id PK "UUIDv4"
        string contract_version_id FK "References ContractVersion.id"
        string status "passed | failed"
        json input_json "Optional prompt/context"
        json output_json "AI output payload evaluated"
        json result_json "Normalized library result snapshot"
        float duration_ms "Execution latency in ms"
        string aieval_version "Recorded aieval-py version"
        datetime created_at
    }

    Review {
        string id PK "UUIDv4"
        string run_id FK "Unique, references EvaluationRun.id"
        string status "unreviewed | reviewed"
        string note "Human annotation note"
        datetime created_at
        datetime updated_at
    }
```

---

## 3. Layered Component Architecture

```
                    ┌─────────────────────────┐
                    │  React Single Page App  │
                    └───────────┬─────────────┘
                                │ JSON / HTTP
                    ┌───────────▼─────────────┐
                    │   FastAPI API Router    │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │    Application Layer    │
                    │   (Services & Domain)   │
                    └──────┬───────────┬──────┘
                           │           │
         ┌─────────────────▼──┐     ┌──▼───────────────────┐
         │  Repository Layer  │     │    AievalAdapter     │
         │  (SQLAlchemy 2.0)  │     │(Calls aieval-py lib) │
         └─────────┬──────────┘     └──┬───────────────────┘
                   │                   │
         ┌─────────▼──────────┐     ┌──▼───────────────────┐
         │  SQLite Database   │     │  aieval-py Core Lib  │
         └────────────────────┘     └──────────────────────┘
```

### Layer Responsibilities

* **API Routers (`app/api/routes/`):** Request validation, status code translation, and HTTP response serialization using Pydantic v2 schemas.
* **Services (`app/services/`):** Business logic, contract version sequencing, SHA-256 hashing, fixture synthesis, and overview aggregations.
* **Adapter (`app/adapters/aieval_adapter.py`):** Translates declarative check dictionaries into executable `aieval-py` check instances using the public `build_check_from_spec` factory.
* **Repositories (`app/repositories/`):** Database queries using SQLAlchemy 2.0 type-safe `select()` statements with pagination and filter criteria.
* **Database Session (`app/db/session.py`):** Managed SQLite connections with `PRAGMA foreign_keys = ON` and connection pooling.
