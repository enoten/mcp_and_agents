# FastAPI Auth

JWT-protected FastAPI currency rate API with a Python client. Uses **stdlib-only** JWT handling (no PyJWT dependency) for both server verification and client token creation.

## Overview

| Component | File | Description |
|-----------|------|-------------|
| **API Server** | `fast_api_cur_jwt.py` | FastAPI app with JWT auth on `/rate` endpoint |
| **API Client** | `fast_api_cur_jwt_client.py` | CLI/client to call the API with JWT |

## Quick Start

### 1. Configure Environment

Create `fastAPI_auth/.env`:

```
FAPI_JWT_SECRET=your-256-bit-secret-key
```

Generate a secure secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Ensure rates.json Exists

The API reads currency rates from `rates.json` in the **project root** (parent of `fastAPI_auth`):

```
mcp_and_agents/
├── rates.json          # Required
└── fastAPI_auth/
    ├── .env
    ├── fast_api_cur_jwt.py
    └── fast_api_cur_jwt_client.py
```

### 3. Start the API

```bash
cd fastAPI_auth
python fast_api_cur_jwt.py
```

Server runs at `http://localhost:8000`.

### 4. Call the API

```bash
# Default: USD → GBP
python fast_api_cur_jwt_client.py

# Specific pair
python fast_api_cur_jwt_client.py EUR JPY
```

---

## API Reference

### Base URL

`http://localhost:8000`

### Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/rate/{base_currency}/{target_currency}` | GET | **Bearer JWT** | Cross currency rate |
| `/health` | GET | None | Health check |

### Authentication

All protected endpoints require:

```
Authorization: Bearer <token>
```

The token must be an HS256 JWT signed with `FAPI_JWT_SECRET` and include `exp` (expiration).

### Response Format

**Success (200):**
```json
{
  "base": "USD",
  "target": "GBP",
  "rate": 0.78
}
```

**Errors:**
- `401` – Missing or invalid token
- `404` – Currency not found

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FAPI_JWT_SECRET` | Yes | — | Secret for JWT signing/verification (HS256) |
| `JWT_ALGORITHM` | No | `HS256` | Algorithm (only HS256 supported without PyJWT) |
| `API_BASE_URL` | No | `http://localhost:8000` | API URL (client only) |

### rates.json Format

```json
{
  "USD": { "EUR": 0.92, "GBP": 0.78, "JPY": 150.50 },
  "EUR": { "USD": 1.09, "GBP": 0.85, "JPY": 163.20 },
  "GBP": { "USD": 1.28, "EUR": 1.18, "JPY": 192.10 }
}
```

Keys: base currency → target currency → rate.

---

## Usage Examples

### Python Client (CLI)

```bash
cd fastAPI_auth
python fast_api_cur_jwt_client.py USD GBP
```

### Python Client (as Module)

```python
from fast_api_cur_jwt_client import get_rate, create_jwt_token

# Get rate
result = get_rate("USD", "EUR")
print(result)  # {"base": "USD", "target": "EUR", "rate": 0.92}

# Get token for custom use
token = create_jwt_token(sub="my-app", exp_hours=2)
```

### cURL

```bash
cd fastAPI_auth
TOKEN=$(python -c "from fast_api_cur_jwt_client import create_jwt_token; print(create_jwt_token())")
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/rate/USD/GBP
```

### Health Check (No Auth)

```bash
curl http://localhost:8000/health
```

---

## Dependencies

```bash
pip install fastapi uvicorn python-dotenv
```

**No PyJWT required** – both server and client use Python stdlib (`base64`, `hmac`, `hashlib`, `json`, `time`) for JWT creation and verification.

---

## File Structure

```
fastAPI_auth/
├── .env                    # FAPI_JWT_SECRET
├── README.md               # This file
├── fast_api_cur_jwt.py     # API server
└── fast_api_cur_jwt_client.py  # API client
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `FAPI_JWT_SECRET must be set` | Add to `.env` or set env var |
| `Missing Authorization header` | Ensure `Authorization: Bearer <token>` is sent |
| `Invalid or expired token` | Regenerate token; verify secret matches server |
| `FileNotFoundError: rates.json` | Create `rates.json` in project root (parent dir) |
| `Connection refused` | Start API with `python fast_api_cur_jwt.py` first |
| `Base currency 'X' not found` | Add currency to `rates.json` |

### Running from Different Directories

The API resolves `rates.json` as `Path(__file__).parent.parent / "rates.json"`, so it always looks in the project root. Run from any directory:

```bash
python fastAPI_auth/fast_api_cur_jwt.py
```

---

## Security Notes

- Use a strong, random secret (256+ bits) for `FAPI_JWT_SECRET`
- Never commit `.env` or secrets to version control
- In production, use HTTPS and consider shorter token expiry
- The client supports `exp_hours` in `create_jwt_token()` for custom expiry
