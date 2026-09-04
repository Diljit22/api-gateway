import hmac
import hashlib
import json
import base64
from typing import Optional, Dict, Any, List

class JWTTokenHelper:
    """Zero-dependency JWT helper using HMAC-SHA256 (HS256)."""
    def __init__(self, secret: str = "toy-gateway-super-secret-key-123"):
        self.secret = secret.encode()

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')

    def _base64url_decode(self, data: str) -> bytes:
        rem = len(data) % 4
        if rem > 0:
            data += '=' * (4 - rem)
        return base64.urlsafe_b64decode(data.encode('utf-8'))

    def create_token(self, payload: Dict[str, Any]) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        header_b64 = self._base64url_encode(json.dumps(header).encode('utf-8'))
        payload_b64 = self._base64url_encode(json.dumps(payload).encode('utf-8'))
        
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
        signature_b64 = self._base64url_encode(signature)
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def verify_and_decode(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts
            
            # Recreate signature based on headers and payload
            signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
            expected_signature = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
            expected_signature_b64 = self._base64url_encode(expected_signature)
            
            # Constant-time comparison to protect against timing attacks
            if not hmac.compare_digest(signature_b64.encode('utf-8'), expected_signature_b64.encode('utf-8')):
                return None
                
            payload_bytes = self._base64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode('utf-8'))
            return payload
        except Exception:
            return None

class AuthManager:
    """Manages JWT parsing and prefix-based Role-Based Access Control (RBAC)."""
    def __init__(self):
        self.jwt_helper = JWTTokenHelper()
        # RBAC Path Rules: prefix -> list of roles required
        self.rules: Dict[str, List[str]] = {
            "/_admin": ["admin"],       # Only admin role can view admin status/endpoints
            "/orders": ["user"],        # Only user role can access orders service
        }

    def authenticate(self, auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
        """Parses Bearer token and returns user info if valid."""
        if not auth_header:
            return None
        parts = auth_header.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        token = parts[1].strip()
        return self.jwt_helper.verify_and_decode(token)

    def is_authorized(self, user_info: Optional[Dict[str, Any]], path: str) -> bool:
        """Checks if the authenticated user has permissions to access the path prefix."""
        for prefix, required_roles in self.rules.items():
            if path.startswith(prefix):
                if not user_info:
                    return False
                user_roles = user_info.get("roles", [])
                if not any(role in user_roles for role in required_roles):
                    return False
        return True