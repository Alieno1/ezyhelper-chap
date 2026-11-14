from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

SourcePlatform = Literal["Apna", "WorkIndia", "Helper_Referral", "Field_Camp"]
Stage = Literal["SCRAPED", "WHATSAPP_PINGED", "ACTIVE_REPLIED_YES", "CV_GENERATED",
                "JOB_INTEREST_CONFIRMED", "KYC_BLUE_TICK", "FO_GEO_VERIFIED"]
WorkType = Literal["Live In", "Full Time", "Part Time"]
JobRole = Literal["Housekeeping", "Cooking", "Elderly Care", "Baby Care", "Physiotherapist"]
DocStatus = Literal["Pending", "Verified"]
FOStatus = Literal["Not_Assigned", "Route_Assigned", "Geo_Verified"]


class HelperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    helper_id: str
    source_platform: SourcePlatform
    source_credit_cost_inr: float
    profile_completion_pct: int = Field(ge=0, le=100)
    profile_quality_score: int = Field(ge=0, le=100)
    onboarding_stage: Stage
    is_available_for_work: bool
    available_from_date: Optional[str] = None
    referral_code: str
    rating_badge: str
    jobs_done_count: int
    total_earnings_inr: float
    created_at: datetime

    app_language: Literal["Hindi", "Hinglish", "English", "Bengali", "Kannada"]
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile_number: str
    mobile_verified: bool
    alt_mobile_number: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[int] = None
    work_type: WorkType
    job_category: Literal["Regular", "On-Demand"]
    languages_known: list[str]
    job_roles: list[JobRole]
    base_pincode: Optional[str] = None
    base_locality: Optional[str] = None
    base_city: Optional[str] = None
    base_state: Optional[str] = None

    citizenship: Literal["India", "Nepal"]
    current_street_house: Optional[str] = None
    current_pincode: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    current_country: str
    is_permanent_same_as_current: bool

    gender: Literal["Female", "Male"]
    email_address: Optional[str] = None
    reference_name: Optional[str] = None
    religion: Optional[str] = None
    experience_years: int
    experience_months: int
    education_level: str
    marital_status: str
    local_commute_type: str
    preferred_localities: list[str]
    nearby_apartments: list[str]
    has_smartphone: bool
    has_whatsapp: bool

    core_skills: list[str]
    min_shift_duration_hours: int
    shift_start_time: Optional[str] = None
    shift_end_time: Optional[str] = None
    break_start_time: Optional[str] = None
    break_end_time: Optional[str] = None
    tasks_dos: list[str]
    tasks_donts: list[str]
    special_preferences: list[str]
    expected_salary_inr: int

    identity_proof_status: DocStatus
    address_proof_status: DocStatus
    kyc_masked_id: str
    kyc_blue_tick: bool
    kyc_verified_at: Optional[datetime] = None
    fo_assigned_name: Optional[str] = None
    fo_verification_status: FOStatus
    fo_geo_coordinates: Optional[str] = None
    fo_house_photo_url: Optional[str] = None


class WhatsAppOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    helper_id: str
    sender: Literal["AGENT_AISENSY", "HELPER"]
    message_text: str
    quick_reply_chips: list[str]
    timestamp: datetime


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    platform: str
    subscription_spend_inr: float
    profiles_scraped_count: int
    whatsapp_active_yes_count: int
    job_inquiry_count: int
    bangalore_converted_count: int
    cost_per_raw_lead_inr: float
    cost_per_active_lead_inr: float
    final_cac_per_onboarded_helper_inr: float


class PipelineStage(BaseModel):
    stage: int
    name: str
    logs: list[str]


class PipelineResult(BaseModel):
    campaign: CampaignOut
    stages: list[PipelineStage]
    helper_ids: list[str]
    parser: str


class CustomerRequirement(BaseModel):
    persona: str = ""
    text: str = Field(min_length=3, description="Free-text customer requirement")
    locality: Optional[str] = None
    roles: list[JobRole] = []
    languages: list[str] = []
    work_type: Optional[WorkType] = None
    budget_inr: Optional[int] = Field(default=None, gt=0, description="Monthly budget in INR (must be positive)")
    must_cook_nonveg: bool = False
    sleep_by_10pm: bool = False
    hygienic: bool = False


class MatchResult(BaseModel):
    helper_id: str
    name: str
    score: int
    pros: list[str]
    tradeoffs: list[str]
    recommendation: str

