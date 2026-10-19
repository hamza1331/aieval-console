# Quality Improvement & Release Readiness Plan

**Scope:** `aieval-py` and `aieval-console`  
**Purpose:** An ordered, test-first plan to address the current quality-review findings before the next public releases.  
**Status:** Implementation in progress. Library safety, console behavior, operational hardening, and the reproducible Docker workflow have implementation and local test evidence. Empty-state UI verification, Python matrix execution, artifact packaging, and final release gates remain open. No package has been published.

This plan coordinates work across the two adjacent repositories. The console depends on the Python library as its evaluation engine, so library behavior and compatibility must be settled before the console is validated against it.

## Release principle

Do not treat a passing build or test suite as release approval by itself. A release candidate must also pass the observable behavior, API integration, packaging, deployment, and documentation gates below. Fixes should be small, independently reviewable changes with regression tests added alongside them.

The library has already been published. Changes to its public behavior therefore need an explicit compatibility assessment, release notes, and an appropriate version increment; do not assume that a bug fix is non-breaking if callers may rely on the old behavior.

The behavior changes in Phase 1 are being prepared as `aieval-py` 0.2.0. The console now accepts only the compatible `>=0.2.0,<0.3.0` range. This is a source-level release decision, not authorization to publish.

## Review baseline

The initial review was performed against the current working trees on 19 October 2026. At that point:

- `aieval-py`: Ruff and mypy passed; 47 tests passed; measured coverage was 90.64%, above its 90% CI threshold.
- `aieval-console` backend: Ruff and mypy passed; 38 tests passed, with dependency deprecation warnings.
- `aieval-console` frontend: `npm run build` passed, including TypeScript compilation.
- Runtime probes still exposed important behavior not covered by those checks: unexpected tool arguments were accepted, invalid custom-check return values passed, and a terminal tool failure could become a non-blocking warning.
- The console Docker build was not exercised; inspection showed that configured build contexts and Dockerfile copy paths do not agree.

Treat these figures as a starting snapshot, not as evidence that later changes or a release candidate pass.

The baseline working-tree heads were `aieval-py` `77672e2f99caa58607c00c09c292ad15b6e3484f` on `feat/field-constraints-and-spec-factory` and `aieval-console` `eca3992d9b4bc3397cee3fb36d28396d926a39da` on `main`. Local validation uses Python 3.14.7, Node 24.21.0/npm 11.19.0, and Docker 29.8.0; these are baseline references, not release-candidate commits.

## Ordered implementation plan

### Phase 0 — Establish compatibility and regression baselines

**Repositories:** Both  
**Depends on:** Nothing

Before editing behavior:

1. Record the exact library and console commits, Python and Node versions, and installed dependency versions used for the baseline.
2. Run and retain the existing test, lint, type-check, coverage, and frontend-build results.
3. Identify public library APIs and console API response shapes that must remain compatible. Add regression tests for confirmed findings before changing implementation.
4. Agree on how breaking behavior will be released. In particular, review whether tightening invalid custom-check returns or tool-call arguments requires a breaking release for existing callers.

**Exit gate:** Each finding below has a reproduction test or a documented integration check, and the baseline is reproducible from a clean checkout.

### Phase 1 — Close library fail-open and tool-call safety gaps

**Repository:** `aieval-py`  
**Depends on:** Phase 0

1. **Enforce the tool-call argument allowlist.** Make `allow_unexpected_args=False` reject undeclared arguments. Define how allowed names are determined with and without a Pydantic schema; preserve the existing explicit `required_args` behavior. Update the contradictory fixture example in `FIXTURE_SPEC.md`.
2. **Reject invalid check results.** In both `evaluate()` and `aevaluate()`, do not interpret unsupported non-`None` custom-check return values as success. Raise the documented configuration error (or a deliberately selected, typed equivalent) and document the supported result protocol.
3. **Keep terminal failures blocking.** Ensure terminal failures cannot be moved into warnings by a severity threshold, and ensure aggregate retryability reflects all failures rather than only those left in the blocking list. Define and test the interaction between caller-selected severity and terminal safety.
4. **Document the behavior change.** Update the public API documentation and examples where needed. Include an upgrade note for users of the published package.

**Required tests:**

- Extra argument rejected when unexpected arguments are disallowed and accepted only under the documented permissive configuration.
- Schema-backed tool calls enforce the intended schema/extra-field policy.
- Invalid synchronous and asynchronous custom-check returns raise clearly; valid supported return shapes keep their existing behavior.
- Terminal unknown-tool failures remain blocking and non-retryable under every supported `fail_on` threshold.
- Existing severity routing, golden fixtures, CLI behavior, and published public API tests remain green.

**Exit gate:** The focused regression tests and full library quality suite pass. Public behavior changes and the release-versioning decision are recorded before publishing a new library version.

### Phase 2 — Make console API and frontend contracts agree

**Repository:** `aieval-console`  
**Depends on:** Phase 1 for tests that exercise the real library

1. **Correct paginated response handling.** Update frontend API types and consumers for contract and run list endpoints to use the backend's `{ items, total, limit, offset }` envelope, rather than treating the response as an array.
2. **Align pagination parameters.** Use backend-supported `limit` and `offset` consistently. Remove or translate client-side `skip` parameters; make sure total counts and next-page behavior work.
3. **Add runtime integration coverage.** Exercise the actual HTTP JSON response shape through the API client or a browser-level test. TypeScript compilation alone is insufficient because the current generic fetch helper casts response JSON without validating it.

**Required tests:**

- Contract and run lists load, filter, and render from the paginated envelope.
- Pagination uses the intended offset and total; empty lists render correctly.
- API error responses remain visible to users and are not swallowed by silent `.catch(() => {})` handlers.
- Frontend type-check, build, and relevant backend API tests pass.

**Exit gate:** A clean run of the console UI against its backend successfully loads the contracts, workbench choices, and run history from populated and empty databases.

### Phase 3 — Correct console evaluation, filtering, and fixture semantics

**Repository:** `aieval-console`  
**Depends on:** Phases 1–2

1. **Do not evaluate archived contracts for new work.** Reject new evaluations by archived `contract_id`; continue to allow access to historical runs and explicitly version-bound history as intended.
2. **Apply failure-code filters before pagination.** Put filtering in the query or otherwise ensure matching results are paginated and counted consistently. The returned `total` must describe the filtered result set.
3. **Compare fixture results at the documented level.** Compare expected and actual failures order-independently. `code` is required; optional `path` and `severity` are asserted only when supplied, explicit `path: null` means no path, and duplicate records remain significant. Make `matches_expected`, parity status, and differences agree.
4. **Validate fixture shape consistently.** Check the required fields from `FIXTURE_SPEC.md`, including `output` and `checks`; validate the optional `expected` block and each expected failure. Avoid broad exception handling that turns unexpected implementation errors into ordinary validation failures.
5. **Keep fixture replay persistence faithful.** If a replay is requested for persistence, store the result that was actually replayed. Do not silently evaluate a different version or discard fixture-defined checks.
6. **Verify library CLI behavior.** The CLI treats a fixture's `expected` block as a regression assertion: it exits successfully when the actual result matches, including expected failures; without an `expected` block it retains the evaluation-result exit code. Validate expected shape and assert the contract in the console interoperability test.

**Required tests:**

- Archived contract cannot be used for a new run; historical records remain readable.
- Failure-code filtering works across multiple pages and returns an accurate filtered total.
- Fixture replay detects code, path, and other agreed parity differences, including duplicate failures.
- Invalid expected blocks and missing fixture fields are rejected with useful client errors.
- Persisted replay matches the replay response and can be exported and executed by the library CLI.

**Exit gate:** Backend tests prove correct API behavior and the cross-repository fixture test proves the chosen fixture contract end to end.

### Phase 4 — Harden request limits and deployment failure handling

**Repository:** `aieval-console`  
**Depends on:** Phase 3

1. **Enforce request limits while receiving the body.** Retain early rejection based on `Content-Length`, but also cap bytes read so missing, false, or streamed/chunked lengths cannot bypass `MAX_PAYLOAD_BYTES`.
2. **Fail startup when migrations fail.** Remove success-shaped fallbacks around migration execution in both application lifespan and startup script. A failed migration must stop the process and surface its cause in logs.
3. **Make health/readiness meaningful.** Verify database readiness for the health/readiness endpoint used by Docker. A service with an unavailable or unmigrated database must not advertise ready.
4. **Resolve unauthenticated deployment exposure.** Before supporting deployments reachable by untrusted users, add and test an appropriate authentication/access-control boundary. Until then, clearly restrict deployment instructions and examples to trusted networks with an explicit access-control layer; do not present an open public reverse proxy as safe.
5. **Review privacy and error handling.** Ensure client responses remain sanitized, operational logs retain useful error context without logging prompts or outputs, and database/API failure modes are surfaced rather than silently ignored.

**Required tests:**

- Oversized body is rejected with and without `Content-Length`, including streamed requests.
- Migration failure causes process/startup failure and a failing readiness check.
- Ready health checks succeed only when the database is usable.
- Deployment security guidance and, if implemented, authentication tests cover protected reads and writes.

**Exit gate:** No request-size or startup-failure scenario produces an unbounded request, a false-success response, or a falsely healthy service.

### Phase 5 — Make Docker packaging reproducible and gate it in CI

**Repository:** `aieval-console`  
**Depends on:** Phase 4

1. Choose and document one Docker build context. Make the `Dockerfile` source paths and both Compose files consistent with that context and with the adjacent `aieval-py` source.
2. Build the image from a clean checkout using the documented command; do not rely on local virtual environments, `node_modules`, generated `dist`, or ignored files being present.
3. Start the image with a fresh persistent data volume. Verify migrations, health checks, static assets, API routes, and database persistence across a restart.
4. Add a Docker image build job to CI so path/context regressions fail before merge.

**Required tests:**

- Clean `docker build` and `docker compose config`.
- Fresh-volume startup, health check, SPA root/deep-route behavior, API health response, and persistence after restart.
- No committed database, local environment file, or build output is required for the image.

**Exit gate:** A clean clone can execute the documented container workflow without manually preparing hidden local state.

### Phase 6 — Align CI, supported versions, and release documentation

**Repositories:** Both  
**Depends on:** Phases 1–5

1. **Align support claims with CI.** Test the library's declared Python range (currently Python 3.10–3.14) and either test every console Python version claimed by its metadata/README or narrow those claims to the tested range.
2. **Make dependency resolution reproducible.** Define and test how the console selects the library version. Avoid an unbounded dependency that can silently change evaluation behavior; use a deliberate compatible range or published-version pin and update it through a tested change.
3. **Keep quality gates aligned with contributor guidance.** Ensure documented CI includes all checks required by the contribution guide, including frontend validation and Docker validation. Fix deprecation warnings when the relevant dependencies or test tools are upgraded; do not hide them without a reason.
4. **Reconcile the docs.** Mark old research/implementation plans as historical or update their status; remove contradictory fixture examples; align API, payload limits, authentication posture, supported Python versions, startup behavior, and Compose instructions with the implementation.
5. **Build and inspect release artifacts.** Build the library wheel and source distribution, install the built artifact into a clean environment, and smoke-test imports and the `aieval` entry point. Confirm the console image contains the intended library version and frontend bundle.

**Current release blocker:** The library tracks an empty `LICENSE` file, and the console README claims MIT while the console repository has no `LICENSE` file. The built wheel therefore contains an empty license file. Confirm the intended license and copyright holder before publishing either repository.

**Exit gate:** Documentation, package metadata, CI matrices, generated artifacts, and runtime behavior make the same support and feature claims.

### Phase 7 — Release-candidate verification and publication

**Repositories:** Both  
**Depends on:** All previous phases

1. Freeze the release-candidate commits and dependency versions; start from clean worktrees.
2. Run all checks from a clean environment, not only targeted tests:

   ```bash
   # aieval-py
   ruff check src tests
   ruff format --check src tests
   mypy src
   pytest --cov=aieval --cov-report=term-missing --cov-fail-under=90
   python -m build
   ```

   ```bash
   # aieval-console/backend
   ruff check app tests
   mypy app
   pytest
   ```

   ```bash
   # aieval-console/frontend
   npm ci
   npm run build
   ```

   Also run the clean Docker build and startup checks from Phase 5.
3. Install the built library artifact into a clean environment and run the console end-to-end against that artifact, rather than a developer's editable checkout. Verify contract creation, pass/fail evaluations, review updates, filtered run history, fixture export/replay, and restart persistence.
4. Review public API compatibility, changelog/release notes, package contents, license files, and security/deployment warnings. Publish the library first only if the console is tested against that exact released library version; publish the console image/release after its integration gate passes.
5. After publication, install each published artifact from its distribution channel into a fresh environment and repeat the public quickstart smoke test.

**Final release gate:** All required checks pass on the release commit; every issue from this plan is either closed with test evidence or explicitly accepted and documented; no untested source changes are made after validation.

## Tracking checklist

- [ ] Phase 0: Baseline and compatibility decisions recorded.
- [x] Phase 1: Library fail-open, tool-call, and terminal-failure regressions fixed and tested.
- [x] Phase 2: Frontend/backend pagination contract corrected and integration-tested.
- [x] Phase 3: Archive rules, filtering counts, and fixture parity corrected and tested.
- [x] Phase 4: Request limits, migrations, readiness, and deployment access controls hardened.
- [x] Phase 5: Clean Docker workflow verified and gated in CI.
- [ ] Phase 6: Python support claims, dependency policy, CI, and documentation aligned.
- [ ] Phase 7: Release artifacts and published-install smoke tests pass.

## Current local validation evidence

Validation was run from the working trees on Python 3.14.7 and Node 24.21.0; it is not a substitute for CI on every declared Python version.

- `aieval-py`: Ruff lint/format, mypy, 65 tests, and 90.90% coverage passed. The 0.2.0 wheel and source distribution built; the wheel installed into a clean virtual environment, and the installed CLI matched a failing golden fixture expectation successfully.
- `aieval-console` backend: dependency consistency, Ruff, mypy, and 49 tests passed. Five existing Starlette/FastAPI deprecation warnings remain visible.
- Frontend: TypeScript build and Vite production build passed.
- Docker: Compose configuration and clean image build passed. Fresh-volume migration, health/version response, SPA root/deep route, API contract create/list, browser flows against populated and empty databases, and persistence after container restart passed.
- CI workflow YAML parses and the Python matrix is configured for 3.10–3.14; GitHub Actions has not run for these changes.

Publication remains blocked on the license decision, remote CI execution, and a final clean release-candidate review. No commit, push, or package publication has been made.
