"use client";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { BookOpen, Loader2 } from "lucide-react";

export default function AIDiagnosisCard() {
  const { sessionState, accuracy, scoredWords, language, controlsLocked } = useSpeakFlow();
  const ur = language === "ur";
  const t = (en: string, text: string) => ur ? text : en;
  const flagged = scoredWords.filter(word => !word.correct);
  return (
    <section aria-label="Your Reading" className="speakflow-card p-6 bg-white h-full min-w-0">
      <h2 className="text-lg font-bold flex items-center gap-2 mb-4"><BookOpen className="w-5 h-5 text-accent-primary-dark" />{t("Your Reading", "آپ کی پڑھائی")}</h2>
      {sessionState !== "complete" ? (
        <div className={ur ? "font-urdu text-lg leading-loose" : "text-sm leading-relaxed"} dir={ur ? "rtl" : "ltr"} role="status">
          {sessionState === "processing" && <Loader2 className="w-6 h-6 animate-spin mb-3" />}
          {sessionState === "processing" ? t("Comparing the sentence with the recording…", "ریکارڈنگ اور جملے کا موازنہ ہو رہا ہے۔")
            : controlsLocked ? t("Finish recording to see the words to review.", "ریکارڈنگ مکمل ہونے پر الفاظ کا موازنہ دکھایا جائے گا۔")
            : t("Read a sentence to see your word match and words to review.", "ایک جملہ پڑھیں۔ پھر الفاظ کا موازنہ یہاں دیکھیں۔")}
        </div>
      ) : (
        <div dir={ur ? "rtl" : "ltr"} className={ur ? "font-urdu leading-loose" : ""}>
          <p role="status" className="text-sm text-status-complete mb-3">{t("Reading complete · saved", "پڑھنا مکمل ہو گیا۔ نتیجہ محفوظ ہے۔")}</p>
          <div className="rounded-xl bg-accent-primary-bg p-4 mb-5">
            <p className="font-bold">{t("Word Match", "الفاظ کا موازنہ")}</p>
            <p className="text-3xl font-bold mt-2" data-testid="reading-word-match">{accuracy ?? "—"}%</p>
            <p className="text-sm text-text-secondary mt-2">{t("How closely the recognized words match the sentence. Recognition can miss or change words.", "یہ جملے اور پہچانے گئے الفاظ کا موازنہ ہے۔ آواز کی پہچان میں بھی فرق آ سکتا ہے۔")}</p>
          </div>
          <h3 className="font-bold mb-3">{t("Words to review", "دوبارہ پڑھنے کے الفاظ")}</h3>
          {flagged.length === 0 ? <p className="text-text-secondary">{t("All words matched in this recording.", "اس ریکارڈنگ میں تمام الفاظ مل گئے۔")}</p> : (
            <div className="space-y-3">
              {flagged.map((word, index) => (
                <dl key={index} className="rounded-lg border border-amber-200 bg-amber-50 p-3 break-words" data-testid="review-word">
                  <div><dt className="text-xs text-text-secondary inline">{t("In the sentence: ", "جملے میں: ")}</dt><dd className="inline font-bold">{word.extra ? t("(extra word)", "اضافی لفظ") : word.word}</dd></div>
                  <div className="mt-1"><dt className="text-xs text-text-secondary inline">{t("Recognized: ", "پہچانا گیا: ")}</dt><dd className="inline">{word.spoken || t("Not recognized", "پہچانا نہیں گیا")}</dd></div>
                </dl>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
