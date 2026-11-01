"use client";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { MessageCircle } from "lucide-react";
import FeedbackSource from "./FeedbackSource";

export default function AgentsAtWorkCard() {
  const { agents, sessionState, language, controlsLocked } = useSpeakFlow();
  const ur = language === "ur";
  const t = (en: string, text: string) => ur ? text : en;
  const rows = [
    { id: "engagement", title: t("Reading observations", "ریکارڈنگ کا مشاہدہ"), field: "teacher_note" as const },
    { id: "difficulty", title: t("Practice suggestion", "مشق کا مشورہ"), field: "primary_issue" as const },
    { id: "progress", title: t("Compare this sentence", "اسی جملے کا موازنہ"), field: "report_text" as const },
  ];
  return (
    <section aria-label="Practice & Feedback" className="speakflow-card p-6 bg-white h-full min-w-0">
      <h2 className="text-lg font-bold flex items-center gap-2"><MessageCircle className="w-5 h-5 text-accent-primary-dark" />{t("Practice & Feedback", "مشق اور رہنمائی")}</h2>
      <p className="text-xs text-text-muted mt-2 mb-5" role="status">
        {sessionState === "complete" ? t("Feedback ready", "رہنمائی تیار ہے")
          : sessionState === "processing" ? t("Preparing feedback…", "رہنمائی تیار ہو رہی ہے۔")
          : controlsLocked ? t("Feedback follows your recording.", "ریکارڈنگ کے بعد رہنمائی ملے گی۔")
          : t("Complete a reading to get practice suggestions.", "رہنمائی کے لیے ایک جملہ پڑھیں۔")}
      </p>
      {sessionState === "complete" && <div className={ur ? "space-y-4 font-urdu text-lg leading-loose" : "space-y-4"} dir={ur ? "rtl" : "ltr"}>
        {rows.map(row => {
          const result = agents.find(agent => agent.id === row.id)?.result;
          return <div key={row.id} className="rounded-xl border border-gray-200 p-4">
            <div className="flex flex-wrap items-center gap-2 mb-2"><h3 className="font-bold">{row.title}</h3><FeedbackSource result={result} /></div>
            <p className="text-text-secondary break-words">{result?.[row.field] || t("No guidance is available for this reading.", "اس ریکارڈنگ کے لیے رہنمائی دستیاب نہیں ہے۔")}</p>
          </div>;
        })}
      </div>}
    </section>
  );
}
