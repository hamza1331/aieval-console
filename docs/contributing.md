# Contributing to Aieval Console

Thank you for contributing to Aieval Console. Please follow these guidelines to ensure quality, security, and consistent code style.

---

## 1. Development Environment Setup

Clone both `aieval-py` and `aieval-console` side-by-side:

```bash
git clone git@github.com:hamza1331/aieval-py.git
git clone git@github.com:aieval/aieval-console.git
```

### Backend Setup
```bash
cd aieval-console/backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

---

## 2. Code Quality & Testing Standards

All pull requests must pass backend linting, type checks, unit tests, and frontend build validation.

### Backend Verification
From `backend/`:
```bash
# Linting & import formatting
ruff check app tests

# Static type analysis
mypy app

# Run full test suite
pytest -v
```

### Frontend Verification
From `frontend/`:
```bash
# Typecheck and build production bundle
npm run build
```

---

## 3. Commit & Pull Request Guidelines

1. **Commit Messages:** Follow the [Conventional Commits](https://www.conventionalcommits.org/) convention:
   * `feat(...)`: New feature or capability
   * `fix(...)`: Bug fix
   * `docs(...)`: Documentation changes
   * `test(...)`: Unit or integration tests
   * `refactor(...)`: Code refactoring without behavior change
2. **Branching:** Create feature branches (e.g., `feat/add-new-check` or `fix/run-query`).
3. **Core Integrity:** Do not duplicate check logic or validation execution in the console backend or frontend. Keep `aieval-py` as the single source of truth.
