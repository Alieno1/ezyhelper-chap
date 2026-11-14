"use client";
import { useState } from "react";
import { CheckCircle2, Loader2, Play, Sparkles, Zap } from "lucide-react";
import { api, type Campaign, type Stage } from "@/lib/api";

const STEPS = [
  "Scraping Apna/WorkIndia",
  "LLM Schema Extraction to CHAP",
  "AiSensy WhatsApp Ping",
  "Free Digital CV Dispatched",
  "Auto Digio Blue-Tick KYC",
  "Auto FO Geo-Docket & Routing",
];
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function PipelineConsole({ onDone }: { onDone: () => void }) {
  const [runningMode, setRunningMode] = useState<"autopilot" | "manual" | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const [step, setStep] = useState(-1);
  const [err, setErr] = useState("");
  const [parser, setParser] = useState("");

  async function run(autopilot: boolean) {
    const mode = autopilot ? "autopilot" : "manual";
    setRunningMode(mode);
    setErr("");
    setLines([
      `🚀 Initializing ${autopilot ? "100% Autonomous Autopilot Mode (Zero Clicks)" : "Interactive Step-by-Step Mode"}...`,
    ]);
    setStep(0);

    try {
      const res = await api<{ campaign: Campaign; stages: Stage[]; parser: string }>(
        `/api/agent/run-sourcing-pipeline?autopilot=${autopilot}`,
        { method: "POST" }
      );
      setParser(res.parser);

      for (const s of res.stages) {
        setStep(s.stage - 1);
        setLines((l) => [...l, `▶ Stage ${s.stage}: ${s.name}`]);
        for (const log of s.logs) {
          setLines((l) => [...l, `   ${log}`]);
          await sleep(70);
        }
      }

      setStep(STEPS.length);
      if (autopilot) {
        setLines((l) => [
          ...l,
          "✔ 100% Autopilot Sourcing & Onboarding Complete! All Bangalore helpers have been verified with Blue Tick KYC and assigned to Field Officer Ankit automatically.",
        ]);
      } else {
        setLines((l) => [
          ...l,
          "✔ Sourcing complete (80% profile state). You can now click “Digio KYC” and “Dispatch FO Ankit” on any helper in the CRM table to test interactive verification.",
        ]);
      }
      onDone();
    } catch (e) {
      setErr((e as Error).message);
      setStep(-1);
    } finally {
      setRunningMode(null);
    }
  }

  const isBusy = runningMode !== null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-5">
      <div className="flex flex-wrap items-center gap-4 justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-slate-900">Agent Control Center</h2>
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
              <Sparkles size={11} /> 2 Operating Modes
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Choose full autonomous autopilot (zero clicks) or interactive mode to test individual verification buttons
          </p>
        </div>

        {/* The Two Control Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Button 1: 100% Autonomous Autopilot */}
          <button
            onClick={() => run(true)}
            disabled={isBusy}
            title="Runs the entire chain autonomously: Sourcing → AI Parsing → WhatsApp Ping → Auto KYC Blue Tick → Auto Field Officer Dispatch"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-white font-semibold text-sm hover:bg-emerald-700 shadow-sm disabled:opacity-50 transition"
          >
            {runningMode === "autopilot" ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Zap size={16} />
            )}
            ⚡ Run Full Autopilot (Zero Clicks)
          </button>

          {/* Button 2: Interactive / Manual Control */}
          <button
            onClick={() => run(false)}
            disabled={isBusy}
            title="Sources candidates and creates 80% profiles, leaving KYC & FO buttons for you to click individually during your demo"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-white font-semibold text-sm hover:bg-blue-700 shadow-sm disabled:opacity-50 transition"
          >
            {runningMode === "manual" ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Play size={16} />
            )}
            ▶ Interactive Mode (Manual Step-by-Step)
          </button>
        </div>
      </div>

      {/* Stepper Display */}
      <ol className="mt-4 flex flex-wrap gap-2">
        {STEPS.map((s, i) => {
          const isDone = i < step || (i === step && !isBusy && lines.length > 0);
          const isCurrent = i === step && isBusy;
          return (
            <li
              key={s}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs transition ${
                isDone
                  ? "bg-emerald-50 border-emerald-300 text-emerald-700"
                  : isCurrent
                  ? "bg-blue-50 border-blue-300 text-blue-700 animate-pulse font-medium"
                  : "text-slate-400 border-slate-200"
              }`}
            >
              {isDone ? (
                <CheckCircle2 size={13} />
              ) : (
                <span className="w-3 text-center">{i + 1}</span>
              )}
              {s}
            </li>
          );
        })}
      </ol>

      {err && <p className="mt-3 text-sm text-red-600">Error: {err}</p>}

      {lines.length > 0 && (
        <pre className="mt-4 max-h-64 overflow-auto rounded-lg bg-slate-900 p-4 text-xs leading-5 text-emerald-300">
          {lines.join("\n")}
          {parser && `\n[ai_parser: ${parser}]`}
        </pre>
      )}
    </div>
  );
}
