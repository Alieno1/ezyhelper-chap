"use client";
import { useState } from "react";
import { BadgeCheck, MapPin, MessageSquare, ShieldCheck, Smartphone, Truck } from "lucide-react";
import { api, fullName, type Helper } from "@/lib/api";

type Props = {
  helpers: Helper[];
  onInspect: (h: Helper) => void;
  onOpenApp: (h: Helper) => void;
  onChanged: () => void;
};

export default function HelperTable({ helpers, onInspect, onOpenApp, onChanged }: Props) {
  const [busy, setBusy] = useState<string>("");
  const [err, setErr] = useState("");

  async function act(kind: "verify-kyc" | "assign-field-officer", h: Helper) {
    setBusy(kind + h.helper_id); setErr("");
    try { await api(`/api/agent/${kind}/${h.helper_id}`, { method: "POST" }); onChanged(); }
    catch (e) { setErr(`${h.helper_id}: ${(e as Error).message}`); }
    finally { setBusy(""); }
  }

  if (!helpers.length)
    return <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center text-slate-500">No helpers yet — run the sourcing agent above.</div>;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-x-auto">
      {err && <p className="px-4 pt-3 text-sm text-red-600">{err}</p>}
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
          <tr>{["Helper ID", "Name", "Mobile", "Locality", "Roles", "Work Type", "Quality", "Status", "Actions"].map((c) => <th key={c} className="px-3 py-3 font-medium whitespace-nowrap">{c}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {helpers.map((h) => (
            <tr key={h.helper_id} className="hover:bg-slate-50 align-top">
              <td className="px-3 py-3 font-mono text-xs text-blue-700">{h.helper_id}</td>
              <td className="px-3 py-3 font-medium text-slate-900 whitespace-nowrap">
                {fullName(h)} {h.kyc_blue_tick && <BadgeCheck size={15} className="inline text-blue-600" aria-label="Blue Tick" />}
                <div className="text-xs font-normal text-slate-400">{h.source_platform} · {h.onboarding_stage.replaceAll("_", " ")}</div>
              </td>
              <td className="px-3 py-3 whitespace-nowrap">{h.mobile_number}</td>
              <td className="px-3 py-3">{h.base_locality ?? "—"}<div className="text-xs text-slate-400">{h.base_city}</div></td>
              <td className="px-3 py-3"><div className="flex flex-wrap gap-1">{h.job_roles.map((r) => <span key={r} className="rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-700">{r}</span>)}</div></td>
              <td className="px-3 py-3 whitespace-nowrap">{h.work_type}</td>
              <td className="px-3 py-3 w-32">
                <div className="h-2 rounded bg-slate-200"><div className={`h-2 rounded ${h.profile_quality_score >= 85 ? "bg-emerald-500" : h.profile_quality_score >= 60 ? "bg-blue-500" : "bg-amber-500"}`} style={{ width: `${h.profile_quality_score}%` }} /></div>
                <div className="mt-1 text-xs text-slate-500">{h.profile_quality_score}/100 · {h.profile_completion_pct}%</div>
              </td>
              <td className="px-3 py-3 space-y-1">
                {h.kyc_blue_tick && <span className="flex items-center gap-1 text-xs text-blue-700"><ShieldCheck size={13} /> Blue Tick KYC</span>}
                {h.fo_verification_status === "Geo_Verified" && <span className="flex items-center gap-1 text-xs text-emerald-700"><MapPin size={13} /> FO Geo-Docket</span>}
                {!h.kyc_blue_tick && h.fo_verification_status !== "Geo_Verified" && <span className="text-xs text-slate-400">Pending</span>}
              </td>
              <td className="px-3 py-3">
                <div className="flex flex-wrap gap-1.5 w-60">
                  <button onClick={() => onInspect(h)} className="btn"><MessageSquare size={13} /> WhatsApp</button>
                  <button disabled={h.kyc_blue_tick || !!busy} onClick={() => act("verify-kyc", h)} className="btn"><ShieldCheck size={13} /> {busy === "verify-kyc" + h.helper_id ? "…" : "Digio KYC"}</button>
                  <button disabled={h.base_city !== "Bangalore" || h.fo_verification_status === "Geo_Verified" || !!busy} onClick={() => act("assign-field-officer", h)} className="btn" title={h.base_city !== "Bangalore" ? "FO covers Bangalore only" : ""}><Truck size={13} /> Dispatch FO Client</button>
                  <button onClick={() => onOpenApp(h)} className="btn bg-blue-600 text-white border-blue-600 hover:bg-blue-700"><Smartphone size={13} /> Partner App</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

