"use client";
import { useState } from "react";
import { CheckCircle2, Loader2, Zap } from "lucide-react";
import { api, type Campaign, type Stage } from "@/lib/api";

const STEPS = ["Scraping Apna/WorkIndia", "Gemini Schema Mapping to CHAP", "AiSensy WhatsApp Ping", "Free Digital CV Dispatched", "Digio Blue-Tick KYC"];
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function PipelineConsole({ onDone }: { onDone: () => void }) {
  const [running, setRunning] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  const [step, setStep] = useState(-1);
  const [err, setErr] = useState("");
  const [parser, setParser] = useState("");

  async function run() {
    setRunning(true); setErr(""); setLines([]); setStep(0);
    try {
      const res = await api<{ campaign: Campaign; stages: Stage[]; parser: string }>("/api/agent/run-sourcing-pipeline", { method: "POST" });
      setParser(res.parser);
      const stepFor = [0, 1, 2, 3];
      for (const s of res.stages) {
        setStep(stepFor[s.stage - 1]);
        setLines((l) => [...l, `▶ Stage ${s.stage}: ${s.name}`]);
        for (const log of s.logs.slice(0, 14)) { setLines((l) => [...l, `   ${log}`]); await sleep(110); }
      }
      setStep(4);
      setLines((l) => [...l, "✔ Pipeline complete. Run “Digio KYC” on any helper to award the Blue Tick (step 5)."]);
      onDone();
    } catch (e) { setErr((e as Error).message); setStep(-1); } finally { setRunning(false); }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
      <div className="flex flex-wrap items-center gap-4 justify-between">
        <div>
          <h2 className="font-semibold text-slate-900">Agent Control Center</h2>
          <p className="text-sm text-slate-500">Autonomous sourcing & onboarding agent (portals, WhatsApp & KYC are simulated)</p>
        </div>
        <button onClick={run} disabled={running}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-3 text-white font-semibold hover:bg-blue-700 disabled:opacity-60">
          {running ? <Loader2 className="animate-spin" size={18} /> : <Zap size={18} />}
          Run Autonomous Sourcing &amp; Onboarding Agent
        </button>
      </div>
      <ol className="mt-4 flex flex-wrap gap-2">
        {STEPS.map((s, i) => (
          <li key={s} className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs ${i < step || (i === step && !running && lines.length) ? "bg-emerald-50 border-emerald-300 text-emerald-700" : i === step ? "bg-blue-50 border-blue-300 text-blue-700 animate-pulse" : "text-slate-400 border-slate-200"}`}>
            {(i < step || (i === step && !running && lines.length > 0)) ? <CheckCircle2 size={13} /> : <span className="w-3 text-center">{i + 1}</span>}{s}
          </li>
        ))}
      </ol>
      {err && <p className="mt-3 text-sm text-red-600">Error: {err}. Is the backend running?</p>}
      {lines.length > 0 && (
        <pre className="mt-4 max-h-56 overflow-auto rounded-lg bg-slate-900 p-4 text-xs leading-5 text-emerald-300">
          {lines.join("\n")}{parser && `\n[parser: ${parser}]`}
        </pre>
      )}
    </div>
  );
}

