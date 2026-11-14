"""SQLAlchemy ORM models for EzyHelpers CHAP.

Models:
1. Helper: Complete 5-Step EzyHelpers Partner registration schema (reverse-engineered
   from the Play Store 'Easy Helper Partner' APK) + CHAP verification statuses.
2. WhatsAppLog: Conversational audit trail tracking interactive bot messages and replies.
3. SourcingCampaign: Customer Acquisition Cost (CAC) marketing funnel metrics.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


def _uuid() -> str:
    """Generates a unique UUID4 string for primary keys."""
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    """Returns current UTC timestamp without timezone info for SQLAlchemy compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Helper(Base):
    """Core Domestic Helper model representing an onboarded candidate profile."""
    __tablename__ = "helpers"

    # =========================================================================
    # System & CHAP CRM Metadata
    # =========================================================================
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    helper_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)  # Format: HLPRINxxxxx
    source_platform: Mapped[str] = mapped_column(String(20), default="Apna")     # Apna | WorkIndia | Referral
    source_credit_cost_inr: Mapped[float] = mapped_column(Float, default=40.0)   # ₹40 per raw CV unlocked
    profile_completion_pct: Mapped[int] = mapped_column(Integer, default=80)     # Initial AI extraction = 80%
    profile_quality_score: Mapped[int] = mapped_column(Integer, default=40)      # Quality score (0 to 100)
    onboarding_stage: Mapped[str] = mapped_column(String(32), default="SCRAPED") # SCRAPED -> WHATSAPP -> KYC -> FO
    is_available_for_work: Mapped[bool] = mapped_column(Boolean, default=True)
    available_from_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(6), default="WXWRSH")
    rating_badge: Mapped[str] = mapped_column(String(20), default="New")
    jobs_done_count: Mapped[int] = mapped_column(Integer, default=0)
    total_earnings_inr: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    # =========================================================================
    # Step 1: Basic Identity & Demographics
    # =========================================================================
    app_language: Mapped[str] = mapped_column(String(12), default="Hinglish")
    first_name: Mapped[str] = mapped_column(String(60))
    middle_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mobile_number: Mapped[str] = mapped_column(String(20), unique=True)
    mobile_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    alt_mobile_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(10), nullable=True)  # DD/MM/YYYY
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_type: Mapped[str] = mapped_column(String(12), default="Full Time")  # Live In | Full Time | Part Time
    job_category: Mapped[str] = mapped_column(String(12), default="Regular") # Regular | On-Demand
    languages_known: Mapped[list] = mapped_column(JSON, default=list)        # ['Hindi', 'Bengali', etc.]
    job_roles: Mapped[list] = mapped_column(JSON, default=list)              # ['Cooking', 'Housekeeping']
    base_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    base_locality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_city: Mapped[str | None] = mapped_column(String(60), nullable=True)
    base_state: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # =========================================================================
    # Step 2: Address & Citizenship
    # =========================================================================
    citizenship: Mapped[str] = mapped_column(String(10), default="India")
    current_street_house: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_city: Mapped[str | None] = mapped_column(String(60), nullable=True)
    current_state: Mapped[str | None] = mapped_column(String(60), nullable=True)
    current_country: Mapped[str] = mapped_column(String(40), default="India")
    is_permanent_same_as_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # =========================================================================
    # Step 3: Background & Social Profile
    # =========================================================================
    gender: Mapped[str] = mapped_column(String(10), default="Female")
    email_address: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reference_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    religion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=1)
    experience_months: Mapped[int] = mapped_column(Integer, default=0)
    education_level: Mapped[str] = mapped_column(String(24), default="Primary")
    marital_status: Mapped[str] = mapped_column(String(24), default="Married")
    local_commute_type: Mapped[str] = mapped_column(String(12), default="Bus")
    preferred_localities: Mapped[list] = mapped_column(JSON, default=list)
    nearby_apartments: Mapped[list] = mapped_column(JSON, default=list)
    has_smartphone: Mapped[bool] = mapped_column(Boolean, default=True)
    has_whatsapp: Mapped[bool] = mapped_column(Boolean, default=True)

    # =========================================================================
    # Step 4: Skills & Shift Constraints
    # =========================================================================
    core_skills: Mapped[list] = mapped_column(JSON, default=list)
    min_shift_duration_hours: Mapped[int] = mapped_column(Integer, default=8)
    shift_start_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    shift_end_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    break_start_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    break_end_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tasks_dos: Mapped[list] = mapped_column(JSON, default=list)
    tasks_donts: Mapped[list] = mapped_column(JSON, default=list)
    special_preferences: Mapped[list] = mapped_column(JSON, default=list)
    expected_salary_inr: Mapped[int] = mapped_column(Integer, default=18000)

    # =========================================================================
    # Step 5: Verification, UIDAI Compliance & Field Officer Docket
    # =========================================================================
    identity_proof_status: Mapped[str] = mapped_column(String(10), default="Pending")
    address_proof_status: Mapped[str] = mapped_column(String(10), default="Pending")
    kyc_masked_id: Mapped[str] = mapped_column(String(32), default="[Aadhaar Redacted]") # Strict UIDAI compliance
    kyc_blue_tick: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fo_assigned_name: Mapped[str | None] = mapped_column(String(80), nullable=True)      # e.g. Client (FO - Bangalore South)
    fo_verification_status: Mapped[str] = mapped_column(String(16), default="Not_Assigned")
    fo_geo_coordinates: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fo_house_photo_url: Mapped[str | None] = mapped_column(String(200), nullable=True)


class WhatsAppLog(Base):
    """WhatsApp conversational audit trail tracking messages exchanged with helper."""
    __tablename__ = "whatsapp_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    helper_id: Mapped[str] = mapped_column(ForeignKey("helpers.helper_id"), index=True)
    sender: Mapped[str] = mapped_column(String(16))  # AGENT_AISENSY | HELPER
    message_text: Mapped[str] = mapped_column(String(1000))
    quick_reply_chips: Mapped[list] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class SourcingCampaign(Base):
    """Marketing and recruitment campaign metrics tracking the CAC funnel."""
    __tablename__ = "sourcing_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(40), default="Apna + WorkIndia")
    subscription_spend_inr: Mapped[float] = mapped_column(Float, default=2000.0)      # ₹2,000 credit spend
    profiles_scraped_count: Mapped[int] = mapped_column(Integer, default=50)          # 50 unlocked CVs
    whatsapp_active_yes_count: Mapped[int] = mapped_column(Integer, default=10)       # 10 active replies
    job_inquiry_count: Mapped[int] = mapped_column(Integer, default=5)                # 5 job seekers
    bangalore_converted_count: Mapped[int] = mapped_column(Integer, default=2)        # 2 Bangalore conversions
    cost_per_raw_lead_inr: Mapped[float] = mapped_column(Float, default=40.0)        # ₹2,000 / 50 = ₹40
    cost_per_active_lead_inr: Mapped[float] = mapped_column(Float, default=200.0)     # ₹2,000 / 10 = ₹200
    final_cac_per_onboarded_helper_inr: Mapped[float] = mapped_column(Float, default=1000.0) # ₹2,000 / 2 = ₹1,000
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
