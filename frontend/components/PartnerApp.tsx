"use client";
import { useState } from "react";
import { BadgeCheck, CheckCircle2, Circle, FileText, Gift, Printer, X } from "lucide-react";
import { fullName, type Helper } from "@/lib/api";

function Ring({ pct }: { pct: number }) {
  const r = 30, c = 2 * Math.PI * r;
  return (
    <svg width="76" height="76" viewBox="0 0 76 76">
      <circle cx="38" cy="38" r={r} stroke="#e2e8f0" strokeWidth="7" fill="none" />
      <circle cx="38" cy="38" r={r} stroke="#2563EB" strokeWidth="7" fill="none" strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)} strokeLinecap="round" transform="rotate(-90 38 38)" />
      <text x="38" y="43" textAnchor="middle" className="fill-slate-800 text-sm font-bold">{pct}%</text>
    </svg>
  );
}

function Resume({ h, onClose }: { h: Helper; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-[60] overflow-auto bg-black/50 p-4 print:bg-white print:p-0" onClick={onClose}>
      <div id="resume" className="mx-auto max-w-2xl rounded-xl bg-white p-8 shadow-xl print:shadow-none" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between border-b-4 border-blue-600 pb-4">
          <div>
            <div className="text-xl font-extrabold text-blue-600">EzyHelpers</div>
            <h1 className="mt-2 text-2xl font-bold text-slate-900">{fullName(h)} {h.kyc_blue_tick && <BadgeCheck className="inline text-blue-600" size={22} />}</h1>
            <p className="text-slate-600">{h.job_roles.join(" · ")}</p>
          </div>
          <div className="text-right text-sm text-slate-500">
            <div className="font-mono font-semibold text-slate-800">{h.helper_id}</div>
            <div>{h.base_locality}, {h.base_city}</div>
            <div className="mt-1 flex gap-2 print:hidden">
              <button onClick={() => window.print()} className="btn"><Printer size={13} /> Print / Save PDF</button>
              <button onClick={onClose} className="btn"><X size={13} /> Close</button>
            </div>
          </div>
        </div>
        <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
          {[["Age", h.age ?? "—"], ["Experience", `${h.experience_years} yr ${h.experience_months} mo`], ["Languages", h.languages_known.join(", ")],
            ["Work Type", `${h.work_type} (${h.job_category})`], ["Education", h.education_level], ["Expected Salary", `₹${h.expected_salary_inr.toLocaleString("en-IN")}/mo`],
            ["Shift", `${h.shift_start_time ?? "—"} – ${h.shift_end_time ?? "—"}`], ["Verification", h.kyc_blue_tick ? "Blue Tick KYC ✔" : "KYC pending"]].map(([k, v]) => (
            <div key={String(k)}><dt className="text-xs uppercase text-slate-400">{k}</dt><dd className="font-medium text-slate-800">{String(v)}</dd></div>
          ))}
        </dl>
        {([["Core Skills", h.core_skills], ["Helper will do", h.tasks_dos], ["Helper will not do", h.tasks_donts], ["Preferences", h.special_preferences]] as [string, string[]][]).map(([t, items]) =>
          items.length ? (
            <div key={t} className="mt-4"><h3 className="text-xs uppercase text-slate-400">{t}</h3>
              <div className="mt-1 flex flex-wrap gap-1.5">{items.map((i) => <span key={i} className="rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-700">{i}</span>)}</div></div>
          ) : null)}
        <p className="mt-6 border-t pt-3 text-xs text-slate-400">Free Digital Resume by EzyHelpers · Phone number shared only with verified employers · Identity: {h.kyc_masked_id}</p>
      </div>
    </div>
  );
}

export default function PartnerApp({ helper: h, onClose }: { helper: Helper; onClose: () => void }) {
  const [avail, setAvail] = useState(h.is_available_for_work);
  const [cv, setCv] = useState(false);
  const docs = [["Identity Proof", h.identity_proof_status], ["Address Proof", h.address_proof_status], ["Field Officer Verification", h.fo_verification_status === "Geo_Verified" ? "Verified" : "Pending"]];
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40" onClick={onClose}>
      <div className="flex h-full w-full max-w-md flex-col items-center overflow-auto bg-slate-100 p-6" onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="self-end text-slate-500" aria-label="Close"><X /></button>
        <div className="mt-2 w-[300px] rounded-[2.2rem] border-[10px] border-slate-900 bg-white shadow-2xl">
          <div className="mx-auto mt-1 h-4 w-24 rounded-b-xl bg-slate-900" />
          <div className="space-y-3 p-4 text-sm">
            <div><div className="text-xs text-slate-400">Namaste 🙏</div><div className="text-lg font-bold">{h.first_name} {h.kyc_blue_tick && <BadgeCheck className="inline text-blue-600" size={16} />}</div>
              <div className="font-mono text-[11px] text-slate-400">{h.helper_id}</div></div>
            <div className="flex items-center gap-3 rounded-xl bg-blue-50 p-3">
              <Ring pct={h.profile_completion_pct} />
              <div><div className="font-semibold text-blue-800">Profile ready hai!</div><div className="text-xs text-slate-600">{h.profile_completion_pct < 100 ? "Baaki documents upload kariye" : "Aapka profile poora hai"}</div></div>
            </div>
            <div className="rounded-xl border p-3">
              <div className="flex items-center gap-2 font-semibold"><FileText size={16} className="text-blue-600" /> Aapka Digital Resume</div>
              <button onClick={() => setCv(true)} className="mt-2 w-full rounded-lg bg-blue-600 py-2 text-xs font-semibold text-white">Resume Dekhiye</button>
            </div>
            <div className="flex items-center justify-between rounded-xl border p-3">
              <span className="font-medium">Kaam ke liye available</span>
              <button onClick={() => setAvail(!avail)} aria-pressed={avail} className={`h-6 w-11 rounded-full p-0.5 transition ${avail ? "bg-emerald-500" : "bg-slate-300"}`}><span className={`block h-5 w-5 rounded-full bg-white transition ${avail ? "translate-x-5" : ""}`} /></button>
            </div>
            <div className="rounded-xl bg-purple-600 p-3 text-white">
              <div className="flex items-center gap-2 font-semibold"><Gift size={16} /> Refer kariye aur ₹500 tak kamaiye</div>
              <div className="mt-2 inline-block rounded bg-white/20 px-2 py-1 font-mono text-xs tracking-widest">{h.referral_code}</div>
            </div>
            <div className="rounded-xl border p-3">
              <div className="mb-1 font-semibold">Documents Checklist</div>
              {docs.map(([n, s]) => (
                <div key={n} className="flex items-center justify-between py-1 text-xs"><span>{n}</span>
                  <span className={`flex items-center gap-1 ${s === "Verified" ? "text-emerald-600" : "text-slate-400"}`}>{s === "Verified" ? <CheckCircle2 size={13} /> : <Circle size={13} />}{s}</span></div>
              ))}
            </div>
          </div>
        </div>
      </div>
      {cv && <Resume h={h} onClose={() => setCv(false)} />}
    </div>
  );
}

