# Open-Source Contribution & Maintainer Guide

Welcome to the F.R.I.D.A.Y. contribution guide!

This document supplements the root [CONTRIBUTING.md](../../CONTRIBUTING.md) with specific technical conventions and engineering standards for maintainers and new contributors.

---

## 1. Engineering Philosophy

F.R.I.D.A.Y. models life-support systems in extreme environments. We value:
- **Simplicity Over Overengineering**: Do not add unnecessary abstraction layers or frameworks for appearance.
- **Physics Grounding**: Do not simulate critical equipment with random number generators when thermodynamic or electrical equations can be applied.
- **Fail-Safe Defaults**: Every network call, LLM query, or database operation must have an offline, bounded-timeout fallback path.
- **Technical Honesty**: Never label simulated or prototype features as production features.

---

## 2. Pull Request Review Checklist (For Maintainers)

Maintainers must verify the following before approving any Pull Request:
- [ ] **Tests Passing**: 100% of backend tests (`python -m pytest`) pass.
- [ ] **Lint Clean**: `python -m ruff check backend/ tests/ --select E9,F63,F7,F82` passes with zero errors.
- [ ] **Frontend Built**: `npm run lint && npm run test && npm run build` completes cleanly.
- [ ] **No Secrets**: No hardcoded API keys, private keys, or passwords.
- [ ] **Offline Autonomy Intact**: The platform starts cleanly and executes the 1 Hz loop without Internet access.
- [ ] **Documentation Updated**: If public API endpoints or environment variables were changed, `.env.example` and `/docs` are updated.

---

## 3. Releasing a New Version

1. Update version number in:
   - `backend/server/app.py`
   - `frontend/package.json`
   - `Dockerfile`
2. Update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/).
3. Tag the release commit:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0: F.R.I.D.A.Y. Polar Digital Twin Platform"
   git push origin v1.0.0
   ```
