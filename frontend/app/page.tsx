"use client";
import { useCallback, useEffect, useState } from "react";
import { Database, Moon, RefreshCw, Sun } from "lucide-react";
import { api, type Campaign, type Helper } from "@/lib/api";
import Funnel from "@/components/Funnel";
import PipelineConsole from "@/components/PipelineConsole";
import HelperTable from "@/components/HelperTable";
import WhatsAppModal from "@/components/WhatsAppModal";
import PartnerApp from "@/components/PartnerApp";
import Matcher from "@/components/Matcher";

export default function Home() {
  const [helpers, setHelpers] = useState<Helper[]>([]);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [tab, setTab] = useState<"crm" | "match">("crm");
  const [wa, setWa] = useState<Helper | null>(null);
  const [app, setApp] = useState<Helper | null>(null);
  const [health, setHealth] = useState<{ database: string; gemini: boolean } | null>(null);
  const [err, setErr] = useState("");
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("chap_theme") : null;
    const isDark = saved === "dark";
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("chap_theme", next ? "dark" : "light");
  }

  const load = useCallback(async () => {
    try {
      const [h, c, hl] = await Promise.all([
        api<Helper[]>("/api/helpers"), api<Campaign | null>("/api/campaign"), api<{ database: string; gemini: boolean }>("/api/health"),
      ]);
      setHelpers(h); setCampaign(c); setHealth(hl); setErr("");
      setApp((cur) => (cur ? h.find((x) => x.helper_id === cur.helper_id) ?? null : null));
    } catch (e) { setErr((e as Error).message); }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <main className="mx-auto max-w-7xl space-y-5 p-4 md:p-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900"><span className="text-blue-600">EzyHelpers</span> · CHAP Command Center</h1>
          <p className="text-sm text-slate-500">Agentic supply sourcing, WhatsApp validation, KYC &amp; Field Officer docketing (POC · simulated integrations)</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          {health && <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1"><Database size={12} /> {health.database} · Gemini {health.gemini ? "on" : "fallback parser"}</span>}
          <button onClick={toggleTheme} className="btn" aria-label="Toggle Dark Mode" title="Switch between Light and Dark Mode">
            {dark ? <Sun size={13} className="text-amber-400" /> : <Moon size={13} />}
            {dark ? "Light Mode" : "Dark Mode"}
          </button>
          <button onClick={load} className="btn" aria-label="Refresh"><RefreshCw size={13} /> Refresh</button>
        </div>
      </header>

      {err && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">Cannot reach backend: {err}. Start it with <code>uvicorn main:app --port 8000</code>.</div>}

      <Funnel c={campaign} />
      <PipelineConsole onDone={load} />

      <div className="flex gap-1 border-b border-slate-200">
        {([["crm", "CHAP CRM"], ["match", "Customer Propensity Matcher"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)} className={`px-4 py-2 text-sm font-medium ${tab === k ? "border-b-2 border-blue-600 text-blue-700" : "text-slate-500"}`}>{l}</button>
        ))}
      </div>
      {tab === "crm"
        ? <HelperTable helpers={helpers} onInspect={setWa} onOpenApp={setApp} onChanged={load} />
        : <Matcher />}

      {wa && <WhatsAppModal helper={wa} onClose={() => setWa(null)} />}
      {app && <PartnerApp key={app.helper_id + app.profile_completion_pct} helper={app} onClose={() => setApp(null)} />}
    </main>
  );
}
