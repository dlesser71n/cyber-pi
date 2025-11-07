#!/usr/bin/env python3
"""
Authentication and security for cyber-pi API
JWT-based authentication with enterprise-grade security
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import hashlib
import secrets

from config.settings import settings

logger = logging.getLogger(__name__)

# JWT Configuration
security = HTTPBearer(auto_error=False)

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class JWTManager:
    """Manages JWT token operations"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        
        # In production, this should be replaced with proper user database
        # For now, using demo credentials
        self.demo_users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "roles": ["admin", "analyst"],
                "permissions": ["read", "write", "delete", "admin"]
            },
            "analyst": {
                "password_hash": self._hash_password("analyst123"),
                "roles": ["analyst"],
                "permissions": ["read", "write"]
            },
            "viewer": {
                "password_hash": self._hash_password("viewer123"),
                "roles": ["viewer"],
                "permissions": ["read"]
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_value = password_hash.split(":")
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == hash_value
        except ValueError:
            return False
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        user = self.demo_users.get(username)
        if not user:
            return None
        
        if not self._verify_password(password, user["password_hash"]):
            return None
        
        return {
            "username": username,
            "roles": user["roles"],
            "permissions": user["permissions"]
        }
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT error: {e}")
            return None
    
    def has_permission(self, user_data: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission"""
        user_permissions = user_data.get("permissions", [])
        return required_permission in user_permissions or "admin" in user_permissions

# Global JWT manager
jwt_manager = JWTManager()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_data = jwt_manager.verify_token(credentials.credentials)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_dependency(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not jwt_manager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_dependency

# Rate limiting (simple in-memory implementation)
class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self):
        self.requests = {}
        self.limit = settings.rate_limit_per_minute
        self.window = 60  # seconds
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow().timestamp()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < self.window]
        
        # Check limit
        if len(self.requests[key]) >= self.limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter()

async def rate_limit_check(identifier: str = "default"):
    """Check rate limit for identifier"""
    if not rate_limiter.is_allowed(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
