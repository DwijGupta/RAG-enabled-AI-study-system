# Contributing to AI Study Buddy

Thank you for your interest in contributing to the **AI Study Buddy** enterprise platform! This document outlines our engineering standards, pull request workflow, code style, and development lifecycle.

---

## 1. Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please maintain a respectful, constructive, and inclusive environment.

---

## 2. Git Workflow & Branch Strategy

We follow the standard Git Feature-Branch workflow:

1. **Fork or branch** off `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```
2. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add graph community summarization caching`
   - `fix: resolve neo4j driver thread pool shutdown leak`
   - `test: add unit tests for tutor planner remediation`
   - `docs: update deployment and architecture documentation`
   - `perf: optimize reciprocal rank fusion candidate pool`

---

## 3. Local Development Setup

### Backend (FastAPI + Python 3.10+)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Copy environment config
cp .env.example .env

# Run unit tests
pytest tests/test_unit_core.py tests/test_pipeline.py

# Start local dev server
python run_server.py
```

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run build
npm run dev
```

### Full Infrastructure (Docker Compose)
```bash
docker compose up -d
```

---

## 4. Code Standards & Quality Checks

Before submitting any Pull Request, ensure:
1. **Automated Tests**: All backend tests pass (`pytest tests/`).
2. **Frontend Build**: The frontend compiles cleanly with zero errors (`npm run build`).
3. **No Secrets**: Verify that no API keys or local `.env` files are tracked by Git.
4. **Documentation**: Update relevant docstrings and the `README.md` for user-facing changes.

---

## 5. Submitting a Pull Request (PR)

- Push your branch to GitHub.
- Open a Pull Request targeting the `main` branch.
- Complete the provided [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md).
- Ensure CI checks pass. A maintainer will review your code.
