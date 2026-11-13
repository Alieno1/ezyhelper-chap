import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

import agents
from database import ACTIVE_URL, Base, engine, get_db
from models import Helper, SourcingCampaign, WhatsAppLog
from schemas import (CampaignOut, CustomerRequirement, HelperOut, MatchResult,
                     PipelineResult, WhatsAppOut)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="EzyHelpers CHAP API", version="1.0.0", lifespan=lifespan)
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"],
                   allow_credentials=origins != ["*"])


def _helper_or_404(db: Session, helper_id: str) -> Helper:
    h = db.scalar(select(Helper).where(Helper.helper_id == helper_id))
    if not h:
        raise HTTPException(404, f"Helper {helper_id} not found")
    return h


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "postgresql" if "postgres" in ACTIVE_URL else "sqlite",
            "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))}


@app.get("/api/helpers", response_model=list[HelperOut])
def list_helpers(db: Session = Depends(get_db)):
    return db.scalars(select(Helper).order_by(Helper.created_at, Helper.helper_id)).all()


@app.get("/api/helpers/{helper_id}", response_model=HelperOut)
def get_helper(helper_id: str, db: Session = Depends(get_db)):
    return _helper_or_404(db, helper_id)


@app.get("/api/helpers/{helper_id}/whatsapp", response_model=list[WhatsAppOut])
def whatsapp(helper_id: str, db: Session = Depends(get_db)):
    _helper_or_404(db, helper_id)
    return db.scalars(select(WhatsAppLog).where(WhatsAppLog.helper_id == helper_id).order_by(WhatsAppLog.id)).all()


@app.get("/api/campaign", response_model=CampaignOut | None)
def campaign(db: Session = Depends(get_db)):
    return db.scalar(select(SourcingCampaign).order_by(SourcingCampaign.id.desc()))


@app.post("/api/agent/run-sourcing-pipeline", response_model=PipelineResult)
def run_pipeline(db: Session = Depends(get_db)):
    return agents.run_pipeline(db)


@app.post("/api/agent/verify-kyc/{helper_id}", response_model=HelperOut)
def verify_kyc(helper_id: str, db: Session = Depends(get_db)):
    return agents.verify_kyc(db, _helper_or_404(db, helper_id))


@app.post("/api/agent/assign-field-officer/{helper_id}", response_model=HelperOut)
def assign_fo(helper_id: str, db: Session = Depends(get_db)):
    h = _helper_or_404(db, helper_id)
    if h.base_city != "Bangalore":
        raise HTTPException(400, "Field Officer Ankit only covers Bangalore helpers")
    return agents.assign_fo(db, h)


@app.post("/api/agent/match-customer", response_model=list[MatchResult])
def match_customer(req: CustomerRequirement, db: Session = Depends(get_db)):
    return agents.match_customer(db, req)

