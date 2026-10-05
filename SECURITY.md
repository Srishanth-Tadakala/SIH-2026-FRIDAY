# F.R.I.D.A.Y. Security Architecture & Threat Model

**Platform:** F.R.I.D.A.Y. Polar Digital Twin Platform (SIH 2026 - SIH26060)  
**Classification:** Defense-Grade / Polar Critical Infrastructure  
**Audience:** NCPOR Mainland Command, Antarctic Station Engineers, Security Auditors

---

## 1. Threat Model & Operational Reality

Indian Antarctic research outposts (**Bharati** at Larsemann Hills and **Maitri** at Schirmacher Oasis) operate under severe physical and cyber constraints:
1. **Isolated Edge Infrastructure**: Local SCADA networks operate over air-gapped or high-latency satellite links (Inmarsat BGAN / Iridium Certus).
2. **Untrusted Mainlines & Public Internet**: When bridging telemetry to NCPOR Mainland Mission Control (Goa), communications pass through public satellite transponders.
3. **Severe Physical Consequences**: Any unauthorized actuator manipulation (e.g., shutting down CHP generators or opening exterior dampers during a $-50^\circ\text{C}$ blizzard) causes utilidor freezing within 18 minutes, resulting in structural destruction and life-support failure.

To address these threats, F.R.I.D.A.Y. implements a zero-trust, defense-in-depth security model across five protective rings.

---

## 2. Authentication & Session Management

### 2.1 JSON Web Tokens (JWT) with HS256
- All REST endpoints (under `/api/*`) and WebSocket connections (under `/ws/*`) require cryptographic Bearer tokens.
- **Algorithm**: HMAC-SHA256 (`HS256`).
- **Configurable Expiry**: Tokens default to 60-minute lifetimes (`FRIDAY_JWT_EXPIRATION_MINUTES=60`).
- **Claims**: Tokens carry `sub` (username), `role` (assigned role), `station_id` (station scope), and `exp` (UNIX epoch expiration).
- **Environment Gating**: In `production`, any missing or invalid token immediately aborts with `HTTP 401 Unauthorized`. In `development` and `testing`, unauthenticated calls are safely scoped to a restricted developer role (`ENGINEER`) for testing convenience.

### 2.2 Password Security & Credential Storage
- Passwords are never stored in plaintext.
- **Hashing**: Salted `PBKDF2-HMAC-SHA256` with 100,000 iterative derivation rounds and a cryptographically secure 16-byte random salt (`secrets.token_hex(16)`).
- **Verification**: Constant-time comparison (`hmac.compare_digest`) protects against timing attacks.

---

## 3. Role-Based Access Control (RBAC)

F.R.I.D.A.Y. enforces a strict 5-tier role hierarchy:

```
[0: VIEWER] ──> [1: OPERATOR] ──> [2: ENGINEER] ──> [3: COMMANDER] ──> [4: ADMIN]
```

| Role | Permissions & Operational Scope |
| :--- | :--- |
| **VIEWER** | Read-only telemetry, digital twin state monitoring, historical charts, alarm views. Cannot dispatch commands or mutate state. |
| **OPERATOR** | Tier 1 autonomous action proposals, telemetry acknowledgment, manual sensor offset reviews. |
| **ENGINEER** | Tier 2 supervised action execution, bypass of countdown queues, copilot parameter tuning, system diagnostics. |
| **COMMANDER** | Tier 3 emergency high-risk actions (generator load shedding, life-support overrides), evacuation protocol authorization, station lockdown. |
| **ADMIN** | User lifecycle management, secret rotation, system reboot, raw physical actuator overrides. |

---

## 4. Actuator Safety Interlocks & Tiered Autonomy

To guarantee that AI models (LLMs/agents) never execute unchecked physical operations:

### 4.1 Autonomy Tiers
- **Tier 1 (Autonomous Micro-Adjustments)**: Non-destructive, reversible trims (e.g., radiator valve $\pm 2\%$) execute automatically within strictly bounded safety envelopes.
- **Tier 2 (Supervised Operational Changes)**: Significant adjustments enter a mandatory 60-second supervised countdown window with real-time operator veto capability.
- **Tier 3 (Commander Emergency Confirmation)**: High-risk actions (backup generator cutover, life-support ventilation changes) require explicit dual-factor Commander authorization:
  1. Valid Station Commander PIN.
  2. Single-use, time-bounded HMAC-SHA256 execution token (`consume_execution_token`).

### 4.2 Commander PIN Protection
- Verified against salted PBKDF2 hash.
- **Exponential Brute-Force Lockout**:
  - 3 failed attempts: 60-second lockout.
  - 5 failed attempts: 300-second lockout.
  - 8+ failed attempts: 1800-second lockout.
- Token replay prevention: Every execution token can only be consumed once.

### 4.3 Deterministic Safety Policy (`SafetyPolicy`)
Centralized in `backend/core/safety_policy.py`, immutable safety rules supersede any autonomous proposal:
- Indoor Living Module Temperature: $\ge 16.0^\circ\text{C}$
- Utildor Pipe Trace Heating: $\ge 4.0^\circ\text{C}$
- Potable Water Reserve Minimum: $\ge 1500\text{ Liters}$
- Maximum Permissible Smoke Obscuration: $\le 1.5\%$
- Battery State of Charge (SoC) Minimum: $\ge 20\%$
- Blizzard Drone Sortie Weather Gate: Wind $\le 45\text{ km/h}$, Visibility $\ge 200\text{ m}$

---

## 5. Network & WebSocket Hardening

1. **CORS Sanitization**: Strict whitelist of authorized origins (`FRIDAY_CORS_ORIGINS`). Wildcard (`*`) is prohibited.
2. **WebSocket Handshake Authentication**: `/ws/*` endpoints validate token authentication either via query parameter (`?token=...`) or HTTP authorization headers prior to connection acceptance.
3. **Connection Flooding Protection**: Station-scoped limits and global maximum connection limits (`FRIDAY_WS_MAX_CONNECTIONS=100`) reject denial-of-service connection storms.
4. **Backpressure Protection**: Outbound WebSocket frames use bounded timeouts (2.0s) to prevent slow clients from buffering memory indefinitely.

---

## 6. Information Leakage Prevention & Error Handling

- **Sanitized Global Exception Handler**: All unhandled exceptions generate an anonymized `request_id` (UUID4).
- Internal stack traces, database schemas, and Python module names are completely stripped from client responses.
- Client receives only:
  ```json
  {
    "error": "Internal Server Error",
    "request_id": "c1a938e2-...",
    "detail": "An unexpected error occurred. Reference the request_id with system administrators."
  }
  ```
- Detailed logs with tracebacks are emitted exclusively to server-side stderr/logs.

---

## 7. Secrets Management & Operational Guidelines

1. **Zero Hardcoded Secrets**: Secrets are loaded from environment variables (`.env`) via `backend/server/config.py`.
2. **Git Protection**: `.env` and sensitive artifacts are permanently ignored in `.gitignore`.
3. **Production Deployment Checklist**:
   - [ ] Set `FRIDAY_ENVIRONMENT=production`
   - [ ] Generate secure `FRIDAY_SECRET_KEY` using `openssl rand -hex 32`
   - [ ] Update default Commander PIN `FRIDAY_COMMANDER_PIN`
   - [ ] Set explicit `FRIDAY_CORS_ORIGINS` to domain(s) serving the frontend
   - [ ] Run automated security tests: `pytest tests/server/test_security_and_auth.py`

---

## 8. Vulnerability Reporting & Responsible Disclosure

We take the security of Antarctic critical infrastructure systems seriously. If you discover a vulnerability, please report it responsibly:

### Supported Versions
| Version | Supported |
| :--- | :--- |
| 1.0.x | :white_check_mark: Active security support |
| < 1.0 | :x: End of Life |

### Reporting Procedure
1. **Do NOT open a public GitHub issue** for undisclosed vulnerabilities.
2. Send details via email to: `ncpor@moes.gov.in` (Subject: `[SECURITY] F.R.I.D.A.Y. Vulnerability Disclosure`).
3. Include:
   - A description of the issue and potential impact.
   - Step-by-step reproduction steps or proof-of-concept.
   - Any suggested remediations.

### Response Timeline & SLA
- **Acknowledgment**: Within 48 hours of receipt.
- **Assessment & Triage**: Within 5 business days.
- **Patch Release & Advisory**: We coordinate patches and public release following industry best practices.

