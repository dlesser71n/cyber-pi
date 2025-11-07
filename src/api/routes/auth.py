#!/usr/bin/env python3
"""
Authentication API endpoints
Login, token management, and user operations
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Dict, Any
import logging
from datetime import datetime

from ..auth import jwt_manager, rate_limit_check, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    """User information response"""
    username: str
    roles: list
    permissions: list

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token
    """
    try:
        # Apply rate limiting
        await rate_limit_check(f"login:{request.username}")
        
        # Authenticate user
        user_data = jwt_manager.authenticate_user(request.username, request.password)
        if user_data is None:
            logger.warning(f"Failed login attempt for user: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create access token
        access_token = jwt_manager.create_access_token(user_data)
        
        logger.info(f"User logged in: {request.username}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=jwt_manager.access_token_expire_minutes * 60,
            user={
                "username": user_data["username"],
                "roles": user_data["roles"],
                "permissions": user_data["permissions"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserResponse(
        username=current_user["username"],
        roles=current_user["roles"],
        permissions=current_user["permissions"]
    )

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout user (client-side token invalidation)
    """
    logger.info(f"User logged out: {current_user['username']}")
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify if current token is valid
    """
    return {
        "valid": True,
        "user": current_user["username"],
        "expires_at": datetime.fromtimestamp(current_user["exp"]).isoformat()
    }

@router.post("/refresh")
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Refresh access token
    """
    try:
        # Create new token with same user data
        new_token = jwt_manager.create_access_token(current_user)
        
        return {
            "access_token": new_token,
            "token_type": "Bearer",
            "expires_in": jwt_manager.access_token_expire_minutes * 60
        }
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
