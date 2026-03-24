from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from jose import JWTError
import redis
import os
import sys

from auth import create_token, verify_token, decode_token_without_verify
from users import get_user, is_device_registered
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ZTNA Auth Service")

# Redis connection - MANDATORY
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'ztna-redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True,
        socket_connect_timeout=5
    )
    redis_client.ping()
    print("✓ Redis connected successfully")
except Exception as e:
    print(f"❌ CRITICAL: Redis connection failed - {e}")
    print("Redis is mandatory for ZTNA security (token blacklisting, rate limiting)")
    sys.exit(1)  # Exit if Redis not available

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REQUEST MODELS ──────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    device_id: str      # konse device se login ho raha hai

class VerifyRequest(BaseModel):
    token: str

class LogoutRequest(BaseModel):
    token: str

# ─── ROUTES ──────────────────────────────────

@app.post("/login")
def login(req: LoginRequest):
    """
    Login with rate limiting and session tracking
    """
    print(f"\nLogin attempt: {req.email} | Device: {req.device_id}")

    # RATE LIMITING - Check failed attempts
    failed_key = f"failed_login:{req.email}"
    failed_attempts = redis_client.get(failed_key)
    
    if failed_attempts and int(failed_attempts) >= 5:
        ttl = redis_client.ttl(failed_key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {ttl} seconds"
        )

    # CHECK 1 — User exist karta hai?
    user = get_user(req.email)
    if not user:
        print(f"User nahi mila: {req.email}")
        # Increment failed attempts
        redis_client.incr(failed_key)
        redis_client.expire(failed_key, 300)  # 5 minutes
        raise HTTPException(
            status_code=401,
            detail="Email ya password galat hai"
        )

    # CHECK 2 — Password sahi hai?
    if user["password"] != req.password:
        print(f"Password galat: {req.email}")
        # Increment failed attempts
        redis_client.incr(failed_key)
        redis_client.expire(failed_key, 300)  # 5 minutes
        raise HTTPException(
            status_code=401,
            detail="Email ya password galat hai"
        )

    # CHECK 3 — Device registered hai?
    if not is_device_registered(req.device_id):
        print(f"Device registered nahi: {req.device_id}")
        raise HTTPException(
            status_code=403,
            detail=f"Device '{req.device_id}' company mein registered nahi hai"
        )

    # SUCCESS - Clear failed attempts
    redis_client.delete(failed_key)
    
    # Create token
    token = create_token(req.email, user["role"], user["name"])
    
    # Track active session in Redis
    session_key = f"session:{req.email}:{req.device_id}"
    redis_client.setex(session_key, 900, token)  # 15 minutes (900 seconds)
    
    # Track user's active devices
    user_devices_key = f"user_devices:{req.email}"
    redis_client.sadd(user_devices_key, req.device_id)
    redis_client.expire(user_devices_key, 86400)  # 24 hours

    print(f"✓ Login successful: {req.email} | Session tracked in Redis")
    
    return {
        "token": token,
        "email": req.email,
        "name": user["name"],
        "role": user["role"],
        "expires_in": "15 minutes",
        "device_id": req.device_id
    }


@app.post("/verify")
def verify(req: VerifyRequest):
    """
    Gateway har request pe ye endpoint call karta hai —
    token valid hai ya nahi check karne ke liye
    """
    # Check if token is blacklisted
    blacklist_key = f"blacklist:{req.token}"
    if redis_client.exists(blacklist_key):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked (logged out)"
        )
    
    try:
        user_info = verify_token(req.token)
        return user_info

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token invalid ya expire ho gaya"
        )


@app.post("/logout")
def logout(req: LogoutRequest):
    """
    Logout - Add token to blacklist
    """
    try:
        # Decode token to get expiry time
        payload = decode_token_without_verify(req.token)
        email = payload.get("sub")
        exp = payload.get("exp")
        
        if not exp:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Calculate remaining TTL
        from datetime import datetime
        exp_time = datetime.fromtimestamp(exp)
        now = datetime.utcnow()
        ttl = int((exp_time - now).total_seconds())
        
        if ttl > 0:
            # Add to blacklist with TTL
            blacklist_key = f"blacklist:{req.token}"
            redis_client.setex(blacklist_key, ttl, "revoked")
            
            # Remove active session
            # We don't have device_id here, so remove all sessions for this user
            pattern = f"session:{email}:*"
            for key in redis_client.scan_iter(match=pattern):
                redis_client.delete(key)
            
            print(f"✓ Logout successful: {email} | Token blacklisted for {ttl}s")
            return {
                "message": "Logged out successfully",
                "email": email
            }
        else:
            return {"message": "Token already expired"}
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Logout failed: {str(e)}"
        )


@app.get("/health")
def health():
    # Check Redis health
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "Auth service chal rahi hai!",
        "port": 8001,
        "redis": redis_status
    }