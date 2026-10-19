# Technical Spike Findings: Aieval Console Integration (Milestone 1.5)

> Point-in-time integration findings. Use [QUALITY_IMPROVEMENT_PLAN.md](./QUALITY_IMPROVEMENT_PLAN.md) for current implementation and release status.

**Date:** 18 October 2026  
**Document Status:** Complete  
**Milestone:** Phase 1 (Week 1) Decision Checkpoint  
**Repositories:** `aieval-py` (v0.1.1 on `feat/field-constraints-and-spec-factory`), `aieval-console`  

---

## 1. Executive Summary

The Phase 1 integration spike successfully verified that:
1. `aieval-py` can serve as the **sole source of truth** for evaluation logic, failure taxonomy, and severity routing without any check duplication inside `aieval-console`.
2. Declarative JSON contracts can be authoritatively evaluated without dynamic Python code execution (`eval`, `exec`, or dynamic class generation) by using an allowlist-based declarative check factory.
3. Field-targeted constraint checks operate accurately across structured object hierarchies and retain exact dot-delimited field paths on failures.

---

## 2. Key Technical Findings & Resolutions

### 2.1 Declarative Contract Construction (SRS Risk 1 & 2)
- **Challenge:** AI outputs in JSON need field-level validations (e.g. checking `output["category"] in ["billing", "technical"]` rather than checking `output in [...]`). Prior to Phase 1, `aieval-py` constraint checks operated solely on root outputs.
- **Resolution:** Added field targeting (`field: str | None = None`) to constraint checks (`AllowedValuesCheck`, `NumericRangeCheck`, `LengthBoundsCheck`, `RegexMatchCheck`). Implemented `_resolve_field` to support simple keys (`category`), dot notation (`user.profile.age`), and JSONPath leading syntax (`$.priority`).
- **Safety Guarantee:** Created public, typed `aieval.specs.factory.build_check_from_spec` that safely validates and constructs checks strictly from a closed allowlist of supported types (`required_fields`, `allowed_fields`, `enum`, `numeric_range`, `length_bounds`, `regex_match`, `valid_json`, `tool_call`). No user-supplied scripts or arbitrary Python classes are ever executed.

### 2.2 API Normalization & Error Taxonomy (FR-05, FR-06)
- Evaluated payloads return stable serialized dictionaries containing:
  - `status`: `"passed"` or `"failed"`
  - `summary`: total checks, passed checks, failed checks, warnings count, and execution duration.
  - `failures`: list of discrete failure items preserving standard `aieval-py` taxonomy (`ENUM_MISMATCH`, `MISSING_REQUIRED_FIELD`, `LENGTH_OUT_OF_BOUNDS`, etc.), field path, severity, and diagnostic metadata.
- Preserved complete cross-language golden fixture compatibility with `FIXTURE_SPEC.md`.

### 2.3 Operational & Security Boundaries
- **Resource Limits:** `PayloadLimitMiddleware` enforces a strict 500 KB payload ceiling, rejecting oversized bodies with HTTP 413.
- **Privacy:** `RequestLoggingMiddleware` records request ID, path, status, and duration, omitting prompts and raw LLM outputs from application log streams.
- **Stack Trace Protection:** Global exception handling intercepts uncaught exceptions and emits sanitized 500 responses referencing a tracked UUID, preventing stack trace disclosure to clients.

---

## 3. Decision for Week 2 (Persistence & Core Workflow)

1. **Persistence Architecture:** Proceed as planned with SQLAlchemy 2.0 and Alembic on SQLite.
2. **Contract Versions:** Store `definition_json` as a validated snapshot alongside SHA-256 `definition_hash`. Never mutate a version once referenced by an `EvaluationRun`.
3. **Historical Snapshots:** Store `result_json` as the exact normalized result snapshot produced at execution time, paired with `aieval_version` to protect against historical drift.
