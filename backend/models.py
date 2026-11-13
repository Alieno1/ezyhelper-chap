import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Helper(Base):
    __tablename__ = "helpers"

    # --- System & CHAP CRM metadata ---
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    helper_id: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    source_platform: Mapped[str] = mapped_column(String(20), default="Apna")  # Apna|WorkIndia|Helper_Referral|Field_Camp
    source_credit_cost_inr: Mapped[float] = mapped_column(Float, default=40.0)
    profile_completion_pct: Mapped[int] = mapped_column(Integer, default=80)
    profile_quality_score: Mapped[int] = mapped_column(Integer, default=40)
    onboarding_stage: Mapped[str] = mapped_column(String(32), default="SCRAPED")
    is_available_for_work: Mapped[bool] = mapped_column(Boolean, default=True)
    available_from_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    referral_code: Mapped[str] = mapped_column(String(6), default="WXWRSH")
    rating_badge: Mapped[str] = mapped_column(String(20), default="New")
    jobs_done_count: Mapped[int] = mapped_column(Integer, default=0)
    total_earnings_inr: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # --- Step 0/1: Basic info ---
    app_language: Mapped[str] = mapped_column(String(12), default="Hinglish")
    first_name: Mapped[str] = mapped_column(String(60))
    middle_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mobile_number: Mapped[str] = mapped_column(String(20), unique=True)
    mobile_verified: Mapped[bool] = mapped_column(Boolean, default=True)
    alt_mobile_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dob: Mapped[str | None] = mapped_column(String(10), nullable=True)  # DD/MM/YYYY
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_type: Mapped[str] = mapped_column(String(12), default="Full Time")  # Live In|Full Time|Part Time
    job_category: Mapped[str] = mapped_column(String(12), default="Regular")  # Regular|On-Demand
    languages_known: Mapped[list] = mapped_column(JSON, default=list)
    job_roles: Mapped[list] = mapped_column(JSON, default=list)
    base_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    base_locality: Mapped[str | None] = mapped_column(String(80), nullable=True)
    base_city: Mapped[str | None] = mapped_column(String(60), nullable=True)
    base_state: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # --- Step 2: Address ---
    citizenship: Mapped[str] = mapped_column(String(10), default="India")
    current_street_house: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    current_city: Mapped[str | None] = mapped_column(String(60), nullable=True)
    current_state: Mapped[str | None] = mapped_column(String(60), nullable=True)
    current_country: Mapped[str] = mapped_column(String(40), default="India")
    is_permanent_same_as_current: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Step 3: Profile ---
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

    # --- Step 4: Skills & shift constraints ---
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

    # --- Step 5: Documents / KYC / FO docket ---
    identity_proof_status: Mapped[str] = mapped_column(String(10), default="Pending")
    address_proof_status: Mapped[str] = mapped_column(String(10), default="Pending")
    kyc_masked_id: Mapped[str] = mapped_column(String(32), default="[Aadhaar Redacted]")
    kyc_blue_tick: Mapped[bool] = mapped_column(Boolean, default=False)
    kyc_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fo_assigned_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fo_verification_status: Mapped[str] = mapped_column(String(16), default="Not_Assigned")
    fo_geo_coordinates: Mapped[str | None] = mapped_column(String(120), nullable=True)
    fo_house_photo_url: Mapped[str | None] = mapped_column(String(200), nullable=True)


class WhatsAppLog(Base):
    __tablename__ = "whatsapp_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    helper_id: Mapped[str] = mapped_column(ForeignKey("helpers.helper_id"), index=True)
    sender: Mapped[str] = mapped_column(String(16))  # AGENT_AISENSY | HELPER
    message_text: Mapped[str] = mapped_column(String(1000))
    quick_reply_chips: Mapped[list] = mapped_column(JSON, default=list)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SourcingCampaign(Base):
    __tablename__ = "sourcing_campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(40), default="Apna + WorkIndia")
    subscription_spend_inr: Mapped[float] = mapped_column(Float, default=2000.0)
    profiles_scraped_count: Mapped[int] = mapped_column(Integer, default=50)
    whatsapp_active_yes_count: Mapped[int] = mapped_column(Integer, default=10)
    job_inquiry_count: Mapped[int] = mapped_column(Integer, default=5)
    bangalore_converted_count: Mapped[int] = mapped_column(Integer, default=2)
    cost_per_raw_lead_inr: Mapped[float] = mapped_column(Float, default=40.0)
    cost_per_active_lead_inr: Mapped[float] = mapped_column(Float, default=200.0)
    final_cac_per_onboarded_helper_inr: Mapped[float] = mapped_column(Float, default=1000.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

