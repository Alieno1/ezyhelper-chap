"""EzyHelpers CHAP (Customer Helper Admin Platform) - Core FastAPI Gateway.

Exposes high-throughput REST APIs for:
1. Candidate Lifecycle & Sourcing Funnel execution (Autopilot vs Manual).
2. Helper CRM Directory & WhatsApp Conversational Audit Logs.
3. Government Identity Verification (Digio UIDAI KYC with Aadhaar Masking).
4. Field Officer (FO Client) Bangalore Geo-Docketing & Routing.
5. Algorithmic Customer Propensity Matching Engine (0-100% score).
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

import agents
from database import ACTIVE_URL, Base, engine, get_db
from models import Helper, SourcingCampaign, WhatsAppLog
from schemas import (
    CampaignOut,
    CustomerRequirement,
    HelperOut,
    MatchResult,
    PipelineResult,
    WhatsAppOut,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan context.
    
    Ensures all PostgreSQL / SQLite tables and relational indices
    are created before accepting incoming HTTP requests.
    """
    Base.metadata.create_all(engine)
    yield


# Initialize FastAPI application with Swagger metadata
app = FastAPI(
    title="EzyHelpers CHAP API",
    description="Agentic Supply Sourcing, LLM Extraction, WhatsApp Lifecycle, Digio KYC & FO Routing Engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) setup for Next.js frontend
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=origins != ["*"],
)


def _helper_or_404(db: Session, helper_id: str) -> Helper:
    """Helper lookup utility.
    
    Retrieves a helper record by helper_id (e.g. HLPRIN52445) or raises HTTP 404.
    """
    h = db.scalar(select(Helper).where(Helper.helper_id == helper_id))
    if not h:
        raise HTTPException(status_code=404, detail=f"Helper {helper_id} not found")
    return h


# ---------------------------------------------------------------------------
# 1. System Health & Observability Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", summary="System Health & Cloud Diagnostics")
def health():
    """Returns database status (Neon PostgreSQL vs SQLite) and LLM engine readiness."""
    return {
        "status": "ok",
        "database": "postgresql" if "postgres" in ACTIVE_URL else "sqlite",
        "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENROUTER_API_KEY")),
    }


# ---------------------------------------------------------------------------
# 2. Candidate Directory & WhatsApp CRM Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/helpers", response_model=list[HelperOut], summary="List All Candidate Helpers")
def list_helpers(db: Session = Depends(get_db)):
    """Returns all registered helpers sorted by creation timestamp."""
    return db.scalars(select(Helper).order_by(Helper.created_at, Helper.helper_id)).all()


@app.get("/api/helpers/{helper_id}", response_model=HelperOut, summary="Get Single Helper Profile")
def get_helper(helper_id: str, db: Session = Depends(get_db)):
    """Fetches complete 5-step profile details for a candidate."""
    return _helper_or_404(db, helper_id)


@app.get("/api/helpers/{helper_id}/whatsapp", response_model=list[WhatsAppOut], summary="WhatsApp Audit Trail")
def whatsapp(helper_id: str, db: Session = Depends(get_db)):
    """Returns the conversational WhatsApp audit trail between candidate and bot."""
    _helper_or_404(db, helper_id)
    return db.scalars(
        select(WhatsAppLog)
        .where(WhatsAppLog.helper_id == helper_id)
        .order_by(WhatsAppLog.id)
    ).all()


@app.get("/api/campaign", response_model=CampaignOut | None, summary="Current CAC Funnel Metrics")
def campaign(db: Session = Depends(get_db)):
    """Returns the active sourcing campaign metrics (₹2,000 spend -> ₹1,000 final CAC)."""
    return db.scalar(select(SourcingCampaign).order_by(SourcingCampaign.id.desc()))


# ---------------------------------------------------------------------------
# 3. Autonomous Agentic Pipeline Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/agent/run-sourcing-pipeline", response_model=PipelineResult, summary="Execute Sourcing Funnel")
def run_pipeline(autopilot: bool = False, db: Session = Depends(get_db)):
    """Executes the autonomous recruitment pipeline.
    
    Parameters:
    - autopilot=True: Executes all 6 stages autonomously (Intake -> AI -> WhatsApp -> KYC -> FO Dispatch).
    - autopilot=False: Executes first 4 stages, creating 80% profiles for manual recruiter verification.
    """
    return agents.run_pipeline(db, autopilot=autopilot)


@app.post("/api/agent/verify-kyc/{helper_id}", response_model=HelperOut, summary="Verify Aadhaar Identity via Digio")
def verify_kyc(helper_id: str, db: Session = Depends(get_db)):
    """Simulates Digio UIDAI OKYC verification, applies Aadhaar masking, and stamps Blue Tick."""
    return agents.verify_kyc(db, _helper_or_404(db, helper_id))


@app.post("/api/agent/assign-field-officer/{helper_id}", response_model=HelperOut, summary="Dispatch Field Officer Client")
def assign_fo(helper_id: str, db: Session = Depends(get_db)):
    """Validates Bangalore residence and dockets candidate to Field Officer Client for home inspection."""
    h = _helper_or_404(db, helper_id)
    if h.base_city != "Bangalore":
        raise HTTPException(status_code=400, detail="Field Officer Client only covers Bangalore helpers")
    return agents.assign_fo(db, h)


@app.post("/api/agent/match-customer", response_model=list[MatchResult], summary="Propensity Matcher Algorithm")
def match_customer(req: CustomerRequirement, db: Session = Depends(get_db)):
    """Scores all verified helpers against customer requirements on a 0-100% scale."""
    return agents.match_customer(db, req)
