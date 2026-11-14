"""Autonomous Agent Engine for EzyHelpers CHAP.

Modules & Capabilities:
1. Sourcing Simulator: Emulates recruiter dashboard credit packs on Apna & WorkIndia.
2. AI Schema Extraction: Google Gemini LLM / OpenRouter extraction with regex fallback.
3. WhatsApp Conversational Bot: AiSensy deterministic quick-reply chip workflow.
4. Digio UIDAI KYC Verifier: Government identity verification with strict Aadhaar masking.
5. Field Officer Geo-Router: Assigns Bangalore candidates to 'Client (FO - Bangalore South)'.
6. Customer Propensity Matcher: Multi-factor 0-100% compatibility scoring algorithm.
"""

import json
import os
import random
import re
import string
import threading
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import Helper, SourcingCampaign, WhatsAppLog, _utcnow
from schemas import CustomerRequirement, MatchResult

# ---------------------------------------------------------------------------
# Locality & Pin Code Geospatial Reference Matrix
# Mapping: locality -> (pincode, city, state, FO geo cluster)
# ---------------------------------------------------------------------------
LOCALITIES = {
    "sarjapur road": ("560102", "Bangalore", "Karnataka", "12.9081° N, 77.6476° E (Bannerghatta / Sarjapur Cluster)"),
    "bannerghatta road": ("560076", "Bangalore", "Karnataka", "12.9121° N, 77.6446° E (Bannerghatta / Sarjapur Cluster)"),
    "hsr layout": ("560102", "Bangalore", "Karnataka", "12.9116° N, 77.6389° E (HSR / Bellandur Cluster)"),
    "whitefield": ("560066", "Bangalore", "Karnataka", "12.9698° N, 77.7500° E (Whitefield Cluster)"),
    "koramangala": ("560034", "Bangalore", "Karnataka", "12.9352° N, 77.6245° E (Koramangala Cluster)"),
    "salt lake": ("700091", "Kolkata", "West Bengal", ""),
    "patia": ("751024", "Bhubaneswar", "Odisha", ""),
    "dwarka": ("110075", "Delhi", "Delhi", ""),
}

# ---------------------------------------------------------------------------
# Curated Candidate Bios (Sampled from 50 Unlocked Recruiter Contacts)
# Intentionally messy to demonstrate the LLM's parsing robustness
# ---------------------------------------------------------------------------
RAW_PROFILES = [
    ("Apna", "rita das, 34 yrs female, bengali cook + housekeeping, 8 yr exp, hsr layout bangalore, bangla hindi english, "
             "full time, salary 24000, fish curry non veg ok, sleeps by 10pm, hygienic, sunday off, graduate, married, cycle, +91 9000010001"),
    ("WorkIndia", "sunita devi 29 f housekeeping n cooking 5 saal exp sarjapur road bangalore hindi kannada part time "
                  "sal 16000 pure veg only no non-veg, jhadu pocha, utensils, 10th pass, auto, +91 9000010002"),
    ("Apna", "mousumi roy 41 female baby care nanny 10 yrs kolkata salt lake bengali hindi live in salary 20000 "
             "infant massage baby feeding, widowed, bus, will relocate? maybe, +91 9000010003"),
    ("WorkIndia", "bimala nayak 38 f elderly care patient care 7 years patia bhubaneswar odia hindi full time 22000 "
                  "diabetic diet, hygienic, post graduate, +91 9000010004"),
    ("Apna", "kavita sharma 31 female cooking housekeeping 6 yr dwarka delhi hindi english full time 21000 "
             "north indian cooking roti sabzi, non veg cooking ok, single, +91 9000010005"),
    ("Apna", "lakshmi gowda 27 f baby care 4 yrs whitefield bangalore kannada hindi english full time 25000 "
             "infant massage baby feeding, sleep by 10 pm, hygienic, 2 wheeler, graduate, +91 9000010006"),
    ("WorkIndia", "dr. anil kumar 36 male physiotherapist elderly care 9 yrs bannerghatta road bangalore hindi english kannada "
                  "part time 35000 muscle strengthening therapeutic exercise, post graduate, 2 wheeler, +91 9000010007"),
    ("Apna", "farida begum 44 female cooking 12 yr koramangala bangalore hindi urdu english full time 23000 "
             "biryani non veg cooking ok, hygienic, secondary, bus, +91 9000010008"),
    ("WorkIndia", "meena kumari 33 f housekeeping 3 yrs sarjapur road bangalore hindi bengali part time 15000 "
                  "deep cleaning bathroom, jhadu pocha, walking, +91 9000010009"),
    ("Apna", "shanti bai 52 female elderly care patient care 15 yrs hsr layout bangalore kannada hindi live in 30000 "
             "sunday off, hygienic, sleep by 10pm, senior secondary, bus, +91 9000010010"),
]

# Keyword dictionaries for domain token matching (supports spaced, hyphenated, and unspaced variants)
ROLE_KEYS = {
    "Housekeeping": ["housekeeping", "house keeping", "housekeeper", "cleaning", "cleaner", "jhadu", "pocha", "maid", "safai", "utensil", "bartan", "ghar ka kaam"],
    "Cooking": ["cook", "cooking", "chef", "biryani", "roti", "khana", "rasoi", "meal", "kitchen", "bawarchi"],
    "Elderly Care": ["elderly", "eldercare", "elderlycare", "patient care", "patientcare", "senior", "old age", "oldage", "parent", "caretaker", "caregiver", "attendant", "bujurg"],
    "Baby Care": ["baby", "babycare", "nanny", "infant", "newborn", "child", "childcare", "kid", "japa", "japamaid", "babysitter", "ayah", "baccha"],
    "Physiotherapist": ["physio", "physiotherapist", "physiotherapy", "rehab", "therapy", "stroke", "paralysis"],
}
LANG_KEYS = {
    "Hindi": ["hindi", "bihari", "bhojpuri", "maithili", "north indian", "northindian", "marwari", "punjabi", "haryanvi", "rajasthani", "up family", "hinglish"],
    "English": ["english", "eng"],
    "Bengali": ["bengali", "bangla", "bangali", "kolkata", "bong"],
    "Kannada": ["kannada", "kannad", "kannadiga", "local language"],
    "Odia": ["odia", "oriya", "odisha"],
    "Urdu": ["urdu", "muslim"],
}
LOCALITY_ALIASES = {
    "sarjapur road": ["sarjapur road", "sarjapurroad", "sarjapur", "sarjapura"],
    "bannerghatta road": ["bannerghatta road", "bannerghattaroad", "bannerghatta", "bg road", "bgroad"],
    "hsr layout": ["hsr layout", "hsrlayout", "h s r layout", "hsr"],
    "whitefield": ["whitefield", "white field", "whitefeild"],
    "koramangala": ["koramangala", "kormangala", "koramangla"],
    "salt lake": ["salt lake", "saltlake"],
    "patia": ["patia"],
    "dwarka": ["dwarka"],
}
EDU_KEYS = [
    ("post graduate", "Post Graduate"),
    ("graduate", "Graduate"),
    ("senior secondary", "Senior Secondary"),
    ("secondary", "Secondary"),
    ("10th", "Secondary"),
    ("primary", "Primary"),
]
COMMUTE_KEYS = [
    ("2 wheeler", "2 Wheeler"),
    ("cycle", "Cycle"),
    ("auto", "Auto"),
    ("walking", "Walking"),
    ("bus", "Bus"),
]
SKILL_KEYS = {
    "north indian cooking": "North Indian Cooking",
    "fish curry": "Bengali Fish Curry",
    "biryani": "Biryani & Non-Veg Cooking",
    "utensils": "Utensil Cleaning",
    "infant massage": "Infant Massage",
    "muscle strengthening": "Muscle Strengthening & Therapeutic Exercise",
    "diabetic diet": "Diabetic Diet Care",
    "deep cleaning": "Deep Cleaning",
    "baby feeding": "Baby Feeding",
}
DO_KEYS = {
    "jhadu": "Jhadu-Pocha",
    "roti": "Roti & Sabzi",
    "baby feeding": "Baby Feeding",
    "utensils": "Utensil Cleaning",
    "patient care": "Patient Care",
    "cook": "Daily Cooking",
}


def _chance_code() -> str:
    """Generates an alphanumeric 6-character partner referral code."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _has(text: str, words: list[str]) -> bool:
    """Returns True if any keyword exists in spaced or unspaced normalized text."""
    compact = re.sub(r"[^a-z0-9]+", "", text.lower())
    norm = re.sub(r"[^a-z0-9]+", " ", text.lower())
    for w in words:
        wl = w.lower()
        w_compact = re.sub(r"[^a-z0-9]+", "", wl)
        if wl in norm or wl in text.lower() or (len(w_compact) >= 3 and w_compact in compact):
            return True
    return False


def _format_locality(loc: str | None) -> str | None:
    """Normalizes locality display casing (e.g., 'HSR Layout' vs Title Case)."""
    if not loc:
        return None
    clean = loc.strip()
    return "HSR Layout" if clean.lower() in ("hsr layout", "hsrlayout", "hsr") else clean.title()


# ---------------------------------------------------------------------------
# 1. Deterministic Rule-Based Parser (Fallback & Base Extraction)
# ---------------------------------------------------------------------------

def deterministic_parse(raw: str, source: str) -> dict:
    """Extracts candidate profile fields using domain-specific regex and keyword matching.
    
    Serves as the reliable foundational baseline for all candidates.
    """
    t = raw.lower()
    clean = re.sub(r"\+91\s*\d{10}", " ", raw)
    head = re.split(r"[,\d]", clean, maxsplit=1)[0]
    name_parts = [w.capitalize() for w in head.replace(".", " ").split() if w.lower() != "dr"][:3]
    first = name_parts[0] if name_parts else "Helper"
    last = " ".join(name_parts[1:]) or None

    tl = clean.lower()
    age_m = re.search(r"\b(\d{2})\s*(?:yrs\s*)?(?:female|male|f|m)\b", tl)
    age = int(age_m.group(1)) if age_m else None
    rest = tl.replace(age_m.group(0), " ", 1) if age_m else tl

    exp_m = re.search(r"(\d{1,2})\s*(?:yrs?|years?|saal)", rest)
    exp = max(0, min(int(exp_m.group(1)), 11)) if exp_m else 1

    sal_m = re.search(r"\b(\d{5})\b", rest)
    salary = int(sal_m.group(1)) if sal_m else 18000

    phone_m = re.search(r"\+91\s*(\d{10})", raw)
    phone = f"+91 {phone_m.group(1)}" if phone_m else "+91 9000000000"

    locality = next((k for k in LOCALITIES if k in t), None)
    pin, city, state, _ = LOCALITIES.get(locality, (None, "Bangalore", "Karnataka", ""))
    loc_display = _format_locality(locality)

    roles = [r for r, keys in ROLE_KEYS.items() if _has(t, keys)] or ["Housekeeping"]
    if "Physiotherapist" in roles and "Elderly Care" not in roles and "elderly" in t:
        roles.append("Elderly Care")

    langs = [l for l, keys in LANG_KEYS.items() if _has(t, keys)] or ["Hindi"]
    work_type = "Live In" if "live in" in t else "Part Time" if "part time" in t else "Full Time"
    female = "male" not in t.replace("female", "")

    edu = next((v for k, v in EDU_KEYS if k in t), "Primary")
    commute = next((v for k, v in COMMUTE_KEYS if k in t), "Bus")
    marital = "Widowed" if "widowed" in t else "Single" if "single" in t else "Married"

    skills = [v for k, v in SKILL_KEYS.items() if k in t]
    dos = [v for k, v in DO_KEYS.items() if k in t]
    donts = []
    if "no non-veg" in t or "pure veg" in t:
        donts.append("Non-Veg Cooking")
    if "bathroom" not in t:
        donts.append("Bathroom Deep Cleaning")

    prefs = []
    if re.search(r"sleeps? by 10\s?pm", t):
        prefs.append("Sleep by 10:00 PM")
    if "sunday off" in t:
        prefs.append("Sunday Off")
    if "hygienic" in t:
        prefs.append("Hygienic Environment")

    app_lang = "Kannada" if "Kannada" in langs[:1] else "Bengali" if "Bengali" in langs[:1] else "Hinglish"
    dob_year = _utcnow().year - (age or 30)

    return {
        "source_platform": source,
        "app_language": app_lang,
        "citizenship": "India",
        "first_name": first,
        "last_name": last,
        "mobile_number": phone,
        "dob": f"15/06/{dob_year}",
        "age": age,
        "work_type": work_type,
        "languages_known": langs,
        "job_roles": roles,
        "base_pincode": pin,
        "base_locality": loc_display,
        "base_city": city,
        "base_state": state,
        "current_city": city,
        "current_state": state,
        "current_pincode": pin,
        "current_street_house": f"{loc_display} (house details pending)" if loc_display else None,
        "gender": "Female" if female else "Male",
        "experience_years": exp,
        "education_level": edu,
        "marital_status": marital,
        "local_commute_type": commute,
        "preferred_localities": [loc_display] if loc_display else [],
        "core_skills": skills,
        "tasks_dos": dos,
        "tasks_donts": donts,
        "special_preferences": prefs,
        "expected_salary_inr": salary,
        "min_shift_duration_hours": 8 if work_type != "Live In" else 12,
        "shift_start_time": "08:00 AM",
        "shift_end_time": "06:00 PM",
        "break_start_time": "01:00 PM",
        "break_end_time": "02:00 PM",
        "religion": None,
    }


# ---------------------------------------------------------------------------
# 2. Google Gemini / OpenRouter LLM Parser
# ---------------------------------------------------------------------------

def gemini_parse(raw: str, source: str, base: dict) -> tuple[dict, str]:
    """Overlays LLM-extracted structured fields onto the deterministic base.
    
    Uses OpenRouter (Gemini 3.5 Flash) or Google GenAI API with strict JSON schema
    guarantees. Falls back gracefully to deterministic base if keys are not provided.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    or_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key and not or_key:
        return base, "deterministic"

    try:
        prompt = (
            "Extract a JSON object from this messy domestic-helper candidate bio. Use ONLY these keys: "
            + ", ".join(k for k in base if k not in {"mobile_number", "source_platform"})
            + ". job_roles must be from [Housekeeping, Cooking, Elderly Care, Baby Care, Physiotherapist]; "
            "work_type from [Live In, Full Time, Part Time]. Never output any ID numbers. Return JSON only.\n\nBIO: " + raw
        )

        if or_key:
            # OpenRouter API (OpenAI-compatible chat completions)
            import urllib.request
            body = json.dumps({
                "model": os.getenv("OPENROUTER_MODEL", "google/gemini-3.5-flash-lite"),
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "max_tokens": 1200,
            }).encode()
            rq = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=body,
                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(rq, timeout=30) as r:
                text = json.load(r)["choices"][0]["message"]["content"]
            provider = "openrouter"
        else:
            # Native Google Gemini API
            from google import genai
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            text, provider = resp.text, "gemini"

        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        data = json.loads(text)
        merged = dict(base)

        for k, v in data.items():
            if k in base and k not in {"mobile_number", "source_platform"} and v is not None and type(v) is type(base[k]):
                merged[k] = v

        # Normalize schema literal bounds
        if isinstance(merged.get("gender"), str):
            merged["gender"] = merged["gender"].strip().capitalize()
            if merged["gender"] not in ("Female", "Male"):
                merged["gender"] = base.get("gender", "Female")

        if isinstance(merged.get("work_type"), str):
            wt = merged["work_type"].strip().title()
            merged["work_type"] = wt if wt in ("Live In", "Full Time", "Part Time") else base.get("work_type", "Full Time")

        if isinstance(merged.get("citizenship"), str):
            c = merged["citizenship"].strip().title()
            merged["citizenship"] = c if c in ("India", "Nepal") else "India"

        if isinstance(merged.get("app_language"), str):
            al = merged["app_language"].strip().title()
            merged["app_language"] = al if al in ("Hindi", "Hinglish", "English", "Bengali", "Kannada") else base.get("app_language", "Hinglish")

        if isinstance(merged.get("job_roles"), list):
            valid_roles = {"Housekeeping", "Cooking", "Elderly Care", "Baby Care", "Physiotherapist"}
            clean_roles = [r.title() for r in merged["job_roles"] if isinstance(r, str) and r.title() in valid_roles]
            merged["job_roles"] = clean_roles or base.get("job_roles", ["Housekeeping"])

        # Preserve canonical deterministic tags for preferences, tasks, skills, and languages
        lang_map = {"bangla": "Bengali", "oriya": "Odia"}
        if isinstance(merged.get("languages_known"), list):
            norm_langs = list(dict.fromkeys(
                list(base.get("languages_known", []))
                + [lang_map.get(x.strip().lower(), x.strip().title()) for x in merged["languages_known"] if isinstance(x, str) and x.strip()]
            ))
            merged["languages_known"] = norm_langs or base.get("languages_known", ["Hindi"])

        for canonical_list_field in ("special_preferences", "tasks_donts", "tasks_dos", "core_skills"):
            merged[canonical_list_field] = list(base.get(canonical_list_field, []))

        # Normalize casing on names, cities, states, and localities returned by LLMs
        for title_field in ("first_name", "last_name", "base_locality", "base_state", "current_state",
                            "education_level", "marital_status", "local_commute_type"):
            val = merged.get(title_field)
            if isinstance(val, str) and val.strip():
                merged[title_field] = _format_locality(val) if title_field == "base_locality" else val.strip().title()

        for city_field in ("base_city", "current_city"):
            val = merged.get(city_field)
            if isinstance(val, str) and val.strip():
                c_norm = val.strip().title()
                merged[city_field] = "Bangalore" if c_norm in ("Bangalore", "Bengaluru") else c_norm

        if merged.get("base_locality"):
            merged["preferred_localities"] = [merged["base_locality"]]

        return merged, provider

    except Exception as exc:  # noqa: BLE001
        print(f"[gemini] fallback to deterministic parser: {exc.__class__.__name__}")
        return base, "deterministic"


# ---------------------------------------------------------------------------
# 3. Helpers & WhatsApp Pipeline Utilities
# ---------------------------------------------------------------------------

def _new_helper_id(db: Session, used: set[str]) -> str:
    """Generates a non-colliding official helper partner ID (Format: HLPRINxxxxx)."""
    while True:
        hid = f"HLPRIN{random.randint(10000, 99999)}"
        if hid not in used and not db.scalar(select(Helper.id).where(Helper.helper_id == hid)):
            used.add(hid)
            return hid


def _wa(db: Session, hid: str, sender: str, text: str, chips: list[str] | None = None):
    """Logs a bidirectional WhatsApp chat interaction in the database."""
    db.add(WhatsAppLog(helper_id=hid, sender=sender, message_text=text, quick_reply_chips=chips or []))


# ---------------------------------------------------------------------------
# 4. Multi-Stage Pipeline Execution (Autopilot vs Manual)
# ---------------------------------------------------------------------------

# Serializes pipeline runs: concurrent runs would otherwise wipe/update the same rows
# at the same time (StaleDataError). Overlapping requests now queue instead of failing.
_PIPELINE_LOCK = threading.Lock()


def run_pipeline(db: Session, autopilot: bool = False) -> dict:
    """Thread-safe entry point: only one pipeline run executes at a time."""
    with _PIPELINE_LOCK:
        db.expire_all()
        return _run_pipeline(db, autopilot)


def _run_pipeline(db: Session, autopilot: bool = False) -> dict:
    """Executes the recruitment funnel.
    
    Stages:
    1. Talent Hunting: Ingests 50 raw recruiter contacts from Apna/WorkIndia (₹2,000 spend).
    2. LLM Extraction: Parses raw candidate bios into 80% complete EzyHelpers partner schema.
    3. WhatsApp Ping: Dispatches automated qualification message + Free Digital Resume link.
    4. Funnel Filtering: Calculates active conversion metrics (₹1,000 CAC).
    5. (If Autopilot): Executes Digio UIDAI KYC verification with Blue Tick.
    6. (If Autopilot): Geo-routes Bangalore helpers to Field Officer Client.
    """
    # Clean previous demo run data
    db.execute(delete(WhatsAppLog))
    db.execute(delete(Helper))
    db.execute(delete(SourcingCampaign))
    db.flush()

    random.seed(7)
    stages = []

    # Stage 1: Sourcing Intake
    stages.append({
        "stage": 1,
        "name": "Talent Hunting (Apna + WorkIndia)",
        "logs": [
            "Logging into Apna recruiter dashboard (simulated session)...",
            "Logging into WorkIndia recruiter dashboard (simulated session)...",
            "Purchasing ₹2,000 credit pack → 50 contact unlocks (₹40/contact)",
            "Filtering for roles: Housekeeping, Cooking, Baby Care, Elderly Care, Physiotherapist",
            "Unlocked 50 raw candidate contacts",
        ],
    })

    # Stage 2: AI Parsing & Partner Schema Creation
    helpers, parser_used, used = [], "deterministic", set()
    logs2 = ["Sending 10 shortlisted raw bios through the schema-extraction agent..."]
    for i, (src, raw) in enumerate(RAW_PROFILES):
        base = deterministic_parse(raw, src)
        data, parser_used_i = gemini_parse(raw, src, base)
        if parser_used_i != "deterministic":
            parser_used = parser_used_i

        hid = _new_helper_id(db, used)
        h = Helper(
            helper_id=hid,
            source_credit_cost_inr=40.0,
            profile_completion_pct=80,
            profile_quality_score=45 + (i % 4) * 3,
            referral_code="WXWRSH" if i == 0 else _chance_code(),
            onboarding_stage="SCRAPED",
            **data,
        )
        db.add(h)
        helpers.append(h)
        logs2.append(f"{hid}: {h.first_name} {h.last_name or ''} → {', '.join(h.job_roles)} @ {h.base_locality or h.base_city} (80% complete)")

    db.flush()
    stages.append({"stage": 2, "name": "LLM Schema Extraction & CHAP Replica Creation", "logs": logs2})

    # Stage 3: WhatsApp Conversational Bot Flow
    logs3 = []
    for h in helpers:
        first = h.first_name
        _wa(
            db,
            h.helper_id,
            "AGENT_AISENSY",
            f"Namaste Didi! 🙏 Main Rita bol rahi hoon EzyHelpers se. Hume Apna app se aapka profile mila. Kya aap abhi ghar ke kaam "
            f"(Cooking / Housekeeping / Baby Care) ki acchi naukri dhundh rahi hain? Niche YES button dabayein!",
            ["Yes, मुझे नौकरी चाहिए", "No"],
        )
        h.onboarding_stage = "WHATSAPP_PINGED"
        _wa(db, h.helper_id, "HELPER", "Yes, मुझे नौकरी चाहिए")
        h.onboarding_stage = "ACTIVE_REPLIED_YES"
        _wa(
            db,
            h.helper_id,
            "AGENT_AISENSY",
            f"Congratulations Didi! 🎉 Aapka EzyHelpers Partner profile (80%) aur aapka FREE Digital Resume taiyar hai! "
            f"App link: https://ezyhelpers.com/app/{h.helper_id} Kya aap Bangalore mein kaam karne ke liye available hain?",
            ["Yes, Bangalore mein available", "No, doosre sheher mein", "Send My Free CV"],
        )
        h.onboarding_stage = "CV_GENERATED"
        logs3.append(f"{h.helper_id} ({first}): ping → YES → Free Digital CV dispatched")

    stages.append({"stage": 3, "name": "AiSensy WhatsApp Deterministic Ping", "logs": logs3})

    # Stage 4: Conversion & CAC Funnel Calculation
    logs4 = []
    for idx, h in enumerate(helpers):
        if idx < 5:
            h.onboarding_stage = "JOB_INTEREST_CONFIRMED"
            if h.base_city == "Bangalore":
                _wa(db, h.helper_id, "HELPER", "Yes, Bangalore mein available")
                _wa(db, h.helper_id, "AGENT_AISENSY", "Shukriya! Hamari team jald hi aapse sampark karegi. 🙏", ["Verify KYC"])
                logs4.append(f"{h.helper_id}: job seeker, Bangalore CONFIRMED ✅ (converted)")
            else:
                _wa(db, h.helper_id, "HELPER", f"No, mujhe {h.base_city} mein kaam chahiye")
                logs4.append(f"{h.helper_id}: job seeker, prefers {h.base_city} (not a Bangalore conversion)")
        else:
            h.is_available_for_work = True
            h.available_from_date = "2026-12-01"

    camp = SourcingCampaign(platform="Apna + WorkIndia", subscription_spend_inr=2000.0)
    camp.profiles_scraped_count, camp.whatsapp_active_yes_count = 50, 10
    camp.job_inquiry_count, camp.bangalore_converted_count = 5, 2
    camp.cost_per_raw_lead_inr = camp.subscription_spend_inr / camp.profiles_scraped_count
    camp.cost_per_active_lead_inr = camp.subscription_spend_inr / camp.whatsapp_active_yes_count
    camp.final_cac_per_onboarded_helper_inr = camp.subscription_spend_inr / camp.bangalore_converted_count
    db.add(camp)

    logs4 += [
        "Funnel: ₹2,000 → 50 scraped → 10 active on WhatsApp → 5 job seekers → 2 Bangalore conversions",
        "Final CAC = ₹1,000 per onboarded helper",
    ]
    stages.append({"stage": 4, "name": "Funnel Filtering", "logs": logs4})

    # Stage 5 & 6: Autopilot Execution (KYC & Field Officer Dispatch)
    if autopilot:
        logs5 = []
        for h in helpers:
            verify_kyc(db, h)
            logs5.append(f"{h.helper_id} ({h.first_name}): Consent received via WhatsApp → Blue Tick awarded ✅ (Quality {h.profile_quality_score}/100)")
        stages.append({"stage": 5, "name": "Autonomous Digio KYC & Consent Verification", "logs": logs5})

        logs6 = []
        for h in helpers:
            if h.base_city == "Bangalore":
                assign_fo(db, h)
                logs6.append(f"{h.helper_id} ({h.first_name} @ {h.base_locality}): FO Client auto-dispatched → Geo verified → 100% Customer Docket Ready 🏠")
            else:
                logs6.append(f"{h.helper_id} ({h.first_name} @ {h.base_city}): Flagged for future Tier-2/regional expansion hub")
        stages.append({"stage": 6, "name": "Autonomous Field Officer Geo-Router & Docket Creation", "logs": logs6})

    db.commit()
    db.refresh(camp)
    return {
        "campaign": camp,
        "stages": stages,
        "helper_ids": [h.helper_id for h in helpers],
        "parser": parser_used,
    }


# ---------------------------------------------------------------------------
# 5. Government Identity Verification (Digio UIDAI OKYC)
# ---------------------------------------------------------------------------

def verify_kyc(db: Session, h: Helper) -> Helper:
    """Simulates Digio Government Aadhaar KYC verification.
    
    Obtains candidate consent, queries UIDAI OKYC records, redacts raw Aadhaar
    numbers into '[Aadhaar Redacted]' for privacy compliance, and stamps Blue Tick.
    """
    _wa(
        db,
        h.helper_id,
        "AGENT_AISENSY",
        "Didi, aapki pehchaan verify karne ke liye hume aapki consent chahiye (Digio / UIDAI). Kya aap sahmat hain?",
        ["Haan, sahmat hoon"],
    )
    _wa(db, h.helper_id, "HELPER", "Haan, sahmat hoon")

    h.kyc_masked_id = "[Aadhaar Redacted]"
    h.identity_proof_status = h.address_proof_status = "Verified"
    h.kyc_blue_tick = True
    h.kyc_verified_at = _utcnow()
    h.profile_completion_pct = max(h.profile_completion_pct, 95)
    h.profile_quality_score = min(100, h.profile_quality_score + 25)

    if h.onboarding_stage != "FO_GEO_VERIFIED":
        h.onboarding_stage = "KYC_BLUE_TICK"

    _wa(db, h.helper_id, "AGENT_AISENSY", "Badhai ho! ✅ Aapka Blue Tick KYC verification poora ho gaya.")
    db.commit()
    return h


# ---------------------------------------------------------------------------
# 6. Field Officer Bangalore Geo-Routing & Docket Creation
# ---------------------------------------------------------------------------

def assign_fo(db: Session, h: Helper) -> Helper:
    """Dispatches Field Officer Client to candidate's Bangalore residence.
    
    Captures geo-coordinates, performs in-person address verification, and promotes
    the profile completion to 100% (Customer Ready Docket).
    """
    loc = (h.base_locality or "").lower()
    geo = LOCALITIES.get(loc, ("", "", "", ""))[3]

    h.fo_assigned_name = "Client (FO - Bangalore South)"
    h.fo_verification_status = "Geo_Verified"
    h.fo_geo_coordinates = geo or "12.9081° N, 77.6476° E (Bannerghatta / Sarjapur Cluster)"
    h.fo_house_photo_url = f"mock://fo-verified-house/{h.helper_id}.jpg"
    h.profile_completion_pct = 100
    h.profile_quality_score = 98
    h.onboarding_stage = "FO_GEO_VERIFIED"

    _wa(db, h.helper_id, "AGENT_AISENSY", "Field Officer Client ne aapke ghar ka geo-verification poora kar liya hai. Customer Docket ready hai! 🏠")
    db.commit()
    return h


# ---------------------------------------------------------------------------
# 7. Customer Propensity Matching Engine (0-100% Score)
# ---------------------------------------------------------------------------

def _smart_extract_locality(text: str, explicit_loc: str | None = None) -> str:
    """Finds canonical locality from spaced, hyphenated, or unspaced text."""
    if explicit_loc:
        el = explicit_loc.strip().lower()
        for canon, aliases in LOCALITY_ALIASES.items():
            if el == canon or any(a in el for a in aliases):
                return canon
        return el
    compact = re.sub(r"[^a-z0-9]+", "", text.lower())
    norm = re.sub(r"[^a-z0-9]+", " ", text.lower())
    for canon, aliases in LOCALITY_ALIASES.items():
        for alias in aliases:
            ac = re.sub(r"[^a-z0-9]+", "", alias)
            if alias in norm or (len(ac) >= 3 and ac in compact):
                return canon
    return ""


def _smart_extract_work_type(text: str, explicit_wt: str | None = None) -> str | None:
    """Detects Live In, Full Time, or Part Time regardless of spaces, hyphens, or casing."""
    if explicit_wt in ("Live In", "Full Time", "Part Time"):
        return explicit_wt
    compact = re.sub(r"[^a-z0-9]+", "", text.lower())
    if any(k in compact for k in ("livein", "24hr", "24x7", "247", "stayin", "24hour")):
        return "Live In"
    if any(k in compact for k in ("parttime", "halfday")):
        return "Part Time"
    if any(k in compact for k in ("fulltime", "fullday", "dayshift", "8hr", "9hr", "10hr", "12hr")):
        return "Full Time"
    return None


def _smart_extract_budget(text: str, explicit_budget: int | None = None) -> int | None:
    """Extracts salary budget from spaced/unspaced text including 'k' shorthand (e.g., 35k, budget35000, ₹22,000)."""
    if explicit_budget is not None:
        return explicit_budget
    tl = text.lower()
    # Check 'k' shorthand first: e.g., '25k', '₹35k', 'budget 22k', 'budget25k'
    mk = re.search(r"(?:budget|salary|₹|rs\.?|inr|under|upto)?\s*\b(\d{2})\s*k\b", tl)
    if mk:
        return int(mk.group(1)) * 1000
    # Check explicit currency/budget prefix with or without spaces: 'budget35000', '₹ 22,000', 'rs.24000'
    m = re.search(r"(?:budget|salary|sal|₹|rs\.?|inr|under|upto)\s*[:=-]?\s*₹?\s*([\d,]{4,7})", tl)
    if m:
        val = int(m.group(1).replace(",", ""))
        if val > 0:
            return val
    # Fallback: standalone 5-digit salary number in text (e.g., 15000 to 99000)
    m_bare = re.search(r"\b([1-9]\d,\d{3}|[1-9]\d{4})\b", tl)
    if m_bare:
        return int(m_bare.group(1).replace(",", ""))
    return None


def _helper_refuses_nonveg(h: Helper) -> bool:
    """Checks if helper is Pure Veg / refuses non-veg across canonical or LLM-generated tags."""
    donts_str = " ".join(h.tasks_donts or []).lower()
    return "non-veg" in donts_str or "non veg" in donts_str or "pure veg" in donts_str or "meat" in donts_str or "fish" in donts_str


def _helper_sleeps_by_10pm(h: Helper) -> bool:
    """Checks if helper has a 10 PM sleep preference across canonical or LLM-generated tags."""
    prefs_str = " ".join(h.special_preferences or []).lower()
    return "10:00 pm" in prefs_str or "10 pm" in prefs_str or "10pm" in prefs_str


def _helper_is_hygienic(h: Helper) -> bool:
    """Checks if helper has verified hygiene preference across canonical or LLM-generated tags."""
    prefs_str = " ".join(h.special_preferences or []).lower()
    return "hygien" in prefs_str or "clean" in prefs_str


def match_customer(db: Session, req: CustomerRequirement) -> list[MatchResult]:
    """Matches verified candidates to customer requests using multi-factor scoring.
    
    Smart NLP features:
    - Tolerates missing spaces ('fulltimecookhousekeeping', 'hsrlayout', 'budget35000')
    - Tolerates any casing ('UPPERCASE', 'lowercase', 'MiXeD') and hyphens ('Full-Time')
    - Maps regional family terms ('Bihari', 'North Indian', 'Marwari' -> Hindi; 'Bangali' -> Bengali)
    - Distinguishes 'pure veg / no non-veg' from 'must cook fish/non-veg'
    - Handles flexible sleep schedules ('sleep by 10 PM' vs 'sleep by 12 AM')
    """
    text = req.text.lower()
    compact = re.sub(r"[^a-z0-9]+", "", text)

    roles = set(req.roles) or {r for r, k in ROLE_KEYS.items() if _has(text, k)}
    langs = set(req.languages) or {l for l, k in LANG_KEYS.items() if _has(text, k)}
    loc = _smart_extract_locality(text, req.locality)
    wt = _smart_extract_work_type(text, req.work_type)
    budget = _smart_extract_budget(text, req.budget_inr)

    # Smart dietary detection: check for pure-veg / negation before non-veg
    wants_pure_veg = bool(
        re.search(r"no\s*non[- ]?veg|without\s*non[- ]?veg|pure[- ]?veg|veg\s*only|strictly\s*veg|no\s*(?:meat|fish)", text)
        or any(k in compact for k in ("nononveg", "pureveg", "vegonly", "strictlyveg"))
    )
    nonveg = req.must_cook_nonveg or (
        not wants_pure_veg
        and (
            bool(re.search(r"non[- ]?veg|fish|chicken|mutton|meat|biryani|egg|seafood", text))
            or any(k in compact for k in ("nonveg", "fish", "chicken", "mutton", "biryani"))
        )
    )

    # Smart sleep schedule detection (10 PM early sleep vs 11 PM / 12 AM late schedule)
    sleep10 = req.sleep_by_10pm or bool(
        re.search(r"sleep\w*\s*(?:by|at|around)?\s*(?:9|10)\s*(?:pm|p\.m\.?)?", text)
        or any(k in compact for k in ("sleepby10", "sleep10", "sleepsby10", "sleepat10", "10pmsleep"))
    )
    sleep_late = bool(
        re.search(r"sleep\w*\s*(?:by|at|around)?\s*(?:11|12)\s*(?:pm|am)?|midnight", text)
        or any(k in compact for k in ("sleepby11", "sleepby12", "sleep11", "sleep12", "12am", "11pm"))
    )

    # Smart hygiene detection (including common typos like 'hygenic', 'hygene')
    hyg = req.hygienic or any(k in compact for k in ("hygien", "hygenic", "hygene", "neatandclean", "saaf"))

    out = []
    for h in db.scalars(select(Helper).where(Helper.is_available_for_work.is_(True))):
        score, pros, trade = 0.0, [], []

        # 1. Job Role Overlap (30 points)
        w_role = 30
        if roles:
            hit = roles & set(h.job_roles)
            score += w_role * len(hit) / len(roles)
            if hit:
                pros.append(f"✅ Does {', '.join(sorted(hit))}")
            if roles - hit:
                trade.append(f"⚠️ Does not do {', '.join(sorted(roles - hit))}")
        else:
            score += w_role * 0.5

        # 2. Languages Known (15 points)
        if langs:
            helper_langs = {lg.title() for lg in (h.languages_known or [])}
            hit = langs & helper_langs
            score += 15 * len(hit) / len(langs)
            if hit:
                pros.append(f"✅ Speaks {'/'.join(sorted(hit))}")
            else:
                trade.append("⚠️ No common language")
        else:
            score += 7.5

        # 3. Location Proximity (15 points)
        if loc and (h.base_locality or "").lower() == loc:
            score += 15
            pros.append(f"✅ Lives in {_format_locality(h.base_locality)}")
        elif loc and (h.base_city or "").title() in ("Bangalore", "Bengaluru"):
            score += 8
            trade.append("⚠️ Different locality in Bangalore (commute)")
        elif loc:
            trade.append(f"⚠️ Based in {(h.base_city or '').title()}, relocation needed")
        else:
            score += 7.5

        # 4. Work Type Compatibility (10 points)
        if wt:
            if h.work_type == wt:
                score += 10
                pros.append(f"✅ {wt}")
            else:
                trade.append(f"⚠️ Prefers {h.work_type}")
        else:
            score += 5

        # 5. Budget Alignment (10 points)
        if budget:
            if h.expected_salary_inr <= budget:
                score += 10
                pros.append("✅ Within budget")
            else:
                score += max(0, 10 - (h.expected_salary_inr - budget) / budget * 20)
                trade.append(f"⚠️ Expects ₹{h.expected_salary_inr:,} vs budget ₹{budget:,}")
        else:
            score += 5

        # 6. Dietary & Lifestyle Constraints (20 points)
        cons_total, cons_hit = 0, 0
        if wants_pure_veg and "Cooking" in roles | set(h.job_roles):
            cons_total += 1
            cons_hit += 1
            if _helper_refuses_nonveg(h):
                pros.append("✅ Strictly Pure Veg cook")
            else:
                pros.append("✅ Can cook Pure Veg meals")
        elif nonveg and "Cooking" in roles | set(h.job_roles):
            cons_total += 1
            if _helper_refuses_nonveg(h):
                trade.append("⚠️ Pure Veg / Does not cook non-veg or fish")
            else:
                cons_hit += 1
                pros.append("✅ Cooks non-veg / fish")

        if sleep10:
            cons_total += 1
            if _helper_sleeps_by_10pm(h):
                cons_hit += 1
                pros.append("✅ Sleeps at 10 PM")
            else:
                trade.append("⚠️ No fixed 10 PM sleep preference")
        elif sleep_late:
            cons_total += 1
            if _helper_sleeps_by_10pm(h):
                trade.append("⚠️ Prefers sleeping by 10 PM (early sleeper)")
            else:
                cons_hit += 1
                pros.append("✅ Flexible for late evening schedule")

        if hyg:
            cons_total += 1
            if _helper_is_hygienic(h):
                cons_hit += 1
                pros.append("✅ Hygienic")
            else:
                trade.append("⚠️ Hygiene preference not stated")

        score += 20 * (cons_hit / cons_total) if cons_total else 10

        # Trust Bonus (+3 points for verified KYC)
        if h.kyc_blue_tick:
            score = min(100, score + 3)
            pros.append("🔵 Blue Tick KYC verified")

        s = max(0, min(100, round(score)))

        # Strategic human recruiter recommendation
        if s >= 85:
            rec = "Strong match — shortlist now."
        elif trade:
            rec = f"{s}% Match: Recommend calling customer to ask if {'1 exception' if len(trade) == 1 else str(len(trade)) + ' exceptions'} acceptable."
        else:
            rec = "Good match."

        display_name = " ".join(
            part.title() for part in f"{h.first_name or ''} {h.last_name or ''}".split()
        )
        out.append(
            MatchResult(
                helper_id=h.helper_id,
                name=display_name,
                score=s,
                pros=pros,
                tradeoffs=trade,
                recommendation=rec,
            )
        )

    return sorted(out, key=lambda r: r.score, reverse=True)
