import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import (
    auth,
    users,
    customers,
    cases,
    calls,
    followups,
    documents,
    reports,
    audit_logs,
    health,
)
from app.telephony.webhooks import incoming as telephony_incoming

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import create_all_tables

from app.api.routes import (
    auth,
    users,
    customers,
    cases,
    calls,
    followups,
    documents,
    reports,
    audit_logs,
    health,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    logger.info("Starting NileConnect AI Contact Center backend...")

    # Ensure upload directory exists
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    logger.info(f"Upload directory: {os.path.abspath(upload_dir)}")

    # Create database tables
    create_all_tables()
    logger.info("Database tables ready.")

    yield

    logger.info("Backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered Telecom/ISP Contact Center — Phase 1 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(health.router,     prefix=PREFIX, tags=["Health"])
app.include_router(auth.router,       prefix=PREFIX, tags=["Authentication"])
app.include_router(users.router,      prefix=PREFIX, tags=["Users"])
app.include_router(customers.router,  prefix=PREFIX, tags=["Customers"])
app.include_router(cases.router,      prefix=PREFIX, tags=["Cases"])
app.include_router(calls.router,      prefix=PREFIX, tags=["Calls"])
app.include_router(followups.router,  prefix=PREFIX, tags=["Follow-ups"])
app.include_router(documents.router,  prefix=PREFIX, tags=["Documents"])
app.include_router(reports.router,    prefix=PREFIX, tags=["Reports"])
app.include_router(audit_logs.router, prefix=PREFIX, tags=["Audit Logs"])
app.include_router(telephony_incoming.router, prefix=PREFIX, tags=["Telephony"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )
