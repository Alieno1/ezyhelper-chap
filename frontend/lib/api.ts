export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Helper = {
  helper_id: string; source_platform: string; source_credit_cost_inr: number;
  profile_completion_pct: number; profile_quality_score: number; onboarding_stage: string;
  is_available_for_work: boolean; available_from_date: string | null; referral_code: string;
  rating_badge: string; jobs_done_count: number; total_earnings_inr: number;
  first_name: string; middle_name: string | null; last_name: string | null; mobile_number: string;
  age: number | null; dob: string | null; work_type: string; job_category: string;
  languages_known: string[]; job_roles: string[]; base_pincode: string | null;
  base_locality: string | null; base_city: string | null; base_state: string | null;
  gender: string; experience_years: number; experience_months: number; education_level: string;
  marital_status: string; local_commute_type: string; preferred_localities: string[];
  core_skills: string[]; tasks_dos: string[]; tasks_donts: string[]; special_preferences: string[];
  expected_salary_inr: number; shift_start_time: string | null; shift_end_time: string | null;
  identity_proof_status: string; address_proof_status: string; kyc_blue_tick: boolean;
  kyc_masked_id: string; fo_assigned_name: string | null; fo_verification_status: string;
  fo_geo_coordinates: string | null; has_whatsapp: boolean; has_smartphone: boolean;
};
export type Campaign = {
  subscription_spend_inr: number; profiles_scraped_count: number; whatsapp_active_yes_count: number;
  job_inquiry_count: number; bangalore_converted_count: number; cost_per_raw_lead_inr: number;
  cost_per_active_lead_inr: number; final_cac_per_onboarded_helper_inr: number;
};
export type WaMsg = { id: number; sender: "AGENT_AISENSY" | "HELPER"; message_text: string; quick_reply_chips: string[]; timestamp: string };
export type Stage = { stage: number; name: string; logs: string[] };
export type Match = { helper_id: string; name: string; score: number; pros: string[]; tradeoffs: string[]; recommendation: string };

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, { ...init, headers: { "Content-Type": "application/json" }, cache: "no-store" });
  if (!r.ok) {
    let msg = r.statusText;
    try { msg = (await r.json()).detail ?? msg; } catch {}
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return r.json();
}

export const fullName = (h: Helper) => [h.first_name, h.middle_name, h.last_name].filter(Boolean).join(" ");

