"use client";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import type { AgentResult } from "@/lib/agentTypes";

export default function FeedbackSource({ result }: { result?: AgentResult }) {
  const { language } = useSpeakFlow();
  const ur = language === "ur";
  const t = (en: string, text: string) => ur ? text : en;
  const label = !result ? t("Not available", "دستیاب نہیں")
    : !result.status || !result.source ? t("Older result · source unknown", "پرانا نتیجہ، ذریعہ نامعلوم")
    : result.status === "unavailable" ? (result.source === "measured_history" ? t("More comparable readings needed", "مزید یکساں پڑھائی درکار ہے") : t("Not available", "دستیاب نہیں"))
    : result.status === "fallback" ? t("Basic guidance", "بنیادی رہنمائی")
    : result.source === "model" ? t("Suggested guidance", "تجویز کردہ رہنمائی")
    : result.source === "measured_history" ? t("From comparable readings", "یکساں پڑھائی کا موازنہ")
    : t("From this recording", "اس ریکارڈنگ سے");
  return <span className="inline-block text-xs rounded-md px-2 py-1 bg-gray-100 text-text-secondary">{label}</span>;
}
