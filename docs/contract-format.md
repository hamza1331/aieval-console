# Declarative Contract Format Specification

Aieval contracts are purely declarative JSON objects defining structural constraints, invariants, and business rules for evaluating AI model outputs.

---

## 1. Top-Level Contract Schema

```json
{
  "name": "Support Ticket Generation",
  "description": "Validates structured support ticket classification and triage schema.",
  "checks": [
    {
      "type": "required_fields",
      "fields": ["ticket_id", "status", "priority", "summary"]
    }
  ]
}
```

### Fields

* `name` *(string, required)*: Descriptive human-readable title (1–200 characters).
* `description` *(string, optional)*: Explanation of the contract's validation purpose.
* `checks` *(array of objects, required)*: Non-empty list of declarative check specifications.

---

## 2. Supported Checks Catalog

All checks are executed through the core `aieval-py` engine. Arbitrary code execution is strictly prohibited.

### `required_fields`
Verifies that all specified keys are present in the output dictionary.

```json
{
  "type": "required_fields",
  "fields": ["ticket_id", "status", "priority"]
}
```

### `enum`
Asserts that a field's value belongs to a predefined list of allowed string literals.

```json
{
  "type": "enum",
  "field": "priority",
  "allowed": ["low", "medium", "high", "urgent"]
}
```

### `numeric_range`
Asserts that a numeric field satisfies minimum and/or maximum bounds (inclusive).

```json
{
  "type": "numeric_range",
  "field": "urgency_score",
  "min": 1,
  "max": 10
}
```

### `length_bounds`
Asserts that a string or array length falls within specified min/max bounds.

```json
{
  "type": "length_bounds",
  "field": "summary",
  "min": 10,
  "max": 300
}
```

### `regex_match`
Asserts that a string field conforms to a regular expression pattern.

```json
{
  "type": "regex_match",
  "field": "ticket_id",
  "pattern": "^TCK-[0-9]{4,6}$"
}
```

### `valid_json`
Validates that a string contains well-formed JSON.

```json
{
  "type": "valid_json",
  "field": "metadata_raw"
}
```

---

## 3. Field Targeting & Severity Semantics

### Field Targeting
Target specific nested or top-level keys using the `field` property. On evaluation failure, the exact target field is captured in the failure report under `path`.

### Severity Levels
Every check specification accepts an optional `severity` parameter:
* `error` *(default)*: Blocks the evaluation; causes `status="failed"`.
* `critical`: Serious blocker; causes `status="failed"`.
* `warning`: Advisory issue; recorded in `warnings` list; does not fail the run.
* `info`: Informational diagnostic notice.

---

## 4. Contract Immutability & Versioning

1. When a contract is created, it begins at **Version 1**.
2. When an evaluation run executes against a contract version, that version becomes **permanently immutable**.
3. Editing or updating a contract's checks specification creates a **new sequential version** (e.g. Version 2, Version 3).
4. Each version calculates a deterministic SHA-256 hash of its normalized definition JSON for cryptographic auditability.
