"use client";
import { useState } from "react";
import { Loader2 } from "lucide-react";
import { api, type Match } from "@/lib/api";

const PERSONAS = [
  { name: "Bengali Family – Sarjapur Road", locality: "Sarjapur Road", text: "Bengali family in Sarjapur Road looking for Full-Time Cook + Housekeeping, must cook fish/non-veg, hygienic, budget ₹24,000" },
  { name: "Bengali Family – HSR Layout", locality: "HSR Layout", text: "Bengali family in HSR Layout looking for Full-Time Cook + Housekeeping, must cook fish/non-veg, sleep by 10 PM, hygienic, budget ₹22,000" },
  { name: "Working Couple with Infant – Whitefield", locality: "Whitefield", text: "Working couple in Whitefield with infant need Full Time Baby Care, Kannada or English speaking, sleep by 10 PM, hygienic, budget ₹26,000" },
  { name: "Elderly Care – Bannerghatta Road", locality: "Bannerghatta Road", text: "Elderly care for parent in Bannerghatta Road, Part Time Physiotherapist + Elderly Care, Hindi English, budget ₹35,000" },
];

const tone = (s: number) => (s >= 85 ? "bg-emerald-100 text-emerald-800" : s >= 70 ? "bg-blue-100 text-blue-800" : "bg-amber-100 text-amber-800");

export default function Matcher() {
  const [text, setText] = useState(PERSONAS[1].text);
  const [res, setRes] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  async function go(t: string, loc?: string) {
    setLoading(true); setErr("");
    try { setRes(await api<Match[]>("/api/agent/match-customer", { method: "POST", body: JSON.stringify({ text: t, locality: loc }) })); }
    catch (e) { setErr((e as Error).message); } finally { setLoading(false); }
  }

  const shown = res?.filter((m) => m.score >= 70) ?? [];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {PERSONAS.map((p) => <button key={p.name} className="btn" onClick={() => { setText(p.text); go(p.text, p.locality); }}>{p.name}</button>)}
      </div>
      <div className="flex gap-2">
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={2} className="flex-1 rounded-lg border border-slate-300 p-3 text-sm" aria-label="Customer requirement" />
        <button onClick={() => go(text)} disabled={loading || text.trim().length < 3} className="rounded-lg bg-blue-600 px-4 font-semibold text-white disabled:opacity-60">{loading ? <Loader2 className="animate-spin" /> : "Match"}</button>
      </div>
      {err && <p className="text-sm text-red-600">{err}</p>}
      {res && (
        <div className="space-y-3">
          <p className="text-sm text-slate-500">{shown.length} helper(s) ≥ 70% · showing top results (all {res.length} scored)</p>
          {(shown.length ? shown : res.slice(0, 3)).map((m) => (
            <div key={m.helper_id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between"><div><span className="font-semibold">{m.name}</span> <span className="font-mono text-xs text-slate-400">{m.helper_id}</span></div>
                <span className={`rounded-full px-3 py-1 text-sm font-bold ${tone(m.score)}`}>{m.score}%</span></div>
              <div className="mt-2 flex flex-wrap gap-1.5 text-xs">{m.pros.map((p) => <span key={p} className="rounded bg-emerald-50 px-2 py-1 text-emerald-700">{p}</span>)}{m.tradeoffs.map((p) => <span key={p} className="rounded bg-amber-50 px-2 py-1 text-amber-700">{p}</span>)}</div>
              <p className="mt-2 text-sm text-slate-600">{m.recommendation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

