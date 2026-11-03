"use client";
import { toError } from "@/lib/errors";

/**
 * Story Mode — level player. One sentence per level, recorded with the mic and
 * scored by the same measurement core as every other engine (Groq→local STT,
 * librosa acoustics, alignment + morphology + extra-word penalties).
 *
 * Result screen: animated score ring, star burst, word chips with a
 * letter-by-letter inspector (Target vs You Said — adapted from the
 * story-mode reference design), Gemini coaching and a rewards celebration.
 */

import KidNav from "@/components/auth/KidNav";
import { useRecorder } from "@/hooks/useRecorder";
import {
fetchStoryFeedback,
fetchStoryPlay,
storyAnalyze,
StoryAttemptResult,StoryPlay,StoryTrack,StoryWord,
} from "@/lib/api";
import { letterDiff,LetterDiffOp } from "@/lib/letterDiff";
import { speak,stopSpeaking } from "@/lib/speech";
import { AnimatePresence,motion } from "framer-motion";
import {
ArrowLeft,ArrowRight,
Crown,
Loader2,Mic,
RotateCcw,
Sparkles,
Square,Star,
Trophy,
Volume2
} from "lucide-react";
import { useRouter,useSearchParams } from "next/navigation";
import { Suspense,useCallback,useEffect,useState,useRef } from "react";

export default function StoryPlayPageWrapper() {
  return (
    <Suspense>
      <StoryPlayPage />
    </Suspense>
  );
}

function ScoreRing({ value, passed }: { value: number; passed: boolean }) {
  const r = 40;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(100, Math.max(0, value)) / 100) * circ;
  const color = value >= 85 ? "#34C759" : value >= 70 ? "#8C6EF0" : "#FFB020";
  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#F0EDFC" strokeWidth="9" />
        <motion.circle
          cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="9" strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`text-2xl font-black ${passed ? "text-emerald-500" : "text-amber-500"}`}>{value}%</span>
      </div>
    </div>
  );
}

function StarBurst({ count, earned }: { count: number; earned: number }) {
  return (
    <div className="flex items-center justify-center gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ scale: 0, rotate: -40, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ delay: 0.4 + i * 0.35, type: "spring", stiffness: 240, damping: 12 }}
        >
          <Star
            className={`w-12 h-12 ${i < earned ? "fill-amber-400 text-amber-400 drop-shadow-[0_0_10px_rgba(250,190,40,0.7)]" : "text-gray-200"}`}
          />
        </motion.div>
      ))}
    </div>
  );
}

function ConfettiBurst() {
  const colors = ["#C9BFF0", "#F5C6D8", "#FFD54D", "#7BC96F", "#8C6EF0"];
  return (
    <div className="pointer-events-none fixed inset-0 z-40 overflow-hidden">
      {Array.from({ length: 28 }).map((_, i) => (
        <motion.span
          key={i}
          initial={{ x: "50vw", y: "-5vh", opacity: 1, scale: 1 }}
          animate={{
            x: `${8 + ((i * 37) % 84)}vw`,
            y: "110vh",
            rotate: ((i * 137) % 720) - 360,
            opacity: [1, 1, 0.8],
          }}
          transition={{ duration: 2.6 + ((i * 7) % 16) / 10, delay: ((i * 3) % 5) / 10, ease: "easeIn" }}
          className="absolute w-2.5 h-3.5 rounded-sm"
          style={{ backgroundColor: colors[i % colors.length] }}
        />
      ))}
    </div>
  );
}

/** The letter-by-letter inspector: Target row vs You Said row (story-mode design). */
function Inspector({ expected, heard, label, isUrdu }: {
  expected: string; heard: string | null; label: string | null; isUrdu: boolean;
}) {
  const ops: LetterDiffOp[] = letterDiff(expected, heard || "");
  const exact = (heard || "").replace(/[.,!?;:]/g, "").toLowerCase() === expected.replace(/[.,!?;:]/g, "").toLowerCase();

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-3xl p-5 shadow-2xl border border-indigo-900/60 bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 text-white"
    >
      <div className="flex items-center justify-between mb-4">
        <p className="text-[10px] font-black uppercase tracking-widest text-purple-300 flex items-center gap-1.5">
          <Sparkles size={13} /> Letter-by-Letter Inspector
        </p>
        <button
          onClick={() => speak(expected, isUrdu ? "ur" : "en", 0.75)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-xs font-bold transition-colors"
        >
          <Volume2 size={13} /> Hear it
        </button>
      </div>

      {heard && !exact && (
        <p className="text-xs text-slate-400 mb-3">
          You said: <span className="text-rose-300 font-bold">{heard}</span>
        </p>
      )}

      {/* Target row */}
      <p className="text-[10px] font-black uppercase tracking-widest text-emerald-300 mb-1.5">Target</p>
      <div className="flex flex-wrap gap-1 mb-4" dir={isUrdu ? "rtl" : "ltr"}>
        {ops.map((op, i) =>
          op.type === "insert" ? null : (
            <span
              key={`t${i}`}
              className={`h-8 px-2 rounded-lg font-extrabold flex items-center justify-center font-mono text-sm ${
                op.type === "match"
                  ? "bg-emerald-500/25 text-emerald-100 border border-emerald-400/40"
                  : "bg-rose-500/25 text-rose-200 border border-rose-400/40 line-through"
              }`}
            >
              {op.expected || "·"}
            </span>
          )
        )}
      </div>

      {/* You said row */}
      <p className="text-[10px] font-black uppercase tracking-widest text-sky-300 mb-1.5">You said</p>
      <div className="flex flex-wrap gap-1" dir={isUrdu ? "rtl" : "ltr"}>
        {ops.map((op, i) =>
          op.type === "delete" ? (
            <span key={`h${i}`} className="h-8 px-2 rounded-lg bg-white/5 border border-dashed border-white/20 text-slate-500 text-[10px] flex items-center justify-center font-bold uppercase">
              missing
            </span>
          ) : (
            <span
              key={`h${i}`}
              className={`h-8 px-2 rounded-lg font-extrabold flex items-center justify-center font-mono text-sm ${
                op.type === "match"
                  ? "bg-emerald-500/25 text-emerald-100 border border-emerald-400/40"
                  : "bg-sky-500/25 text-sky-100 border border-sky-400/40"
              }`}
            >
              {op.heard || "—"}
            </span>
          )
        )}
      </div>

      {label && (
        <p className="mt-4 text-xs font-bold text-amber-300" dir={isUrdu ? "rtl" : "ltr"}>
          {label === "extra word"
            ? isUrdu ? "یہ لفظ جملے میں نہیں تھا۔" : "This word is not in the sentence — read only what you see!"
            : isUrdu ? `آواز کی غلطی: ${label}` : `Sound to work on: ${label}`}
        </p>
      )}
    </motion.div>
  );
}

function StoryPlayPage() {
  const router = useRouter();
  const params = useSearchParams();
  const track = (params.get("track") === "ur" ? "ur" : "en") as StoryTrack;
  const level = Math.max(1, parseInt(params.get("level") || "1", 10) || 1);
  const isUrdu = track === "ur";
  const recorder = useRecorder();

  const [play, setPlay] = useState<StoryPlay | null>(null);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<"ready" | "recording" | "processing" | "result">("ready");
  const [result, setResult] = useState<StoryAttemptResult | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Record<string, unknown> | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [showRewards, setShowRewards] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittingRef = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        setPlay(await fetchStoryPlay(track, level));
      } catch ( caught) {
      const err = toError(caught);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [track, level]);

  useEffect(() => () => stopSpeaking(), []);

  const analyzeBlob = useCallback(async (blob: Blob) => {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setPhase("processing");
    setError(null);
    try {
      if (blob.size < 1000) throw new Error("No usable recording was captured. Please record again.");
      const result = await storyAnalyze(track, level, blob);
      setResult(result);
      setSelectedIdx(result.words.findIndex((w) => !w.correct) ?? 0);
      if (selectedIdxFallback(result)) setSelectedIdx(0);
      setPhase("result");
      setFeedbackLoading(true);
    } catch ( caught) {
      const err = toError(caught);
      submittingRef.current = false;
      setError(err.message || "Analysis failed");
      setPhase("ready");
    }

    function selectedIdxFallback(r: StoryAttemptResult) {
      return r.words.findIndex((w) => !w.correct) === -1 && r.words.length > 0;
    }
  }, [track, level]);

  const recordingSeconds = recorder.seconds;
  const isRecording = recorder.isRecording;
  const stopRecording = recorder.stop;
  useEffect(() => {
    if (phase !== "recording" || isRecording || recordingSeconds < 30) return;
    let cancelled = false;
    stopRecording().then((blob) => { if (!cancelled) void analyzeBlob(blob); });
    return () => { cancelled = true; };
  }, [phase, isRecording, recordingSeconds, stopRecording, analyzeBlob]);

  // poll Phase-2 coaching once a result exists
  useEffect(() => {
    if (phase !== "result" || !result) return;
    let cancelled = false;
    let tries = 0;
    const poll = setInterval(async () => {
      tries++;
      const fb = await fetchStoryFeedback(result.attempt_id);
      if (cancelled) return;
      if (fb) {
        setFeedback(fb);
        setFeedbackLoading(false);
        clearInterval(poll);
      } else if (tries >= 20) {
        setFeedbackLoading(false);
        clearInterval(poll);
      }
    }, 1500);
    return () => { cancelled = true; clearInterval(poll); };
  }, [phase, result]);

  const startMic = async () => {
    setError(null);
    try {
      await recorder.start();
      setPhase("recording");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Microphone access failed. Check permission and HTTPS.");
      setPhase("ready");
    }
  };

  const stopAndSubmit = async () => {
    const blob = await recorder.stop();
    if (blob.size < 1000) {
      setError(isUrdu ? "ریکارڈنگ بہت مختصر تھی — دوبارہ کوشش کریں!" : "That was too short — try reading the whole sentence!");
      setPhase("ready");
      return;
    }
    await analyzeBlob(blob);
  };

  const retry = () => {
    submittingRef.current = false;
    setResult(null);
    setFeedback(null);
    setSelectedIdx(null);
    setShowRewards(false);
    setPhase("ready");
  };

  const nextLevel = () => {
    retry();
    setLoading(true);
    router.replace(`/read/play?track=${track}&level=${level + 1}`);
  };

  const selected = selectedIdx != null && result ? result.words[selectedIdx] : null;

  return (
    <div className="min-h-screen bg-bg-base">
      <KidNav />
      <div className="max-w-2xl mx-auto px-4 pb-20">
        {/* header */}
        <div className="flex items-center justify-between pt-6 pb-4">
          <button
            onClick={() => router.push("/read")}
            className="h-10 w-10 rounded-full bg-white border-2 border-gray-100 text-text-secondary hover:text-text-primary flex items-center justify-center shadow-sm"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="text-center">
            <p className="text-[10px] font-mono font-black uppercase tracking-widest text-text-muted">
              {isUrdu ? `لیول ${level}` : `Level ${level}`}
              {play?.difficulty === "boss" && <span className="text-amber-500"> · BOSS</span>}
            </p>
            <p className={`text-sm font-black text-text-primary ${isUrdu ? "font-urdu" : ""}`} dir={isUrdu ? "rtl" : "ltr"}>
              {play?.theme ?? "…"}
            </p>
          </div>
          <div className="flex items-center gap-1 bg-white border-2 border-amber-200 rounded-full px-3 py-1">
            <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
            <span className="text-sm font-black text-amber-500 font-mono">{play?.best_stars ?? 0}</span>
          </div>
        </div>

        {loading && (
          <div className="py-24 flex justify-center">
            <Loader2 className="w-8 h-8 text-accent-primary-dark animate-spin" />
          </div>
        )}

        {error && !loading && (
          <div className="my-6 text-center text-sm text-red-500 bg-red-50 border border-red-100 rounded-xl p-4">
            {error}
            <button onClick={() => router.push("/read")} className="ml-2 underline">back to map</button>
          </div>
        )}

        {play && !loading && (
          <div className="bg-white rounded-[32px] border-2 border-gray-100 shadow-xl p-6">
            {/* sentence card */}
            <div className="rounded-2xl bg-bg-base border border-gray-100 p-6 flex flex-col items-center">
              <p
                dir={isUrdu ? "rtl" : "ltr"}
                className={`text-center text-2xl leading-relaxed font-bold text-text-primary ${isUrdu ? "font-urdu" : ""}`}
              >
                {play.sentence}
              </p>
              <button
                onClick={() => { stopSpeaking(); speak(play.sentence, isUrdu ? "ur" : "en", 0.9); }}
                disabled={recorder.isRecording || phase === "processing"}
                className="mt-4 px-4 py-2 rounded-full bg-white border border-gray-200 text-text-secondary hover:text-accent-primary-dark hover:border-accent-primary transition-colors text-sm font-bold inline-flex items-center gap-2 disabled:opacity-50"
              >
                <Volume2 className="w-4 h-4" />
                {isUrdu ? "پہلے سنیں" : "Hear it first"}
              </button>
            </div>

            {/* ready / recording / processing */}
            {phase === "ready" && (
              <div className="py-8 flex flex-col items-center">
                <button
                  onClick={startMic}
                  aria-label={isUrdu ? "ریکارڈنگ شروع کریں" : "Start recording"}
                  className={`w-20 h-20 rounded-full text-white shadow-xl flex items-center justify-center ring-8 ring-accent-primary-bg hover:scale-105 transition-transform ${
                    recorder.isRecording ? "bg-red-400 animate-pulse" : "bg-accent-primary-dark"
                  }`}
                >
                  <Mic className="w-8 h-8" />
                </button>
                <p className="text-xs font-mono uppercase tracking-widest text-text-muted mt-4">
                  {isUrdu ? "مائیک دبائیں اور زور سے پڑھیں" : "Tap the mic and read aloud"}
                </p>

              </div>
            )}

            {phase === "recording" && (
              <div className="py-8 flex flex-col items-center">
                <div className="flex items-end gap-1 h-14 mb-4">
                  {Array.from({ length: 26 }).map((_, i) => {
                    const h = Math.min(52, Math.max(8, recorder.volume * (0.4 + Math.sin(i * 0.9 + recorder.seconds) * 0.35) * (1 - Math.abs(i - 13) / 26) * 2.4) + 8);
                    return <span key={i} className="w-1.5 rounded-full bg-accent-primary" style={{ height: `${h}px` }} />;
                  })}
                </div>
                <button
                  onClick={() => { stopAndSubmit(); }}
                  aria-label={isUrdu ? "ریکارڈنگ روکیں اور جانچیں" : "Stop recording and analyze"}
                  className="w-20 h-20 rounded-full bg-red-400 text-white shadow-xl flex items-center justify-center animate-pulse"
                >
                  <Square className="w-7 h-7 fill-white" />
                </button>
                <p className="text-xs font-mono text-text-muted mt-3">
                  {String(Math.floor(recorder.seconds / 60)).padStart(2, "0")}:{String(recorder.seconds % 60).padStart(2, "0")} / 00:30
                </p>
              </div>
            )}

            {phase === "processing" && (
              <div className="py-12 flex flex-col items-center">
                <Loader2 className="w-10 h-10 text-accent-primary-dark animate-spin" />
                <p className="text-xs font-mono uppercase tracking-widest text-text-muted mt-4">
                  {isUrdu ? "جانچ ہو رہی ہے…" : "Listening closely…"}
                </p>
              </div>
            )}

            {/* ── results ── */}
            {phase === "result" && result && (
              <AnimatePresence>
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6">
                  {result.passed && <ConfettiBurst />}

                  {/* score + stars */}
                  <div className="flex flex-col items-center">
                    <ScoreRing value={result.accuracy} passed={result.passed} />
                    <p className="mt-2 text-xs font-bold text-text-secondary">{isUrdu ? "الفاظ کا ملاپ" : "Word match"}</p>
                    <div className="mt-4">
                      <StarBurst count={3} earned={result.stars} />
                    </div>
                    <p className={`mt-3 text-xl font-black ${result.passed ? "text-emerald-500" : "text-amber-500"}`}>
                      {result.passed
                        ? (isUrdu ? "شاباش!" : result.stars === 3 ? "Perfect!" : "Level cleared!")
                        : (isUrdu ? "قریب تھے — دوبارہ کوشش!" : "So close — try again!")}
                    </p>
                    <p className="text-xs text-text-muted font-mono mt-1">
                      {Math.round(result.wpm)} WPM · {result.stt_source === "groq" ? "Meta Voice STT" : "offline STT"}
                    </p>
                    <p className="mt-2 max-w-sm text-center text-xs text-text-secondary">
                      {isUrdu ? "یہ نتیجہ پہچانے گئے الفاظ پر مبنی ہے۔ لفظ غلط سنائی دے تو دوبارہ پڑھیں۔" : "If a word was heard incorrectly, try recording again."}
                    </p>
                  </div>

                  {/* word chips */}
                  <p className="text-[10px] font-mono font-black uppercase tracking-widest text-text-muted mt-6 mb-2">
                    {isUrdu ? "لفظ بہ لفظ" : "Word by Word"}
                  </p>
                  <div className="flex flex-wrap gap-2" dir={isUrdu ? "rtl" : "ltr"}>
                    {result.words.map((w: StoryWord, i) => {
                      const shown = w.spoken || w.word;
                      const isExtra = !!w.extra;
                      const tone = w.correct
                        ? "bg-emerald-50 border-emerald-200 text-emerald-600"
                        : isExtra
                        ? "bg-red-50 border-red-300 text-red-600 border-dashed"
                        : w.phoneme_mismatch
                        ? "bg-amber-50 border-amber-200 text-amber-600"
                        : "bg-red-50 border-red-200 text-red-600";
                      return (
                        <motion.button
                          key={i}
                          initial={{ opacity: 0, scale: 0.7 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: i * 0.04 }}
                          onClick={() => setSelectedIdx(i)}
                          className={`px-3 py-1.5 rounded-xl text-base font-bold border transition-shadow ${tone} ${isUrdu ? "font-urdu" : ""} ${
                            selectedIdx === i ? "ring-2 ring-accent-primary-dark shadow-md" : ""
                          }`}
                        >
                          {shown}
                        </motion.button>
                      );
                    })}
                  </div>
                  <div className="flex items-center gap-4 mt-3 mb-4 text-[10px] font-bold text-text-secondary">
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Good</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#FFB020]" /> Needs practice</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#FF4D4F]" /> Missed</span>
                  </div>

                  {/* inspector for selected word */}
                  {selected && (
                    <Inspector
                      expected={selected.word}
                      heard={selected.spoken ?? null}
                      label={selected.phoneme_mismatch ?? null}
                      isUrdu={isUrdu}
                    />
                  )}

                  {/* Gemini coaching */}
                  <div className="mt-4 flex items-start gap-3">
                    <div className="h-11 w-11 shrink-0 rounded-full bg-accent-primary-bg flex items-center justify-center text-xl">⭐</div>
                    <div className="flex-1 bg-bg-base rounded-2xl rounded-tl-sm px-4 py-3">
                      {feedbackLoading ? (
                        <p className="text-xs text-text-muted animate-pulse">
                          {isUrdu ? "مشورہ تیار ہو رہا ہے…" : "Getting your coaching tip…"}
                        </p>
                      ) : (
                        <p
                          dir={isUrdu ? "rtl" : "ltr"}
                          className={`text-sm text-text-primary leading-relaxed ${isUrdu ? "font-urdu" : ""}`}
                        >
                          {(feedback?.feedback_text as string) ||
                            (isUrdu ? "ہر کوشش آپ کو بہتر بناتی ہے!" : "Every attempt makes you stronger — keep reading aloud!")}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* actions */}
                  <div className="flex gap-3 mt-6">
                    <button
                      onClick={retry}
                      className="flex-1 py-3.5 rounded-2xl bg-white border-2 border-gray-200 text-text-primary text-sm font-bold hover:border-accent-primary inline-flex items-center justify-center gap-2"
                    >
                      <RotateCcw className="w-4 h-4" /> {isUrdu ? "دوبارہ" : "Try again"}
                    </button>
                    {result.passed ? (
                      <button
                        onClick={nextLevel}
                        className="flex-1 py-3.5 rounded-2xl bg-accent-primary-dark text-white text-sm font-bold shadow-lg hover:bg-accent-primary inline-flex items-center justify-center gap-2"
                      >
                        {level % 5 === 0
                          ? (isUrdu ? "اگلی دنیا" : "Next World")
                          : (isUrdu ? "اگلا لیول" : "Next Level")}
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <button
                        onClick={() => router.push("/read")}
                        className="flex-1 py-3.5 rounded-2xl bg-white border-2 border-gray-200 text-text-primary text-sm font-bold hover:border-accent-primary inline-flex items-center justify-center gap-2"
                      >
                        {isUrdu ? "نقشے پر واپس" : "Back to Map"}
                      </button>
                    )}
                  </div>

                  {/* world-cleared celebration */}
                  {showRewards && null}
                  {result.passed && level % 5 === 0 && (
                    <div className="mt-5 rounded-2xl bg-gradient-to-r from-amber-100 to-rose-100 border-2 border-amber-200 p-4 flex items-center gap-3">
                      <Trophy className="w-8 h-8 text-amber-500" />
                      <div>
                        <p className="font-black text-text-primary">
                          {isUrdu ? "دنیا مکمل!" : "World cleared!"}
                        </p>
                        <p className="text-xs text-text-secondary">
                          {isUrdu ? "اگلی دنیا کھل گئی ہے — نئے موضوع، نئے جملے!" : "A new world just unlocked — new theme, new sentences!"}
                        </p>
                      </div>
                      <Crown className="w-7 h-7 text-amber-500 ml-auto" />
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
