"""
Client to call the FastAPI currency rate API with JWT authentication.

Uses stdlib-only JWT creation (no PyJWT required).
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
JWT_SECRET = os.environ.get("FAPI_JWT_SECRET")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


def _base64url_encode(data: bytes) -> str:
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_jwt_token(sub: str = "api-client", exp_hours: int = 1) -> str:
    """Create HS256 JWT using stdlib only (no PyJWT dependency)."""
    if not JWT_SECRET:
        raise ValueError(
            "FAPI_JWT_SECRET must be set in environment. "
            "Add to fastAPI_auth/.env to match the server."
        )
    if JWT_ALGORITHM and JWT_ALGORITHM.upper() != "HS256":
        raise ValueError("Only HS256 is supported without PyJWT. Set JWT_ALGORITHM=HS256.")
    payload = {
        "sub": sub,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_hours * 3600,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    message = f"{header_b64}.{payload_b64}".encode()
    secret_bytes = JWT_SECRET.encode() if isinstance(JWT_SECRET, str) else JWT_SECRET
    signature = hmac.new(secret_bytes, message, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def get_rate(base: str, target: str) -> dict:
    """Call the API to get cross rate. Returns dict with base, target, rate."""
    token = create_jwt_token()
    url = f"{API_BASE_URL.rstrip('/')}/rate/{base}/{target}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode() if e.fp else ""
        except Exception:
            body = ""
        print(f"API Error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print("Is the API server running? (python fast_api_cur_jwt.py)", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if not JWT_SECRET:
        print("ERROR: FAPI_JWT_SECRET not set. Add to fastAPI_auth/.env", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        base_currency = sys.argv[1]
        target_currency = sys.argv[2]
    else:
        base_currency = "USD"
        target_currency = "GBP"

    result = get_rate(base_currency, target_currency)
    print(json.dumps(result, indent=2))
