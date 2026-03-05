"""
Generate a cryptographically secure JWT secret key for MCP/API auth.

Output is suitable for MCP_JWT_SECRET, FAPI_JWT_SECRET, etc.
"""
import secrets

# 256 bits (32 bytes) - recommended for HS256
SECRET_BYTES = 32
secret = secrets.token_urlsafe(SECRET_BYTES)

print("# Add to .env:")
print(f"MCP_JWT_SECRET={secret}")
print(f"FAPI_JWT_SECRET={secret}")
print()
print("# Or copy just the key:")
print(secret)
