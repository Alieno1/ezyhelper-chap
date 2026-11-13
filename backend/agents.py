"""Agent logic: simulated scraping, schema extraction (Gemini + deterministic fallback),
WhatsApp bot simulation, KYC, FO routing and propensity matching.

All portal/KYC/WhatsApp integrations are SIMULATED. No real Aadhaar numbers are ever
generated, stored or logged; KYC uses the placeholder "[Aadhaar Redacted]".
"""
import json
import os
import random
import re
import string
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import Helper, SourcingCampaign, WhatsAppLog
from schemas import CustomerRequirement, MatchResult

# locality -> (pincode, city, state, FO geo cluster)
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

# 10 curated raw "scraped" bios (messy on purpose) out of the 50 unlocked contacts.
# Format of tail tokens: phone is a MOCK number.
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

ROLE_KEYS = {
    "Housekeeping": ["housekeeping", "cleaning", "jhadu"],
    "Cooking": ["cook", "biryani", "roti"],
    "Elderly Care": ["elderly", "patient care"],
    "Baby Care": ["baby", "nanny", "infant"],
    "Physiotherapist": ["physio"],
}
LANG_KEYS = {"Hindi": ["hindi"], "English": ["english"], "Bengali": ["bengali", "bangla"],
             "Kannada": ["kannada"], "Odia": ["odia"], "Urdu": ["urdu"]}
EDU_KEYS = [("post graduate", "Post Graduate"), ("graduate", "Graduate"), ("senior secondary", "Senior Secondary"),
            ("secondary", "Secondary"), ("10th", "Secondary"), ("primary", "Primary")]
COMMUTE_KEYS = [("2 wheeler", "2 Wheeler"), ("cycle", "Cycle"), ("auto", "Auto"), ("walking", "Walking"), ("bus", "Bus")]
SKILL_KEYS = {
    "north indian cooking": "North Indian Cooking", "fish curry": "Bengali Fish Curry", "biryani": "Biryani & Non-Veg Cooking",
    "utensils": "Utensil Cleaning", "infant massage": "Infant Massage", "muscle strengthening": "Muscle Strengthening & Therapeutic Exercise",
    "diabetic diet": "Diabetic Diet Care", "deep cleaning": "Deep Cleaning", "baby feeding": "Baby Feeding",
}
DO_KEYS = {"jhadu": "Jhadu-Pocha", "roti": "Roti & Sabzi", "baby feeding": "Baby Feeding", "utensils": "Utensil Cleaning",
           "patient care": "Patient Care", "cook": "Daily Cooking"}


def _chance_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _has(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


def deterministic_parse(raw: str, source: str) -> dict:
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
    dob_year = datetime.utcnow().year - (age or 30)
    return {
        "source_platform": source, "app_language": app_lang, "first_name": first, "last_name": last,
        "mobile_number": phone, "dob": f"15/06/{dob_year}", "age": age, "work_type": work_type,
        "languages_known": langs, "job_roles": roles, "base_pincode": pin,
        "base_locality": locality.title() if locality else None, "base_city": city, "base_state": state,
        "current_city": city, "current_state": state, "current_pincode": pin,
        "current_street_house": f"{locality.title()} (house details pending)" if locality else None,
        "gender": "Female" if female else "Male", "experience_years": exp, "education_level": edu,
        "marital_status": marital, "local_commute_type": commute,
        "preferred_localities": [locality.title()] if locality else [], "core_skills": skills,
        "tasks_dos": dos, "tasks_donts": donts, "special_preferences": prefs,
        "expected_salary_inr": salary, "min_shift_duration_hours": 8 if work_type != "Live In" else 12,
        "shift_start_time": "08:00 AM", "shift_end_time": "06:00 PM", "break_start_time": "01:00 PM", "break_end_time": "02:00 PM",
        "religion": None,
    }


def gemini_parse(raw: str, source: str, base: dict) -> tuple[dict, str]:
    """Overlay Gemini-extracted fields on the deterministic base. Falls back silently on any error."""
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
        if or_key:  # OpenRouter (OpenAI-compatible chat completions)
            import urllib.request
            body = json.dumps({
                "model": os.getenv("OPENROUTER_MODEL", "google/gemini-3.5-flash-lite"),
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}, "max_tokens": 1200,
            }).encode()
            rq = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers={
                "Authorization": f"Bearer {or_key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(rq, timeout=30) as r:
                text = json.load(r)["choices"][0]["message"]["content"]
            provider = "openrouter"
        else:
            from google import genai
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            text, provider = resp.text, "gemini"
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        data = json.loads(text)
        merged = dict(base)
        for k, v in data.items():
            if k in base and k not in {"mobile_number", "source_platform"} and v is not None and type(v) is type(base[k]):
                merged[k] = v
        return merged, provider
    except Exception as exc:  # noqa: BLE001
        print(f"[gemini] fallback to deterministic parser: {exc.__class__.__name__}")
        return base, "deterministic"


def _new_helper_id(db: Session, used: set[str]) -> str:
    while True:
        hid = f"HLPRIN{random.randint(10000, 99999)}"
        if hid not in used and not db.scalar(select(Helper.id).where(Helper.helper_id == hid)):
            used.add(hid)
            return hid


def _wa(db: Session, hid: str, sender: str, text: str, chips: list[str] | None = None):
    db.add(WhatsAppLog(helper_id=hid, sender=sender, message_text=text, quick_reply_chips=chips or []))


def run_pipeline(db: Session) -> dict:
    """Wipes demo data and executes the 4-stage funnel (2000 -> 50 -> 10 -> 5 -> 2)."""
    db.execute(delete(WhatsAppLog))
    db.execute(delete(Helper))
    db.execute(delete(SourcingCampaign))
    db.flush()
    random.seed(7)
    stages = []

    stages.append({"stage": 1, "name": "Talent Hunting (Apna + WorkIndia)", "logs": [
        "Logging into Apna recruiter dashboard (simulated session)...",
        "Logging into WorkIndia recruiter dashboard (simulated session)...",
        "Purchasing ₹2,000 credit pack → 50 contact unlocks (₹40/contact)",
        "Filtering for roles: Housekeeping, Cooking, Baby Care, Elderly Care, Physiotherapist",
        "Unlocked 50 raw candidate contacts"]})

    helpers, parser_used, used = [], "deterministic", set()
    logs2 = ["Sending 10 shortlisted raw bios through the schema-extraction agent..."]
    for i, (src, raw) in enumerate(RAW_PROFILES):
        base = deterministic_parse(raw, src)
        data, parser_used_i = gemini_parse(raw, src, base)
        if parser_used_i != "deterministic":
            parser_used = parser_used_i
        hid = _new_helper_id(db, used)
        h = Helper(helper_id=hid, source_credit_cost_inr=40.0, profile_completion_pct=80,
                   profile_quality_score=45 + (i % 4) * 3, referral_code="WXWRSH" if i == 0 else _chance_code(),
                   onboarding_stage="SCRAPED", **data)
        db.add(h)
        helpers.append(h)
        logs2.append(f"{hid}: {h.first_name} {h.last_name or ''} → {', '.join(h.job_roles)} @ {h.base_locality or h.base_city} (80% complete)")
    db.flush()
    stages.append({"stage": 2, "name": "LLM Schema Extraction & CHAP Replica Creation", "logs": logs2})

    logs3 = []
    for h in helpers:
        first = h.first_name
        _wa(db, h.helper_id, "AGENT_AISENSY",
            f"Namaste Didi! 🙏 Main Rita bol rahi hoon EzyHelpers se. Hume Apna app se aapka profile mila. Kya aap abhi ghar ke kaam "
            f"(Cooking / Housekeeping / Baby Care) ki acchi naukri dhundh rahi hain? Niche YES button dabayein!",
            ["Yes, मुझे नौकरी चाहिए", "No"])
        h.onboarding_stage = "WHATSAPP_PINGED"
        _wa(db, h.helper_id, "HELPER", "Yes, मुझे नौकरी चाहिए")
        h.onboarding_stage = "ACTIVE_REPLIED_YES"
        _wa(db, h.helper_id, "AGENT_AISENSY",
            f"Congratulations Didi! 🎉 Aapka EzyHelpers Partner profile (80%) aur aapka FREE Digital Resume taiyar hai! "
            f"App link: https://ezyhelpers.com/app/{h.helper_id} Kya aap Bangalore mein kaam karne ke liye available hain?",
            ["Yes, Bangalore mein available", "No, doosre sheher mein", "Send My Free CV"])
        h.onboarding_stage = "CV_GENERATED"
        logs3.append(f"{h.helper_id} ({first}): ping → YES → Free Digital CV dispatched")
    stages.append({"stage": 3, "name": "AiSensy WhatsApp Deterministic Ping", "logs": logs3})

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
    logs4 += ["Funnel: ₹2,000 → 50 scraped → 10 active on WhatsApp → 5 job seekers → 2 Bangalore conversions",
              "Final CAC = ₹1,000 per onboarded helper"]
    stages.append({"stage": 4, "name": "Funnel Filtering", "logs": logs4})
    db.commit()
    db.refresh(camp)
    return {"campaign": camp, "stages": stages, "helper_ids": [h.helper_id for h in helpers], "parser": parser_used}


def verify_kyc(db: Session, h: Helper) -> Helper:
    _wa(db, h.helper_id, "AGENT_AISENSY",
        "Didi, aapki pehchaan verify karne ke liye hume aapki consent chahiye (Digio / UIDAI). Kya aap sahmat hain?", ["Haan, sahmat hoon"])
    _wa(db, h.helper_id, "HELPER", "Haan, sahmat hoon")
    h.kyc_masked_id = "[Aadhaar Redacted]"
    h.identity_proof_status = h.address_proof_status = "Verified"
    h.kyc_blue_tick = True
    h.kyc_verified_at = datetime.utcnow()
    h.profile_completion_pct = max(h.profile_completion_pct, 95)
    h.profile_quality_score = min(100, h.profile_quality_score + 25)
    if h.onboarding_stage != "FO_GEO_VERIFIED":
        h.onboarding_stage = "KYC_BLUE_TICK"
    _wa(db, h.helper_id, "AGENT_AISENSY", "Badhai ho! ✅ Aapka Blue Tick KYC verification poora ho gaya.")
    db.commit()
    return h


def assign_fo(db: Session, h: Helper) -> Helper:
    loc = (h.base_locality or "").lower()
    geo = LOCALITIES.get(loc, ("", "", "", ""))[3]
    h.fo_assigned_name = "Ankit (FO - Bangalore South)"
    h.fo_verification_status = "Geo_Verified"
    h.fo_geo_coordinates = geo or "12.9081° N, 77.6476° E (Bannerghatta / Sarjapur Cluster)"
    h.fo_house_photo_url = f"mock://fo-verified-house/{h.helper_id}.jpg"
    h.profile_completion_pct = 100
    h.profile_quality_score = 98
    h.onboarding_stage = "FO_GEO_VERIFIED"
    _wa(db, h.helper_id, "AGENT_AISENSY", "Field Officer Ankit ne aapke ghar ka geo-verification poora kar liya hai. Customer Docket ready hai! 🏠")
    db.commit()
    return h


def match_customer(db: Session, req: CustomerRequirement) -> list[MatchResult]:
    text = req.text.lower()
    roles = set(req.roles) or {r for r, k in ROLE_KEYS.items() if _has(text, k)}
    langs = set(req.languages) or {l for l, k in LANG_KEYS.items() if _has(text, k)}
    loc = (req.locality or next((k for k in LOCALITIES if k in text), "") or "").lower()
    nonveg = req.must_cook_nonveg or bool(re.search(r"non[- ]?veg|fish|chicken|biryani", text))
    sleep10 = req.sleep_by_10pm or bool(re.search(r"sleep\w* by 10", text))
    hyg = req.hygienic or "hygien" in text
    wt = req.work_type or next((w for w in ("Live In", "Full Time", "Part Time") if w.lower() in text), None)
    budget = req.budget_inr
    if budget is None:
        m = re.search(r"(?:budget|₹|rs\.?)\s*([\d,]{4,7})", text)
        budget = int(m.group(1).replace(",", "")) if m else None

    out = []
    for h in db.scalars(select(Helper).where(Helper.is_available_for_work.is_(True))):
        score, pros, trade = 0.0, [], []
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
        if langs:
            hit = langs & set(h.languages_known)
            score += 15 * len(hit) / len(langs)
            if hit:
                pros.append(f"✅ Speaks {'/'.join(sorted(hit))}")
            else:
                trade.append("⚠️ No common language")
        else:
            score += 7.5
        if loc and (h.base_locality or "").lower() == loc:
            score += 15
            pros.append(f"✅ Lives in {h.base_locality}")
        elif loc and h.base_city == "Bangalore":
            score += 8
            trade.append("⚠️ Different locality in Bangalore (commute)")
        elif loc:
            trade.append(f"⚠️ Based in {h.base_city}, relocation needed")
        else:
            score += 7.5
        if wt:
            if h.work_type == wt:
                score += 10
                pros.append(f"✅ {wt}")
            else:
                trade.append(f"⚠️ Prefers {h.work_type}")
        else:
            score += 5
        if budget:
            if h.expected_salary_inr <= budget:
                score += 10
                pros.append("✅ Within budget")
            else:
                score += max(0, 10 - (h.expected_salary_inr - budget) / budget * 20)
                trade.append(f"⚠️ Expects ₹{h.expected_salary_inr:,} vs budget ₹{budget:,}")
        else:
            score += 5
        cons_total, cons_hit = 0, 0
        if nonveg and "Cooking" in roles | set(h.job_roles):
            cons_total += 1
            if "Non-Veg Cooking" in h.tasks_donts:
                trade.append("⚠️ Pure Veg / Does not cook non-veg or fish")
            else:
                cons_hit += 1
                pros.append("✅ Cooks non-veg / fish")
        if sleep10:
            cons_total += 1
            if "Sleep by 10:00 PM" in h.special_preferences:
                cons_hit += 1
                pros.append("✅ Sleeps at 10 PM")
            else:
                trade.append("⚠️ No fixed 10 PM sleep preference")
        if hyg:
            cons_total += 1
            if "Hygienic Environment" in h.special_preferences:
                cons_hit += 1
                pros.append("✅ Hygienic")
            else:
                trade.append("⚠️ Hygiene preference not stated")
        score += 20 * (cons_hit / cons_total) if cons_total else 10
        if h.kyc_blue_tick:
            score = min(100, score + 3)
            pros.append("🔵 Blue Tick KYC verified")
        s = max(0, min(100, round(score)))
        if s >= 85:
            rec = "Strong match — shortlist now."
        elif trade:
            rec = f"{s}% Match: Recommend calling customer to ask if {'1 exception' if len(trade) == 1 else str(len(trade)) + ' exceptions'} acceptable."
        else:
            rec = "Good match."
        out.append(MatchResult(helper_id=h.helper_id, name=f"{h.first_name} {h.last_name or ''}".strip(),
                               score=s, pros=pros, tradeoffs=trade, recommendation=rec))
    return sorted(out, key=lambda r: r.score, reverse=True)
