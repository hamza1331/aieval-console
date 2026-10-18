# Phase 1 Plan: Library Enhancements & FastAPI Integration Spike

**Milestone:** Week 1 Delivery  
**Repositories Involved:**  
1. `aieval-py` (Core Library Enhancements)  
2. `aieval-console` (FastAPI Skeleton & Adapter Integration)  

---

## 1. Overview & Objectives

The primary objective of Phase 1 is to prove the end-to-end integration between declarative validation contracts and the `aieval-py` runtime engine without duplicating check implementations.

### Phase 1 Success Criteria
1. **Zero Duplication:** All validation checks are executed strictly by `aieval-py`.
2. **Declarative Spec Factory:** `aieval-py` provides a public, typed factory `build_check_from_spec` that safely instantiates check objects from JSON dictionaries.
3. **Field-Targeted Constraints:** Constraint checks in `aieval-py` support an optional `field` parameter (with dot-path resolution) so structured object attributes can be checked individually.
4. **FastAPI Baseline:** `aieval-console/backend` initializes cleanly, implements configuration and middleware (payload caps, logging, error handling), and serves `/api/v1/health` and `/api/v1/evaluations`.
5. **Appendix A Support Ticket Validation:** Both passing and failing outputs for the synthetic Support Ticket classifier contract evaluate with stable, normalized failure reports.
6. **Milestone 1.5 Architecture Spike Note:** Gaps and design decisions documented in `docs/SPIKE_FINDINGS.md`.

---

## 2. Part A: `aieval-py` Library Enhancements

### 2.1 Field-Targeted Constraint Checks
Currently, constraint checks in `src/aieval/checks/constraints.py` evaluate `output` directly. When evaluating structured JSON payloads, checks must inspect specific fields (e.g. `field="category"` or dot-path `field="customer.priority"`).

#### 2.1.1 Helper Function: `_resolve_field`
Location: `src/aieval/checks/base.py` (or shared helper module):
```python
def _resolve_field(output: Any, field_path: str | None) -> tuple[Any, bool]:
    """Resolves a field from an output dictionary or object.
    
    Supports:
    - None or empty string: returns (output, True)
    - Simple keys: 'category' -> output['category']
    - Leading JSONPath syntax: '$.category' -> output['category']
    - Dot-notation: 'customer.tier' -> output['customer']['tier']
    
    Returns:
        (resolved_value, exists_flag)
    """
    if field_path is None or field_path == "":
        return output, True
    
    # Strip leading '$.' if present
    normalized_path = field_path[2:] if field_path.startswith("$.") else field_path
    parts = normalized_path.split(".")
    
    current = output
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None, False
    return current, True
```

#### 2.1.2 Update Constraint Checks
Modify checks in `src/aieval/checks/constraints.py` to accept `field: str | None = None`:
1. **`AllowedValuesCheck` (`allowed_values`)**:
   - Signature: `def __init__(self, allowed: Collection[Any], *, field: str | None = None, severity: Severity = Severity.ERROR, name: str | None = None)`
   - Execution: Resolves `target_val, exists = _resolve_field(output, self.field)`. If field does not exist, returns failure with `code=FailureCode.MISSING_REQUIRED_FIELD, path=self.field`. If value not in `self.allowed`, returns failure with `code=FailureCode.ENUM_MISMATCH, path=self.field`.
2. **`NumericRangeCheck` (`numeric_range`)**:
   - Signature: Accepts optional `field: str | None = None`.
   - Execution: Resolves target field. If value violates range or cannot be converted to float, returns failure with `code=FailureCode.VALUE_CONSTRAINT_VIOLATION, path=self.field`.
3. **`LengthBoundsCheck` (`length_bounds`)**:
   - Signature: Accepts optional `field: str | None = None`.
   - Execution: Resolves target field. If length violates bounds, returns failure with `code=FailureCode.LENGTH_OUT_OF_BOUNDS, path=self.field`.
4. **`RegexMatchCheck` (`regex_match`)**:
   - Signature: Accepts optional `field: str | None = None`.
   - Execution: Resolves target field. If regex fails to match, returns failure with `code=FailureCode.REGEX_MISMATCH, path=self.field`.

---

### 2.2 Public Declarative Check Factory
Formalize specification parsing into a public module: `src/aieval/specs/factory.py` and export in `src/aieval/__init__.py`.

#### 2.2.1 Check Spec Schema & Aliases
```python
def build_check_from_spec(spec: dict[str, Any]) -> Check:
    """Builds an aieval Check from a declarative dictionary specification.
    
    Supports canonical types and common aliases specified in the SRS:
    - 'required_fields' | 'required': fields, severity
    - 'allowed_fields' | 'whitelist_fields': fields, severity
    - 'enum' | 'allowed_values': allowed (or values), field, severity
    - 'max_length' | 'max_len': max (or max_len), field, severity
    - 'min_length' | 'min_len': min (or min_len), field, severity
    - 'length_bounds' | 'length': min_len, max_len, field, severity
    - 'numeric_range' | 'range': min_val, max_val, field, severity
    - 'regex_match' | 'regex' | 'pattern': pattern, field, severity
    - 'valid_json' | 'json': severity
    - 'tool_call' | 'tool': name, required_args, allow_unexpected_args, severity
    """
```

#### 2.2.2 Refactor CLI Runner to Use Public Factory
Update `src/aieval/cli/main.py`:
- Remove internal `_build_check_from_spec`.
- Import and use `from aieval.specs.factory import build_check_from_spec`.
- Verifies that both the CLI and application rely on the identical factory logic.

---

### 2.3 Tests in `aieval-py`
Create `tests/unit/test_specs_factory.py`:
1. **Appendix A Support Ticket Contract Verification:**
   - Valid ticket passes (`passed=True`, 0 failures).
   - Missing `summary` returns `MISSING_REQUIRED_FIELD` at `path="summary"`.
   - Invalid `priority="urgent_now"` returns `ENUM_MISMATCH` at `path="priority"`.
   - Long `summary` (>300 chars) returns `LENGTH_OUT_OF_BOUNDS` at `path="summary"`.
2. **All Aliases & Field Resolution Verification:**
   - Tests `enum`, `max_length`, `min_length`, `range`, `pattern`, `whitelist_fields`.
   - Tests nested dot notation (e.g. `field="metadata.user.role"`).
3. **Regression Tests:**
   - Run `pytest` across the entire `aieval-py` suite to ensure zero regressions in golden parity tests or CLI functionality.

---

## 3. Part B: `aieval-console` Backend Setup

### 3.1 Environment & Package Configuration (`backend/pyproject.toml`)
Initialize backend with `uv`:
```toml
[project]
name = "aieval-console-backend"
version = "0.1.0"
description = "FastAPI backend for Aieval Console"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.28.0",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.2.0",
    "aieval-py",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

Configure `aieval-py` as an editable dependency (`uv pip install -e ../aieval-py`).

---

### 3.2 Core Modules & Configuration

1. **`app/core/config.py`**:
   - `Settings` (inheriting `pydantic_settings.BaseSettings`):
     - `PROJECT_NAME: str = "Aieval Console"`
     - `VERSION: str = "0.1.0"`
     - `API_V1_STR: str = "/api/v1"`
     - `HOST: str = "127.0.0.1"` (Local-first default)
     - `PORT: int = 8000`
     - `CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]`
     - `MAX_PAYLOAD_BYTES: int = 524288` (500 KB limit)
     - `ENABLE_OPENAPI: bool = True` (Can be disabled via env var)

2. **`app/core/logging.py`**:
   - Structured JSON logging.
   - Logs: `request_id`, `method`, `path`, `status_code`, `duration_ms`.
   - Omit full request/response bodies by default (NFR-08).

3. **`app/core/middleware.py`**:
   - `PayloadLimitMiddleware`: Returns `413 Request Entity Too Large` if `Content-Length > MAX_PAYLOAD_BYTES`.
   - Global exception handler: Catches unhandled exceptions, logs traceback with error ID, and returns sanitized `500` response (NFR-04).

4. **`app/main.py`**:
   - App factory with CORS, middleware, router inclusion, and lifespan startup banner.

---

### 3.3 Schemas (`app/schemas/`)

1. **`app/schemas/contract.py`**:
   - `CheckSpec`: Discriminated or validated Pydantic model for checks.
   - `ContractDefinitionSchema`: `name`, `description`, `checks: list[CheckSpec]`.
2. **`app/schemas/evaluation.py`**:
   - `EvaluationRequest`:
     ```python
     class EvaluationRequest(BaseModel):
         contract_version_id: str | None = None
         contract: ContractDefinitionSchema | None = None
         input: dict[str, Any] | None = None
         output: Any
     ```
     *(In Phase 1, supports either inline `contract` specification or `contract_version_id` resolved via an in-memory registry).*
   - `FailureSchema`: `code`, `message`, `severity`, `path`, `metadata`, `suggested_repair`.
   - `EvaluationSummarySchema`: `total_checks`, `passed_checks`, `failed_checks`, `warnings_count`, `duration_ms`.
   - `EvaluationResponse`: `run_id`, `status` ("passed" | "failed"), `duration_ms`, `summary`, `failures`, `warnings`.
3. **`app/schemas/health.py`**:
   - `HealthResponse`: `status: str`, `app_version: str`, `aieval_version: str`.

---

### 3.4 Adapter Layer (`app/adapters/aieval_adapter.py`)

```python
from typing import Any
import aieval
from aieval.domain import EvaluationContext, EvaluationResult
from app.schemas.evaluation import EvaluationResponse, FailureSchema, EvaluationSummarySchema

class AievalAdapter:
    """Translates contract check specs to aieval-py checks and normalizes execution results."""

    @staticmethod
    def evaluate(
        output: Any,
        checks_spec: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> EvaluationResponse:
        # 1. Instantiate checks via aieval.build_check_from_spec
        checks = [aieval.build_check_from_spec(spec) for spec in checks_spec]
        
        # 2. Build EvaluationContext
        context = EvaluationContext(
            input=context_data.get("input") if context_data else None,
            prompt=context_data.get("prompt") if context_data else None,
            metadata=context_data.get("metadata", {}) if context_data else {},
        ) if context_data else None

        # 3. Execute evaluation
        result: EvaluationResult = aieval.evaluate(output, checks=checks, context=context)

        # 4. Map to normalized response
        failures = [
            FailureSchema(
                code=f.code.value if hasattr(f.code, "value") else str(f.code),
                message=f.message,
                severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                path=str(f.path) if f.path else None,
                metadata=f.metadata,
                suggested_repair=f.suggested_repair,
            )
            for f in result.failures
        ]
        
        warnings = [
            FailureSchema(
                code=w.code.value if hasattr(w.code, "value") else str(w.code),
                message=w.message,
                severity=w.severity.value if hasattr(w.severity, "value") else str(w.severity),
                path=str(w.path) if w.path else None,
                metadata=w.metadata,
            )
            for w in result.warnings
        ]

        return EvaluationResponse(
            run_id=run_id or "temp-run-id",
            status="passed" if result.passed else "failed",
            duration_ms=result.summary.duration_ms,
            summary=EvaluationSummarySchema(
                total_checks=result.summary.total_checks,
                passed_checks=result.summary.passed_checks,
                failed_checks=result.summary.failed_checks,
                warnings_count=result.summary.warnings_count,
                duration_ms=result.summary.duration_ms,
            ),
            failures=failures,
            warnings=warnings,
        )
```

---

### 3.5 Routes & Endpoints

1. **`GET /api/v1/health`**:
   - Returns 200 OK with `status="ok"`, `app_version="0.1.0"`, and `aieval_version=aieval.__version__`.
2. **`POST /api/v1/evaluations`**:
   - Validates request body.
   - Evaluates payload via `AievalAdapter`.
   - Returns 200 OK with `EvaluationResponse`.
   - Rejects invalid check definitions with 422 Unprocessable Entity (field-level validation errors per FR-02).

---

### 3.6 Milestone 1.5 Architecture Spike Note (`docs/SPIKE_FINDINGS.md`)
Deliverable 1.5 document verifying:
1. Public API compatibility and serialization fidelity of `aieval-py`.
2. Declarative contract JSON maps cleanly without dynamic Python code execution.
3. Path reporting fidelity (`$.field` vs `field`).
4. Confirmation that database persistence (Week 2) can store `definition_json` and `result_json` as snapshots without schema divergence.

---

## 4. Phase 1 Verification Checklist

- [ ] `aieval-py` tests pass (`pytest tests/`) including new tests in `test_specs_factory.py`.
- [ ] `aieval-py` passes `ruff check` and `mypy src/`.
- [ ] `aieval-py` CLI (`aieval run <fixture>.json`) executes successfully with the refactored public factory.
- [ ] Backend environment initializes via `uv venv` and `uv pip install -e .`.
- [ ] `GET /api/v1/health` returns `200 OK` with valid versions.
- [ ] `POST /api/v1/evaluations` successfully processes the Appendix A Support Ticket classifier:
  - Valid output returns `status="passed"`.
  - Invalid output returns `status="failed"` with structured failure array (`ENUM_MISMATCH`, `path="priority"`).
- [ ] Automated tests in `backend/tests/` verify health, evaluation, and failure modes with 100% pass and no network calls.
- [ ] Milestone 1.5 document `docs/SPIKE_FINDINGS.md` is authored.
