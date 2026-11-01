"use client";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { speak } from "@/lib/speech";
import { Target, Volume2 } from "lucide-react";
import { useState } from "react";
import FeedbackSource from "./FeedbackSource";

export default function PracticeCard() {
  const { sessionState, agents, addAvailableSentence, setTargetSentence, language } = useSpeakFlow();
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const result = agents.find(a => a.id === "practice")?.result;
  const sentences = result?.sentences || [];
  useDeferredEffect(() => { setSelectedIndex(null); }, [result, sessionState]);
  const ur = language === "ur";
  const t = (en: string, text: string) => ur ? text : en;
  const difficulty = (value?: string) => ({ easy: t("Easy", "آسان"), medium: t("Medium", "درمیانی"), hard: t("Hard", "مشکل") }[value || ""] || t("Practice", "مشق"));
  return <section aria-label="Targeted Practice" className="speakflow-card p-6 h-full bg-white min-w-0">
    <h2 className="text-lg font-bold flex items-center gap-2 mb-3"><Target className="w-5 h-5 text-accent-secondary" />{t("Targeted Practice", "الفاظ کی مشق")}</h2>
    {sessionState !== "complete" ? <p className="text-sm text-text-secondary">{sessionState === "processing" ? t("Preparing exercises…", "مشق تیار ہو رہی ہے۔") : t("Complete a reading to get an exercise.", "مشق کے لیے ایک جملہ پڑھیں۔")}</p> : <div dir={ur ? "rtl" : "ltr"} className={ur ? "font-urdu text-lg leading-loose" : ""}>
      <FeedbackSource result={result} />
      <p className="text-text-secondary my-3">{t("Choose an exercise below. It becomes your next reading sentence.", "نیچے مشق منتخب کریں۔ پھر اسے پڑھیں۔")}</p>
      <p className="mb-3">{result?.encouraging_note}</p>
      <div className="space-y-3">
        {sentences.map((item, i) => <div key={i} className={`rounded-xl border p-3 flex items-start gap-2 ${selectedIndex === i ? "border-accent-secondary bg-pink-50" : "border-gray-200"}`}>
          <button aria-pressed={selectedIndex === i} onClick={() => setSelectedIndex(i)} className="flex-1 min-w-0 text-start">
            <span className={`block font-bold break-words ${ur ? "text-xl leading-loose" : "text-base"}`}>{item.text}</span>
            <span className="block text-sm text-text-secondary mt-2">{t("Word: ", "لفظ: ")}{item.target_word || item.target_phoneme || result?.focus_area} · {difficulty(item.difficulty)}</span>
          </button>
          <button onClick={() => speak(item.text, language, .9)} aria-label={t("Hear this exercise", "مشق سنیں")} className="p-2 shrink-0"><Volume2 className="w-5 h-5" /></button>
        </div>)}
      </div>
      {!sentences.length && <p>{t("No exercise is available. Try another reading.", "مشق دستیاب نہیں۔ دوبارہ پڑھیں۔")}</p>}
      <button disabled={selectedIndex === null || !sentences[selectedIndex]} onClick={() => {
        if (selectedIndex === null || !sentences[selectedIndex]) return;
        const text = sentences[selectedIndex].text;
        addAvailableSentence(text);
        setTargetSentence(text);
      }} className="w-full rounded-xl bg-accent-secondary text-white font-bold p-3 mt-4 disabled:opacity-40">{t("Read This One Next", "اب یہ جملہ پڑھیں")}</button>
    </div>}
  </section>;
}
