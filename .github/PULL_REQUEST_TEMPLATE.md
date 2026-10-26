## Description
<!-- Provide a concise explanation of the changes made and the motivation behind them. -->

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] ⚡ Performance improvement
- [ ] ♻️ Code refactoring / Cleanup
- [ ] 📝 Documentation update
- [ ] 🔒 Security fix

## Architecture & Subsystem Impact
- [ ] Backend Core / Pipeline
- [ ] Ingestion Engine (Docling / PyMuPDF)
- [ ] Vector Store / Graph Database
- [ ] Frontend UI / React Components
- [ ] Telemetry & Observability (Langfuse / RAGAS)
- [ ] Docker & Ops Infrastructure

## Verification & Testing
<!-- Detail the steps you took to verify your changes. Include test commands or screenshots. -->
- **Pytest**: `pytest tests/test_unit_core.py tests/test_pipeline.py`
- **Frontend Build**: `npm run build`
- **Manual Verification**: (Steps executed)

## Checklist
- [ ] My code adheres to the company style and architectural guidelines.
- [ ] I have performed a self-review of my own code.
- [ ] No hardcoded secrets or API keys have been committed.
- [ ] All new and existing automated tests pass locally.
- [ ] Relevant documentation has been updated.
