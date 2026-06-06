from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi.responses import JSONResponse
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

app = FastAPI(title="HR Portal")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def verify_gateway_cert(request: Request, call_next):
    forwarded_by = request.headers.get("X-Forwarded-By")   #it is extra layer only not security, main kaam to nginx kr rha hai

    if request.url.path == "/health":
        return await call_next(request)

    if forwarded_by != "ZTNA-Gateway":
        return JSONResponse(
            status_code=403,
            content={
                "error": "Direct access blocked!",
                "detail": "Only accessible through ZTNA Gateway",
            }
        )

    return await call_next(request)

@app.get("/hr-portal")
def hr_portal(
    x_user_email: Optional[str] = Header(None),
    x_user_role:  Optional[str] = Header(None)
):
    return {
        "service": "HR Portal",
        "message": f"Welcome {x_user_email}!",
        "role":    x_user_role,
        "mtls":    "mTLS verified connection",
        "data": {
            "employees":      150,
            "leaves_pending": 12,
            "payroll_date":   "25th March"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "HR Portal running",
        "port":   9001,
        "mtls":   "enabled"
    }

if __name__ == "__main__":
    config = Config()
    config.bind = ["127.0.0.1:19001"]  #Sirf same machine/container access kar sakta hai. outside world se hr-service accessible nhi
    asyncio.run(serve(app, config))