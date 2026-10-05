# Contributing to F.R.I.D.A.Y.

Thank you for your interest in contributing to **F.R.I.D.A.Y.** (*Fleet, Resource, Infrastructure, Diagnostics, Automation & Yield*), the open-source polar digital twin and cognitive operations platform for Antarctic research outposts.

Whether you are fixing a bug, adding new physics sensor definitions, enhancing SCADA bridges, optimizing satcom telemetry compression, or improving UI accessibility, your contributions are welcome!

---

## 1. Code of Conduct

This project is governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## 2. Getting Started

### 2.1 Prerequisites
- **Python**: 3.11, 3.12, or 3.14 (Python 3.12+ recommended)
- **Node.js**: v20 or v22 LTS
- **Git**
- Optional: **Docker** & **Docker Compose**

### 2.2 Local Repository Setup
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/SIH-2026-FRIDAY.git
   cd SIH-2026-FRIDAY
   ```
3. Initialize the configuration:
   ```bash
   cp .env.example .env
   ```
4. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Install frontend dependencies:
   ```bash
   cd frontend
   npm ci
   cd ..
   ```

---

## 3. Development Workflow

### 3.1 Branching Strategy
- `main`: Production-ready branch. All changes land here via Pull Requests.
- Feature branches should branch off `main` with descriptive prefixes:
  - `feat/<feature-name>` for new features or capabilities
  - `fix/<bug-name>` for bug fixes
  - `refactor/<module>` for non-breaking code cleanup
  - `docs/<topic>` for documentation improvements
  - `test/<suite>` for test additions or hardening

### 3.2 Commit Conventions
We follow the Conventional Commits specification:
```text
<type>(<scope>): <short description>

[optional body]

[optional footer(s)]
```
Examples:
- `feat(telemetry): add wind turbulence decay model for katabatic storms`
- `fix(auth): enforce constant-time PIN comparison on commander lockout`
- `docs(api): document DTN bundle custody transfer schemas`

---

## 4. Verification & Testing Standards

All pull requests must pass the complete automated test and linting pipeline before merge.

### 4.1 Backend Verification
Run the backend test suite:
```bash
python -m pytest
```
Verify that code quality and linting rules pass:
```bash
python -m ruff check backend/ tests/ --select E9,F63,F7,F82
```
Test end-to-end API benchmarks:
```bash
python tools/test_all_endpoints.py
```

### 4.2 Frontend Verification
Inside the `frontend/` directory:
```bash
cd frontend
npm run lint    # Runs oxlint
npm run test    # Runs vitest test suite
npm run build   # Verifies TypeScript compiler (tsc -b) & Vite bundle
cd ..
```

---

## 5. Architectural Invariants to Respect

When contributing code, please preserve the following core system design principles:
1. **Offline Autonomy Invariant**: The system must run 100% autonomously without external cloud access. Never introduce hard dependencies on cloud APIs without local offline fallbacks.
2. **Three-Tier Safety Interlock**:
   - Tier 1: Autonomous fast-loop micro-adjustments (<1.2s, strictly non-destructive).
   - Tier 2: Supervised operational changes (60s countdown, operator veto).
   - Tier 3: Emergency high-hazard actions (Station Commander PIN authorization required).
3. **Deterministic Digital Twin**: Sensor models in `backend/sensors/` must maintain physical validity (thermodynamics, power balance, hydraulic pressure).
4. **Bandwidth Awareness**: Polar satellite communication is constrained (simulated 2400 bps). All new telemetry streams must support deadband filtering and delta compression.

---

## 6. Submitting a Pull Request (PR)

1. Ensure your branch is rebased on the latest `main`.
2. Ensure all 397+ backend tests and all frontend tests pass cleanly.
3. Open a Pull Request referencing any relevant issues.
4. Fill in the [Pull Request Template](.github/pull_request_template.md).
5. At least one code review approval and clean CI status are required before merge.

---

## 7. Reporting Bugs & Security Issues

- For general bugs and feature suggestions, open an issue on the GitHub Issues tracker.
- For sensitive security vulnerabilities, please refer to our [Security Policy](SECURITY.md) and email `ncpor@moes.gov.in` instead of opening a public issue.
