import hashlib
import hmac
import json
import base64
import time
from functools import wraps
from flask import request, jsonify
from config import Config

# ------------------------------------------------------------------
# Password hashing (SHA-256 demo implementation)
# ------------------------------------------------------------------
def hash_password(password):
    salt = "cybersec"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def verify_password(password, password_hash):
    return hmac.compare_digest(hash_password(password), password_hash)

# ------------------------------------------------------------------
# JWT implementation using Python standard library only
# (no external PyJWT dependency required)
# ------------------------------------------------------------------
def _b64url(data):
    """Base64url encode without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64url_decode(data):
    """Base64url decode with padding restored."""
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _sign(header, payload):
    """Create HMAC-SHA256 signature for header+payload."""
    signing_input = f"{header}.{payload}".encode()
    signature = hmac.new(Config.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    return _b64url(signature)

def create_token(user_id, role):
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload_data = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + Config.JWT_EXPIRATION_HOURS * 3600
    }
    payload = _b64url(json.dumps(payload_data).encode())
    signature = _sign(header, payload)
    return f"{header}.{payload}.{signature}"

def decode_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        expected = _sign(header, payload)
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time():
            return None  # expired
        return data
    except Exception:
        return None

# ------------------------------------------------------------------
# Auth decorators
# ------------------------------------------------------------------
def _extract_token():
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.user_id = data["user_id"]
        request.user_role = data["role"]
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401
        if data["role"] != "admin":
            return jsonify({"error": "Admin access required"}), 403
        request.user_id = data["user_id"]
        request.user_role = data["role"]
        return f(*args, **kwargs)
    return decorated
