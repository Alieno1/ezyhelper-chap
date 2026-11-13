"use client";
import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { api, fullName, type Helper, type WaMsg } from "@/lib/api";

export default function WhatsAppModal({ helper, onClose }: { helper: Helper; onClose: () => void }) {
  const [msgs, setMsgs] = useState<WaMsg[] | null>(null);
  useEffect(() => { api<WaMsg[]>(`/api/helpers/${helper.helper_id}/whatsapp`).then(setMsgs).catch(() => setMsgs([])); }, [helper.helper_id]);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="w-full max-w-md overflow-hidden rounded-2xl bg-[#efeae2] shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between bg-[#075e54] px-4 py-3 text-white">
          <div><div className="font-semibold">{fullName(helper)}</div><div className="text-xs opacity-80">{helper.mobile_number} · AiSensy Inspector</div></div>
          <button onClick={onClose} aria-label="Close"><X size={20} /></button>
        </div>
        <div className="max-h-[60vh] space-y-3 overflow-auto p-4">
          {msgs === null && <p className="text-sm text-slate-500">Loading…</p>}
          {msgs?.length === 0 && <p className="text-sm text-slate-500">No messages.</p>}
          {msgs?.map((m) => (
            <div key={m.id} className={`flex ${m.sender === "HELPER" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm shadow ${m.sender === "HELPER" ? "bg-[#d9fdd3]" : "bg-white"}`}>
                {m.message_text}
                {m.quick_reply_chips.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">{m.quick_reply_chips.map((c) => <span key={c} className="rounded-full border border-sky-300 px-2.5 py-1 text-xs text-sky-700">{c}</span>)}</div>
                )}
                <div className="mt-1 text-right text-[10px] text-slate-400">{new Date(m.timestamp + "Z").toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

