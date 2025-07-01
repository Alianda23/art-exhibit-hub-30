
import jwt
import datetime
import os
from functools import wraps
from http.server import BaseHTTPRequestHandler
from decimal import Decimal
import json

# Get the secret key from environment or use a default (in production, always use environment variables)
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'afriart_default_secret_key')

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def generate_token(user_id, name, is_admin):
    """Generate a JWT token for authentication"""
    payload = {
        "sub": str(user_id),  # Ensure user_id is converted to string
        "name": name,
        "is_admin": is_admin,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    
    print(f"Generating token with payload: {payload}")
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token):
    """Verify a JWT token"""
    try:
        print(f"Verifying token: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"Token decoded successfully: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token verification failed: Token expired")
        return {"error": "Token expired"}
    except jwt.InvalidTokenError as e:
        print(f"Token verification failed: Invalid token - {str(e)}")
        return {"error": f"Invalid token: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error during token verification: {str(e)}")
        return {"error": f"Token verification error: {str(e)}"}

def extract_auth_token(handler):
    """Extract token from Authorization header
    
    This function can accept either:
    - A BaseHTTPRequestHandler object (with headers attribute)
    - A string that is already an Authorization header value
    """
    if isinstance(handler, str):
        # Handler is already an auth header string
        auth_header = handler
    elif hasattr(handler, 'headers'):
        # Handler is a request handler object
        auth_header = handler.headers.get('Authorization', '')
    else:
        # Unknown type
        print(f"Warning: extract_auth_token received unknown type: {type(handler)}")
        return None
    
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    elif " " in auth_header:
        token = auth_header.split(" ")[1]
    
    return token

def auth_required(handler_method):
    """Decorator to ensure a valid token is present for protected routes"""
    @wraps(handler_method)
    def wrapper(self, *args, **kwargs):
        token = extract_auth_token(self)
        
        if not token:
            self._set_response(401)
            self.wfile.write(b'{"error": "Authentication required"}')
            return None
        
        payload = verify_token(token)
        if isinstance(payload, dict) and "error" in payload:
            self._set_response(401)
            self.wfile.write(f'{{"error": "{payload["error"]}"}}'.encode())
            return None
        
        # Attach user info to the handler
        self.user_info = payload
        return handler_method(self, *args, **kwargs)
    
    return wrapper

def admin_required(handler_method):
    """Decorator to ensure the user is an admin for admin-only routes"""
    @wraps(handler_method)
    def wrapper(self, *args, **kwargs):
        token = extract_auth_token(self)
        
        if not token:
            self._set_response(401)
            self.wfile.write(b'{"error": "Authentication required"}')
            return None
        
        payload = verify_token(token)
        if isinstance(payload, dict) and "error" in payload:
            self._set_response(401)
            self.wfile.write(f'{{"error": "{payload["error"]}"}}'.encode())
            return None
        
        # Check if user is admin
        if not payload.get("is_admin", False):
            self._set_response(403)
            self.wfile.write(b'{"error": "Unauthorized access: Admin privileges required"}')
            return None
        
        # Attach user info to the handler
        self.user_info = payload
        return handler_method(self, *args, **kwargs)
    
    return wrapper

# Helper function to safely encode JSON with Decimal values
def json_dumps(data):
    """Safely convert data to JSON string, handling Decimal types"""
    return json.dumps(data, cls=DecimalEncoder)
