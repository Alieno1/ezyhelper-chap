import { IndianRupee, MessageCircle, Search, Target, Users } from "lucide-react";
import type { Campaign } from "@/lib/api";

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

export default function Funnel({ c }: { c: Campaign | null }) {
  const cards = [
    { icon: IndianRupee, label: "Portal Spend", sub: "Apna + WorkIndia", value: c ? inr(c.subscription_spend_inr) : "₹2,000", tone: "bg-slate-100 text-slate-700" },
    { icon: Search, label: "Contacts Unlocked", sub: c ? `@ ${inr(c.cost_per_raw_lead_inr)}/CV` : "@ ₹40/CV", value: c?.profiles_scraped_count ?? 50, tone: "bg-indigo-50 text-indigo-700" },
    { icon: MessageCircle, label: "WhatsApp Active “Yes”", sub: c ? `@ ${inr(c.cost_per_active_lead_inr)}/active` : "@ ₹200/active", value: c?.whatsapp_active_yes_count ?? 10, tone: "bg-emerald-50 text-emerald-700" },
    { icon: Users, label: "Job Seekers", sub: "interested", value: c?.job_inquiry_count ?? 5, tone: "bg-amber-50 text-amber-700" },
    { icon: Target, label: "Bangalore Conversions", sub: c ? `${inr(c.final_cac_per_onboarded_helper_inr)} final CAC` : "₹1,000 final CAC", value: c?.bangalore_converted_count ?? 2, tone: "bg-blue-600 text-white" },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {cards.map((k, i) => (
        <div key={k.label} className={`rounded-xl p-4 shadow-sm border border-slate-200 ${k.tone} ${c ? "" : "opacity-60"}`}>
          <div className="flex items-center justify-between text-xs font-medium opacity-80">
            <span>{k.label}</span><k.icon size={16} />
          </div>
          <div className="text-3xl font-bold mt-2">{k.value}</div>
          <div className="text-xs mt-1 opacity-80">{k.sub}</div>
          {i < cards.length - 1 && <span className="hidden md:block absolute" />}
        </div>
      ))}
    </div>
  );
}

