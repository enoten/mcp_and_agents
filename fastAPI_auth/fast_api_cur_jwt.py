"""
FastAPI currency rate API with JWT authentication.

Requires Bearer token in Authorization header for all endpoints.
Uses stdlib-only JWT verification (no PyJWT required).
"""
import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv(Path(__file__).parent / ".env")

# JWT config
JWT_SECRET = os.environ.get("FAPI_JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

# Path to your local JSON file (project root)
DATA_FILE = str(Path(__file__).parent.parent / "rates.json")

security = HTTPBearer(auto_error=False)


def _base64url_decode(s: str) -> bytes:
    """Decode base64url string to bytes."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _verify_hs256_jwt(token: str, secret: str) -> dict:
    """Verify HS256 JWT and return payload. Raises ValueError if invalid."""
    if not secret:
        raise ValueError("JWT secret not configured")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    header_b64, payload_b64, sig_b64 = parts
    message = f"{header_b64}.{payload_b64}".encode()
    secret_bytes = secret.encode() if isinstance(secret, str) else secret
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(secret_bytes, message, hashlib.sha256).digest()
    ).rstrip(b"=").decode("ascii")
    if not hmac.compare_digest(sig_b64, expected_sig):
        raise ValueError("Invalid signature")
    payload_json = _base64url_decode(payload_b64).decode("utf-8")
    payload = json.loads(payload_json)
    exp = payload.get("exp")
    if exp is not None and exp < int(time.time()):
        raise ValueError("Token expired")
    return payload


def verify_token(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """Verify JWT and return payload. Raises 401 if invalid."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        if JWT_ALGORITHM and JWT_ALGORITHM.upper() != "HS256":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Only HS256 is supported without PyJWT",
            ) from None
        payload = _verify_hs256_jwt(token, JWT_SECRET or "")
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def load_rates():
    """Helper function to load data from the JSON file."""
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


app = FastAPI(title="Currency Rate API (JWT Protected)")


@app.get("/rate/{base_currency}/{target_currency}")
async def get_cross_rate(
    base_currency: str,
    target_currency: str,
    _payload: dict = Depends(verify_token),
):
    """Returns the cross rate for a given currency pair. Requires JWT Bearer token."""
    base = base_currency.upper()
    target = target_currency.upper()

    data = load_rates()

    if base not in data:
        raise HTTPException(status_code=404, detail=f"Base currency '{base}' not found.")

    rate = data[base].get(target)
    if rate is None:
        raise HTTPException(
            status_code=404, detail=f"Rate for {base} to {target} not available."
        )

    return {"base": base, "target": target, "rate": rate}


@app.get("/health")
async def health():
    """Health check - no auth required."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
