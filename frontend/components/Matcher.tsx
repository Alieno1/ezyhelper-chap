"use client";
import { useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { api, type Match } from "@/lib/api";

const PERSONAS = [
  { name: "Bengali Family – Sarjapur Road", locality: "Sarjapur Road", text: "Bengali family in Sarjapur Road looking for Full-Time Cook + Housekeeping, must cook fish/non-veg, hygienic, budget ₹24,000" },
  { name: "Bengali Family – HSR Layout", locality: "HSR Layout", text: "Bengali family in HSR Layout looking for Full-Time Cook + Housekeeping, must cook fish/non-veg, sleep by 10 PM, hygienic, budget ₹22,000" },
  { name: "Working Couple with Infant – Whitefield", locality: "Whitefield", text: "Working couple in Whitefield with infant need Full Time Baby Care, Kannada or English speaking, sleep by 10 PM, hygienic, budget ₹26,000" },
  { name: "Elderly Care – Bannerghatta Road", locality: "Bannerghatta Road", text: "Elderly care for parent in Bannerghatta Road, Part Time Physiotherapist + Elderly Care, Hindi English, budget ₹35,000" },
];

const tone = (s: number) => (s >= 85 ? "bg-emerald-100 text-emerald-800" : s >= 70 ? "bg-blue-100 text-blue-800" : "bg-amber-100 text-amber-800");

function parseSmartPreview(raw: string): string[] {
  const tl = raw.toLowerCase();
  const compact = tl.replace(/[^a-z0-9]+/g, "");
  const norm = tl.replace(/[^a-z0-9]+/g, " ");
  const has = (words: string[]) =>
    words.some((w) => {
      const wc = w.replace(/[^a-z0-9]+/g, "");
      return norm.includes(w) || (wc.length >= 3 && compact.includes(wc));
    });

  const chips: string[] = [];
  const roles: string[] = [];
  if (has(["cook", "cooking", "chef", "biryani", "roti", "khana", "rasoi"])) roles.push("Cooking");
  if (has(["housekeeping", "housekeeper", "cleaning", "cleaner", "jhadu", "pocha", "maid", "safai", "utensil"])) roles.push("Housekeeping");
  if (has(["baby", "babycare", "nanny", "infant", "newborn", "child", "japa", "babysitter"])) roles.push("Baby Care");
  if (has(["elderly", "eldercare", "patient care", "patientcare", "senior", "old age", "parent", "caretaker", "caregiver"])) roles.push("Elderly Care");
  if (has(["physio", "physiotherapist", "physiotherapy", "rehab", "therapy"])) roles.push("Physiotherapist");
  if (roles.length) chips.push(`Role: ${roles.join(" + ")}`);

  const langs: string[] = [];
  if (has(["hindi", "bihari", "bhojpuri", "maithili", "north indian", "marwari", "punjabi", "hinglish"])) langs.push("Hindi");
  if (has(["bengali", "bangla", "bangali", "kolkata"])) langs.push("Bengali");
  if (has(["kannada", "kannad", "kannadiga"])) langs.push("Kannada");
  if (has(["english", "eng"])) langs.push("English");
  if (has(["odia", "oriya"])) langs.push("Odia");
  if (has(["urdu", "muslim"])) langs.push("Urdu");
  if (langs.length) chips.push(`Language: ${langs.join("/")}`);

  const locMap: [string, string[]][] = [
    ["HSR Layout", ["hsr layout", "hsrlayout", "hsr"]],
    ["Sarjapur Road", ["sarjapur road", "sarjapurroad", "sarjapur"]],
    ["Whitefield", ["whitefield", "white field", "whitefeild"]],
    ["Bannerghatta Road", ["bannerghatta road", "bannerghattaroad", "bannerghatta", "bg road"]],
    ["Koramangala", ["koramangala", "kormangala"]],
    ["Salt Lake", ["salt lake", "saltlake"]],
    ["Patia", ["patia"]],
    ["Dwarka", ["dwarka"]],
  ];
  for (const [label, aliases] of locMap) {
    if (has(aliases)) {
      chips.push(`Location: ${label}`);
      break;
    }
  }

  if (has(["livein", "24hr", "24x7", "stayin"])) chips.push("Shift: Live In");
  else if (has(["parttime", "halfday"])) chips.push("Shift: Part Time");
  else if (has(["fulltime", "fullday", "dayshift", "8hr", "10hr", "12hr"])) chips.push("Shift: Full Time");

  const pureVeg = /no\s*non[- ]?veg|pure[- ]?veg|veg\s*only|strictly\s*veg/.test(tl) || has(["nononveg", "pureveg", "vegonly"]);
  if (pureVeg) chips.push("Diet: Pure Veg");
  else if (has(["nonveg", "fish", "chicken", "mutton", "meat", "biryani"])) chips.push("Diet: Non-Veg / Fish");

  if (/sleep\w*\s*(?:by|at)?\s*(?:9|10)/.test(tl) || has(["sleepby10", "sleep10", "10pmsleep"])) chips.push("Sleep: By 10 PM");
  else if (/sleep\w*\s*(?:by|at)?\s*(?:11|12)|midnight/.test(tl) || has(["sleepby11", "sleepby12", "12am", "11pm"])) chips.push("Schedule: Late (11 PM–12 AM)");

  if (has(["hygien", "hygenic", "hygene", "neatandclean", "saaf"])) chips.push("Hygiene: Required");

  const mk = tl.match(/(?:budget|salary|₹|rs\.?|inr|under|upto)?\s*\b(\d{2})\s*k\b/);
  const mFull = tl.match(/(?:budget|salary|sal|₹|rs\.?|inr|under|upto)\s*[:=-]?\s*₹?\s*([\d,]{4,7})/);
  const mBare = tl.match(/\b([1-9]\d,\d{3}|[1-9]\d{4})\b/);
  if (mk) chips.push(`Budget: ₹${( parseInt(mk[1], 10) * 1000 ).toLocaleString("en-IN")}`);
  else if (mFull) chips.push(`Budget: ₹${parseInt(mFull[1].replace(/,/g, ""), 10).toLocaleString("en-IN")}`);
  else if (mBare) chips.push(`Budget: ₹${parseInt(mBare[1].replace(/,/g, ""), 10).toLocaleString("en-IN")}`);

  return chips;
}

export default function Matcher() {
  const [text, setText] = useState(PERSONAS[1].text);
  const [res, setRes] = useState<Match[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const smartChips = useMemo(() => parseSmartPreview(text), [text]);

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
      <div className="space-y-2">
        <div className="flex gap-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if ((e.ctrlKey || e.metaKey || e.key === "Enter") && !e.shiftKey && text.trim().length >= 3) {
                e.preventDefault();
                go(text);
              }
            }}
            spellCheck={false}
            autoCapitalize="none"
            placeholder="Type naturally (even without spaces or any casing, e.g. 'biharifamily hsrlayout fulltimecook nonveg budget35k')..."
            rows={2}
            className="flex-1 rounded-lg border border-slate-300 p-3 text-sm focus:border-blue-500 focus:outline-none"
            aria-label="Customer requirement"
          />
          <button onClick={() => go(text)} disabled={loading || text.trim().length < 3} className="rounded-lg bg-blue-600 px-5 font-semibold text-white hover:bg-blue-700 disabled:opacity-60">{loading ? <Loader2 className="animate-spin" /> : "Match"}</button>
        </div>
        {smartChips.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-600">
            <span className="inline-flex items-center gap-1 font-medium text-blue-700"><Sparkles className="h-3.5 w-3.5" /> Smart Understood:</span>
            {smartChips.map((c) => (
              <span key={c} className="rounded-md border border-blue-200 bg-blue-50/70 px-2 py-0.5 text-blue-800">{c}</span>
            ))}
          </div>
        )}
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

