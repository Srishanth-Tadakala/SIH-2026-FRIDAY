# Environment Configuration & Hardening

## Configuration Model

F.R.I.D.A.Y. utilizes a centralized, strongly-typed settings engine powered by Pydantic Settings (`backend/server/config.py`). Settings are automatically loaded from:
1. Shell environment variables.
2. The local `.env` file at the repository root.
3. Built-in, secure operational defaults.

To maintain backward compatibility and support multiple configuration conventions, all key settings support both standard variable names and `FRIDAY_` prefixed aliases via Pydantic `AliasChoices`.

---

## Detailed Variable Reference

| Variable Name | Alias | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | `FRIDAY_ENVIRONMENT` | `development` | Operating environment: `development`, `testing`, or `production`. In `production`, strict secret checks are enforced. |
| `SERVER_HOST` | - | `0.0.0.0` | Host IP address to bind FastAPI ASGI server. |
| `SERVER_PORT` | - | `8000` | Port to bind FastAPI ASGI server. |
| `DEBUG` | - | `false` | Enable verbose debug logging. |
| `JWT_SECRET_KEY` | `FRIDAY_SECRET_KEY` | *(dev default)* | Cryptographic HMAC secret key used for signing JWT bearer tokens. In `production`, must be $\ge 32$ characters. |
| `JWT_ALGORITHM` | `FRIDAY_JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `FRIDAY_JWT_EXPIRATION_MINUTES` | `1440` | Lifetime of issued authentication tokens in minutes. |
| `COMMANDER_PIN` | `FRIDAY_COMMANDER_PIN` | `BHARATI-CMD-2026` | Emergency Station Commander authorization PIN for Tier 3 physical actions. In `production`, must be customized and $\ge 8$ characters. |
| `CORS_ALLOWED_ORIGINS` | `FRIDAY_CORS_ORIGINS` | `["http://localhost:5173", ...]` | JSON list or comma-separated list of authorized HTTP origins for CORS validation. |
| `GROQ_API_KEY` | - | `""` *(empty)* | Optional Groq Cloud LPU API key for LLaMA-3.3-70B model inferences. |
| `GROQ_MODEL` | - | `llama-3.3-70b-versatile` | Model identifier for Groq cloud inference. |
| `LOCAL_MONGO_URI` | `MONGODB_URI` | `mongodb://localhost:27017` | Local MongoDB connection URI. Falls back to embedded JSON store if unavailable. |
| `MONGODB_ATLAS_URI` | `CLOUD_MONGO_URI` | `""` *(empty)* | Mainland headquarters MongoDB Atlas connection string. |
| `EDGE_STORAGE_PATH` | `FRIDAY_EDGE_STORAGE_PATH` | `data/edge_storage/friday_embedded_edge.json` | Path to persistent file store for zero-dependency atomic edge persistence. |
| `SATCOM_BANDWIDTH_LIMIT_BPS` | - | `2400` | Bandwidth throughput ceiling in bps for simulated Iridium satellite communications. |
| `WS_MAX_CONNECTIONS` | `FRIDAY_WS_MAX_CONNECTIONS` | `100` | Maximum concurrent WebSocket client connections allowed before rejecting new clients. |

---

## Production Security Hardening Checklist

When deploying F.R.I.D.A.Y. to an active station edge server or cloud environment:

1. **Activate Production Enforcement**:
   ```env
   ENVIRONMENT=production
   ```
2. **Generate Cryptographic Secret Key**:
   ```bash
   openssl rand -hex 32
   ```
   Set `JWT_SECRET_KEY` to the generated 64-character hex string.
3. **Change Station Commander PIN**:
   Set `COMMANDER_PIN` to a strong, station-specific passphrase known only to the Expedition Leader.
4. **Restrict CORS Whitelist**:
   Explicitly specify the domain or internal IP serving the cockpit UI:
   ```env
   CORS_ALLOWED_ORIGINS=["https://antarctic-command.ncpor.res.in"]
   ```
5. **Verify Verification Tests**:
   Run the security test suite to confirm all production guards are active:
   ```bash
   python -m pytest tests/server/test_security_and_auth.py
   ```
