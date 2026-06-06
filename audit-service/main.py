from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import SessionLocal, AccessLog, init_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ZTNA Audit Service")


# Dashboard ko allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():   #server start hote hi run hoga
    init_db()

class LogRequest(BaseModel):   #model
    email:      Optional[str] = "anonymous"
    role:       Optional[str] = "unknown"
    path:       str
    device_id:  Optional[str] = "unknown"
    allowed:    bool
    blocked_at: Optional[str] = None
    reason:     Optional[str] = None

# ---------- LOG LIKHNA -----------------
@app.post("/log")
def write_log(req: LogRequest):
    """
    Gateway har request ke baad yahan call karta hai
    Ramesh allowed hua ya hacker blocked —
    dono cases mein PostgreSQL mein record jaata hai
    """
    db = SessionLocal()  #connection open
    try:
        log = AccessLog(
            email      = req.email,
            role       = req.role,
            path       = req.path,
            device_id  = req.device_id,
            allowed    = req.allowed,
            blocked_at = req.blocked_at,
            reason     = req.reason,
            timestamp  = datetime.utcnow()
        )
        db.add(log)
        db.commit()  #BTS sql execute hua INSERT INTO access_logs(...)

        status = "ALLOWED" if req.allowed else " BLOCKED"
        print(f"{status} | {req.email} → {req.path} | {req.reason or 'Access granted'}")

        return {"logged": True}

    except Exception as e:
        db.rollback()
        print(f" Log error: {e}")
        return {"logged": False, "error": str(e)}
    finally:
        db.close()

# ------------- LOGS PADHNA -------------------
@app.get("/logs")
def get_logs(limit: int = 20):
    """
    Dashboard yahan se logs fetch karega
    Latest pehle dikhenge
    """
    db = SessionLocal()
    try:
        #table select
        #newest first
        #limit = 20
        #execute
        logs = db.query(AccessLog)\
                 .order_by(AccessLog.timestamp.desc())\
                 .limit(limit)\
                 .all()

        return [
            {
                "id":         log.id,
                "timestamp":  log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "email":      log.email,
                "role":       log.role,
                "path":       log.path,
                "device_id":  log.device_id,
                "allowed":    log.allowed,
                "blocked_at": log.blocked_at,
                "reason":     log.reason
            }
            for log in logs
        ]
    finally:
        db.close()

# --------------------- STATS -------------------------
@app.get("/stats")
def get_stats():
    """
    Dashboard ke liye:
    Total requests, allowed, blocked, block rate
    """
    db = SessionLocal()
    try:
        total   = db.query(AccessLog).count()
        allowed = db.query(AccessLog)\
                    .filter(AccessLog.allowed == True).count()
        blocked = db.query(AccessLog)\
                    .filter(AccessLog.allowed == False).count()

        return {
            "total_requests": total,
            "allowed":        allowed,
            "blocked":        blocked,
            "block_rate":     f"{(blocked/total*100):.1f}%" if total > 0 else "0%"
        }
    finally:
        db.close()

# ------------------- RECENT BLOCKED ----------------------
@app.get("/blocked")
def get_blocked():
    """
    Sirf blocked requests — 
    Admin dashboard mein red mein dikhenge
    Security alerts ke liye
    """
    db = SessionLocal()
    try:
        logs = db.query(AccessLog)\
                 .filter(AccessLog.allowed == False)\
                 .order_by(AccessLog.timestamp.desc())\
                 .limit(10)\
                 .all()

        return [
            {
                "timestamp":  log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "email":      log.email,
                "path":       log.path,
                "device_id":  log.device_id,
                "blocked_at": log.blocked_at,
                "reason":     log.reason
            }
            for log in logs
        ]
    finally:
        db.close()

@app.get("/health")
def health():
    return {
        "status": "Audit service chal rahi hai!",
        "port":   9999,
        "db":     "PostgreSQL"
    }