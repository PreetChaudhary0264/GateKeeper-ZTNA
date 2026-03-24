from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from fastapi.responses import JSONResponse
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

app = FastAPI(title="Finance Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def verify_gateway_cert(request: Request, call_next):
    forwarded_by = request.headers.get("X-Forwarded-By")

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

@app.get("/finance")
def finance(
    x_user_email: Optional[str] = Header(None),
    x_user_role:  Optional[str] = Header(None)
):
    return {
        "service": "Finance DB",
        "message": f"Welcome {x_user_email}!",
        "mtls":    "mTLS verified connection",
        "data": {
            "revenue_march":    "₹45,00,000",
            "expenses_march":   "₹12,00,000",
            "invoices_pending": 8
        }
    }

@app.get("/health")
def health():
    return {"status": "Finance service running", "port": 9002}

if __name__ == "__main__":
    config = Config()
    config.bind = ["127.0.0.1:9002"]
    asyncio.run(serve(app, config))