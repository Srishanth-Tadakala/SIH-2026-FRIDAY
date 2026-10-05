# Changelog

All notable changes to the **F.R.I.D.A.Y.** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-05

### Added
- **Formal Open-Source Architecture Documentation**: Structured `/docs` hierarchy including system overview, telemetry pillars, multi-agent cognitive architecture, satcom sync engine, database layer, development setup, and deployment guides.
- **Community Governance & Standards**: Added `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `CHANGELOG.md`, and `.github/pull_request_template.md`.
- **Configuration Alias Support**: Added Pydantic `AliasChoices` in `backend/server/config.py` enabling both standard setting names and `FRIDAY_*` environment variables seamlessly.
- **Enhanced Security Policy**: Updated `SECURITY.md` with explicit vulnerability disclosure procedures, SLA response timelines, and supported version matrices.
- **Postman API Suite**: Full Postman v2.1.0 collection (`postman_collection.json`) and environment (`postman_environment.json`) covering all 60 REST endpoints.

### Changed
- **Synchronized Environment Template**: Aligned `.env.example` with current platform configuration defaults and security requirements.
- **Root Gitignore Hardening**: Expanded `.gitignore` with coverage for temporary scratch directories, `.ruff_cache/`, `node_modules/`, `dist/`, logs, and edge storage artifacts.

### Removed
- **Unused Frontend Legacy Components**: Safely pruned 10 unreferenced legacy prototype components (`BentoCapabilities.tsx`, `HeroCtaBanner.tsx`, `InteractiveCrisisBar.tsx`, `MetricRoiCards.tsx`, `NavigationHeader.tsx`, `PartnerCloud.tsx`, `PolarCommandCanvas.tsx`, `StationCardsSection.tsx`, `TopTitleSection.tsx`, `UnderMaintenanceView.tsx`).
- **Template Starter Assets**: Removed default starter assets (`react.svg`, `vite.svg`, `hero.png`) that were unreferenced across the codebase.
- **Temporary Debug Scripts**: Cleaned untracked CI monitoring scripts from `scratch/`.

### Verified
- **Backend Test Suite**: 397 unit, integration, and failure injection tests passing via `pytest`.
- **API Benchmark**: 60 of 60 endpoints passing with 100% success rate.
- **Frontend Verification**: TypeScript build (`tsc -b`), Vitest unit tests (16/16 passing), and Oxlint checks clean with zero errors.
- **Security Audit**: Zero committed credentials or sensitive tokens in repository history.
