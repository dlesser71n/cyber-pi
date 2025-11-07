"""
Security Module for TQAKB-V4
Implements authentication, authorization, and security best practices
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator
import structlog
import hashlib
import hmac
import redis.asyncio as redis
from functools import wraps
import time
import re

from backend.core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token
security = HTTPBearer()

# Rate limiting
rate_limit_redis: Optional[redis.Redis] = None

class TokenData(BaseModel):
    """JWT Token payload"""
    sub: str  # Subject (user_id)
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    role: str = "user"
    permissions: List[str] = []

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    role: str = "user"
    permissions: List[str] = []
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    """User creation model with validation"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        """Ensure password complexity"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class LoginRequest(BaseModel):
    """Login request with validation"""
    username: str
    password: str

class SecurityManager:
    """Manages all security operations"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key.get_secret_value()
        self.algorithm = settings.jwt_algorithm
        self.token_expire_hours = settings.jwt_expiration_hours
        self.refresh_token_expire_days = 7
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": hashlib.sha256(f"{data.get('sub')}:{time.time()}".encode()).hexdigest()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode = data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "jti": hashlib.sha256(f"refresh:{data.get('sub')}:{time.time()}".encode()).hexdigest()
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is revoked
            if await self.is_token_revoked(payload.get("jti")):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return TokenData(**payload)
            
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked in Redis"""
        if not rate_limit_redis:
            return False
        
        revoked = await rate_limit_redis.get(f"revoked_token:{jti}")
        return revoked is not None
    
    async def revoke_token(self, jti: str, exp: datetime):
        """Revoke a token by adding to Redis blacklist"""
        if not rate_limit_redis:
            return
        
        ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
        if ttl > 0:
            await rate_limit_redis.setex(f"revoked_token:{jti}", ttl, "1")

# Singleton instance
security_manager = SecurityManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> User:
    """Get current authenticated user from token"""
    token = credentials.credentials
    token_data = await security_manager.decode_token(token)
    
    # In production, fetch from database
    # For now, create mock user from token data
    user = User(
        id=token_data.sub,
        username=token_data.sub,
        email=f"{token_data.sub}@tqakb.local",
        role=token_data.role,
        permissions=token_data.permissions,
        created_at=datetime.now(timezone.utc)
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if permission not in current_user.permissions and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker

def require_role(role: str):
    """Decorator to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return role_checker

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
    
    async def __call__(self, request, user: Optional[User] = None):
        """Check rate limit for user or IP"""
        if not rate_limit_redis:
            return True
        
        # Use user ID if authenticated, otherwise use IP
        identifier = user.id if user else request.client.host
        key = f"rate_limit:{identifier}"
        
        try:
            current = await rate_limit_redis.incr(key)
            
            if current == 1:
                await rate_limit_redis.expire(key, self.period)
            
            if current > self.calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self.calls} calls per {self.period} seconds"
                )
            
            return True
            
        except redis.RedisError as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open in case of Redis issues
            return True

def rate_limit(calls: int = 100, period: int = 60):
    """Rate limiting decorator"""
    limiter = RateLimiter(calls, period)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = kwargs.get('current_user')
            await limiter(request, user)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

class InputSanitizer:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Truncate to max length
        value = value[:max_length]
        
        # Remove control characters except newline and tab
        value = ''.join(char for char in value if char == '\n' or char == '\t' or ord(char) >= 32)
        
        return value.strip()
    
    @staticmethod
    def validate_key(key: str) -> str:
        """Validate Redis/Kafka key format"""
        if not re.match(r'^[a-zA-Z0-9:_\-\.]+$', key):
            raise ValueError(f"Invalid key format: {key}")
        
        if len(key) > 250:
            raise ValueError(f"Key too long: {len(key)} > 250")
        
        return key
    
    @staticmethod
    def validate_json_path(path: str) -> str:
        """Validate JSON path to prevent injection"""
        if not re.match(r'^[\w\.\[\]]+$', path):
            raise ValueError(f"Invalid JSON path: {path}")
        
        return path

class SecurityHeaders:
    """Security headers middleware"""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    @classmethod
    async def add_security_headers(cls, request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        for header, value in cls.HEADERS.items():
            response.headers[header] = value
        
        return response

async def initialize_security(redis_client: redis.Redis):
    """Initialize security components"""
    global rate_limit_redis
    rate_limit_redis = redis_client
    logger.info("Security module initialized")

# Audit logging
class AuditLogger:
    """Audit trail for security events"""
    
    @staticmethod
    async def log_event(event_type: str, user_id: Optional[str], details: Dict[str, Any]):
        """Log security event"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        logger.info("Security event", **event)
        
        # In production, also write to Kafka for permanent storage
        # await kafka_producer.send("security.audit", value=event)

# API Key management
class APIKeyManager:
    """Manage API keys for service-to-service auth"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return hashlib.sha256(f"tqakb:{time.time()}:{os.urandom(32).hex()}".encode()).hexdigest()
    
    @staticmethod
    async def validate_api_key(api_key: str) -> bool:
        """Validate API key"""
        if not rate_limit_redis:
            return False
        
        # Check if key exists and is valid
        key_data = await rate_limit_redis.get(f"api_key:{api_key}")
        return key_data is not None

import os  # Add at top for API key generation