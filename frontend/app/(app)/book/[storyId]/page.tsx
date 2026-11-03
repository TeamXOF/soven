"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import Image from "next/image";
import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, BookOpen, CheckCircle2, Mic, RotateCcw, Settings, Square, Volume2, VolumeX } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { analyzeCheckpoint, createSession, fetchFeedback, fetchSessionDetail, fetchWordTip, getStoredToken, type WordTip, type CreatedSession, type Phase1Response, type Phase2Response } from "@/lib/api";
import { useRecorder } from "@/hooks/useRecorder";
import { bookArt } from "@/lib/book-art";
import { speak, stopSpeaking } from "@/lib/speech";
import { useReaderActivity } from "@/components/soven/ReaderActivity";
import OfflineNotice from "@/components/soven/OfflineNotice";
import type { ReadingLanguage } from "@/lib/languages";
type Stage = "ready" | "opening" | "recording" | "processing" | "done";
export default function BookReader() {
    const { user } = useAuth();
    const { setBusy: setGlobalBusy } = useReaderActivity();
    const params = useParams<{
        storyId: string;
    }>();
    const query = useSearchParams();
    const storyId = params.storyId;
    const requested = query.get("lang");
    const validLanguage = requested === null || requested === "en" || requested === "ur" || requested === "es";
    const language: ReadingLanguage = requested === "ur" ? "ur" : requested === "es" ? "es" : "en";
    const es = language === "es";
    const ur = language === "ur";
    const resume = query.get("session");
    const userId = user?.id;
    const [session, setSession] = useState<CreatedSession | null>(null);
    const [index, setIndex] = useState(0);
    const [stage, setStage] = useState<Stage>("ready");
    const [result, setResult] = useState<Phase1Response | null>(null);
    const [feedback, setFeedback] = useState<Phase2Response | null>(null);
    const [error, setError] = useState("");
    const [speechError, setSpeechError] = useState("");
    const [tip, setTip] = useState<WordTip | null>(null);
    const [tipLoading, setTipLoading] = useState(false);
    const [tipError, setTipError] = useState("");
    const [selectedWord, setSelectedWord] = useState<string | null>(null);
    const [finished, setFinished] = useState(false);
    const [loading, setLoading] = useState(false);
    const recorder = useRecorder(30);
    const generation = useRef(0);
    const lock = useRef(false);
    const micEpoch = useRef(0);
    const alive = useRef(true);
    const { cancel } = recorder;
    const invalidate = useCallback(() => { generation.current++; cancel(); stopSpeaking(); }, [cancel]);
    const art = bookArt(storyId);
    const prefs = user?.profile?.accessibility;
    const page = session?.checkpoints[index];
    const busy = stage === "opening" || stage === "recording" || stage === "processing";
    useDeferredEffect(() => { setGlobalBusy(busy); return () => setGlobalBusy(false); }, [busy, setGlobalBusy]);
    const title = storyId === "story_space_02" ? (ur ? "چھوٹا راکٹ" : es ? "El pequeño cohete" : "The Little Rocket") : storyId === "story_ocean_03" ? (ur ? "گانے والی وہیل" : es ? "La ballena cantante" : "The Singing Whale") : (ur ? "بہادر چھوٹا لومڑ" : es ? "El zorrito valiente" : "The Brave Little Fox");
    useDeferredEffect(() => {
        alive.current = true;
        generation.current++;
        setSession(null);
        setResult(null);
        setFeedback(null);
        setStage("ready");
        setFinished(false);
        setIndex(0);
        setError("");
        lock.current = false;
        cancel();
        const epoch = generation.current;
        const token = getStoredToken();
        if (resume && userId) {
            setLoading(true);
            fetchSessionDetail(resume).then(detail => {
                if (!alive.current || generation.current !== epoch || getStoredToken() !== token)
                    return;
                if (detail.story_id !== storyId || detail.language !== language)
                    throw new Error("This saved reading belongs to a different book or language.");
                setSession({ session_id: detail.session_id, student_id: detail.student_id, story_id: detail.story_id, language: detail.language, created_at: detail.created_at, checkpoints: detail.checkpoints });
                const first = detail.checkpoints.findIndex(p => !p.passed);
                setIndex(first < 0 ? 0 : first);
            }).catch(e => {
                if (generation.current === epoch)
                    setError(e.message);
            }).finally(() => {
                if (generation.current === epoch)
                    setLoading(false);
            });
        }
        return () => { alive.current = false; invalidate(); };
    }, [userId, storyId, language, resume, cancel, invalidate]);
    useDeferredEffect(() => {
        if (!selectedWord)
            return;
        let active = true;
        const token = getStoredToken();
        const epoch = generation.current;
        setTip(null);
        setTipError("");
        setTipLoading(true);
        fetchWordTip(selectedWord, language).then(data => {
            if (active && generation.current === epoch && getStoredToken() === token)
                setTip(data);
        }).catch(() => {
            if (active && generation.current === epoch)
                setTipError(ur ? "لفظ کی مزید رہنمائی دستیاب نہیں۔" : "A word tip is unavailable. You can still listen or try reading it again.");
        }).finally(() => { if (active && generation.current === epoch)
            setTipLoading(false); });
        return () => { active = false; };
    }, [selectedWord, language, ur]);
    async function startBook() {
        if (!user?.student_id || lock.current || !validLanguage)
            return;
        lock.current = true;
        setLoading(true);
        setError("");
        const epoch = generation.current;
        const token = getStoredToken();
        try {
            const data = await createSession(user.student_id, storyId, language);
            if (alive.current && generation.current === epoch && getStoredToken() === token) {
                setSession(data);
                setIndex(0);
            }
        }
        catch (e) {
            if (alive.current && generation.current === epoch)
                setError(e instanceof Error ? e.message : "Could not open the book.");
        }
        finally {
            if (generation.current === epoch) {
                lock.current = false;
                setLoading(false);
            }
        }
    }
    async function startReading() {
        if (lock.current || !page)
            return;
        lock.current = true;
        stopSpeaking();
        setSpeechError("");
        setError("");
        setResult(null);
        setFeedback(null);
        setSelectedWord(null);
        setStage("opening");
        const epoch = ++generation.current;
        micEpoch.current = epoch;
        try {
            await recorder.start();
            if (alive.current && generation.current === epoch)
                setStage("recording");
        }
        catch (e) {
            if (alive.current && generation.current === epoch) {
                setError(e instanceof Error ? e.message : "Microphone unavailable. Please retry.");
                setStage("ready");
                lock.current = false;
            }
        }
    }
    const analyze = useCallback(async (audio: Blob) => {
        if (!session || !page)
            return;
        const epoch = micEpoch.current;
        const token = getStoredToken();
        const current = () => alive.current && generation.current === epoch && getStoredToken() === token;
        setStage("processing");
        try {
            if (!audio.size)
                throw new Error("The recording was empty. Please try again.");
            const response = await analyzeCheckpoint(session.session_id, page.checkpoint_id, audio);
            if (!current())
                return;
            setResult(response);
            setStage("done");
            lock.current = false;
            if (prefs?.coach_enabled !== false) {
                for (let attempt = 0; attempt < 10; attempt++) {
                    const advice = await fetchFeedback(session.session_id, page.checkpoint_id);
                    if (!current())
                        return;
                    if (advice) {
                        setFeedback(advice);
                        break;
                    }
                    await new Promise(resolve => setTimeout(resolve, 750));
                }
            }
        }
        catch (e) {
            if (current()) {
                setError(e instanceof Error ? e.message : "Could not analyze this reading.");
                setStage(result ? "done" : "ready");
                lock.current = false;
            }
        }
    }, [session, page, prefs, result]);
    useDeferredEffect(() => {
        if (recorder.blob && stage === "recording") {
            setStage("processing");
            void analyze(recorder.blob);
        }
    }, [recorder.blob, stage, analyze]);
    function play(text: string) {
        if (busy)
            return;
        setSpeechError(speak(text, language) ? "" : ur ? "اس آلے پر اردو کی آواز دستیاب نہیں۔" : "A voice for this language is not available on this device. You can still read aloud.");
    }
    function reset() { generation.current++; cancel(); stopSpeaking(); lock.current = false; setStage("ready"); setResult(null); setFeedback(null); setSelectedWord(null); setError(""); }
    function next() {
        if (busy || !result?.passed || !session)
            return;
        reset();
        if (index === session.checkpoints.length - 1)
            setFinished(true);
        else
            setIndex(i => i + 1);
    }
    const flagged = result?.words.filter(w => !w.correct) ?? [];
    const status = stage === "opening" ? (ur ? "مائیکروفون کی اجازت درکار ہے۔" : "Waiting for microphone permission…") : stage === "recording" ? (ur ? "پڑھیں، پھر روکیں اور موازنہ کریں۔" : "Read aloud, then stop to see your word feedback.") : stage === "processing" ? (ur ? "الفاظ کا موازنہ ہو رہا ہے…" : "Comparing the recognized words with this page…") : stage === "done" ? (ur ? "ریڈنگ مکمل۔ الفاظ دیکھیں یا دوبارہ کوشش کریں۔" : "Reading complete. Review the words, or try this page again.") : (ur ? "تیار ہوں تو مائیکروفون دبائیں۔" : "Tap the microphone when you’re ready.");
    if (!validLanguage)
        return <div className="soven-error" role="alert">This reading language is not available. <Link href="/languages">Choose English or Urdu</Link>.</div>;
    return <div className="soven-reader"><OfflineNotice /><header className="soven-reader-toolbar"><div className="soven-reader-title"><Link href="/books" aria-label="Back to books" className="soven-icon-button"><ArrowLeft size={18}/></Link><div><h1 className={ur ? "font-urdu" : ""}>{title}</h1><p>{ur ? "اردو" : "English"} · {session ? `${ur ? "صفحہ" : "Page"} ${index + 1} / ${session.checkpoints.length}` : ur ? "اپنی رفتار سے پڑھیں" : "A story at your own pace"}</p></div></div><div className="soven-reader-actions"><button disabled={busy || !page} className="soven-icon-button" aria-label="Listen to this page" onClick={() => page && play(page.target_text)}><Volume2 size={18}/></button><button className="soven-icon-button" aria-label="Stop spoken playback" onClick={stopSpeaking}><VolumeX size={18}/></button><Link href="/profile" className="soven-icon-button" aria-label="Reading preferences"><Settings size={18}/></Link></div></header>
  {error && <p role="alert" className="soven-error mb-5">{error}</p>}{speechError && <p role="status" className="soven-note mb-5">{speechError}</p>}
  {finished ? <section className="soven-form-card max-w-xl mx-auto soven-success"><CheckCircle2 size={42}/><h1>{ur ? "آپ نے کتاب مکمل کر لی!" : "You’ve reached the last page."}</h1><p>{ur ? "ہر صفحہ آپ کی محفوظ ریڈنگ میں شامل ہے۔" : "Your page results are saved. Take a moment to enjoy that small achievement."}</p><Link href="/books" className="soven-button">{ur ? "کتابوں کی طرف واپس" : "Back to your bookshelf"}<ArrowRight size={17}/></Link></section> : <div className="soven-book-stage"><article className="soven-spread"><div className="soven-page-art"><Image src={art.image} alt={title + " story illustration"} fill priority sizes="(max-width: 800px) 100vw, 450px"/></div><div className="soven-page-content"><p className="soven-eyebrow">{ur ? "ایک چھوٹی مہم" : "A LITTLE ADVENTURE"}</p><h2>{session ? (ur ? `صفحہ ${index + 1}` : `Chapter ${index + 1}`) : ur ? "کہانی شروع کریں" : "Let’s turn the first page."}</h2>
    {!session ? <div className="soven-empty"><BookOpen size={30}/><p>{ur ? art.ur : art.description}</p><p>{ur ? "ہر صفحے پر ایک جملہ پڑھیں۔ ریکارڈنگ سرور کو بھیجی جائے گی اور نتیجہ آپ کے اکاؤنٹ میں محفوظ ہو گا۔" : "Read one sentence on each page. Recordings are sent to the server for analysis and results are saved to your account."}</p><button className="soven-button" disabled={loading} onClick={startBook}>{loading ? "Opening your book…" : ur ? "پڑھنا شروع کریں" : "Open this book"}<ArrowRight size={17}/></button></div> : <><div className={`soven-reading-text ${ur ? "font-urdu" : ""}`} data-larger={prefs?.larger_text ?? false} dir={ur ? "rtl" : "ltr"} style={{ lineHeight: prefs?.line_spacing === "wide" ? (ur ? 3.2 : 2.5) : prefs?.line_spacing === "comfortable" ? (ur ? 2.9 : 2.2) : undefined }}>{result ? result.words.map((w, i) => <button key={i} disabled={busy || prefs?.word_tips === false} data-correct={w.correct} aria-label={`${w.word}: ${w.correct ? "matched" : `recognized ${w.spoken || "missing"}`}`} onClick={() => { setSelectedWord(w.word); play(w.word); }}>{w.word}</button>) : page?.target_text}</div><div className="soven-recorder-row">{stage === "recording" ? <button className="soven-mic" aria-label="Stop and analyze reading" aria-pressed="true" onClick={() => void recorder.stop()}><Square size={22} fill="currentColor"/></button> : <button className="soven-mic" aria-label="Record this page" disabled={busy} onClick={startReading}><Mic size={27}/></button>}<div><p role="status" aria-live="polite" className="soven-status">{status}</p><span className="soven-timer">{recorder.seconds}s / 30s</span></div></div><nav className="soven-page-navigation" aria-label="Book page navigation"><button disabled={busy} className="soven-text-link" onClick={reset}><RotateCcw size={15}/>{ur ? "دوبارہ کوشش" : "Try again"}</button><span className="soven-fine">{index + 1} / {session.checkpoints.length}</span><button disabled={busy || !result?.passed} className="soven-button soven-button-small" onClick={next}>{ur ? "اگلا صفحہ" : "Next page"}<ArrowRight size={16}/></button></nav></>}
    </div></article><aside className="soven-reader-side"><section className="soven-panel"><h2>{ur ? "آپ کی ریڈنگ" : "Your reading"}</h2><p>{ur ? "ریکارڈنگ کے بعد نتیجہ یہاں آئے گا۔" : "Read aloud to see your own results here."}</p>{result ? <><p className="soven-score">{Math.round(result.accuracy)}%</p><p>{ur ? "الفاظ کی مطابقت" : "Word match"}</p><div className="soven-progress-bar"><span style={{ width: `${Math.max(0, Math.min(100, result.accuracy))}%` }}/></div><p>{Math.round(result.wpm)} {ur ? "الفاظ فی منٹ" : "words per minute"} · {ur ? "رفتار پر اسکور کم نہیں ہوتا۔" : "No speed penalty."}</p><p className="soven-fine mt-3">{ur ? "شناخت شدہ الفاظ کا صفحے سے موازنہ، تلفظ کی تشخیص نہیں۔" : "Recognized words compared with the page, not a pronunciation diagnosis."}</p><p className="soven-fine mt-2">{result.stt_source === "local_fallback" ? "Server-local speech recognition" : "Hosted speech recognition"}</p><p className="soven-fine mt-2">{ur ? "وقفے" : "Pauses"}: <span>{result.speech_evidence?.pause_assessment === "available" ? result.hesitations.length : (ur ? "دستیاب نہیں" : "Unavailable")}</span></p>{result.warnings.map((w, i) => <p className="soven-note mt-3" key={i}>{w}</p>)}</> : <div className="soven-empty"><Mic size={25}/><p>{ur ? "تیار ہوں تو ریکارڈ کریں۔" : "Your voice, your pace. Record when you’re ready."}</p></div>}{selectedWord && <div className="soven-word-help" dir={ur ? "rtl" : "ltr"}>{ur ? "سننے کے لیے چنا گیا لفظ" : "Selected word"}: <strong>{selectedWord}</strong>{tipLoading ? <p role="status">{ur ? "رہنمائی آ رہی ہے…" : "Loading a word tip…"}</p> : tip ? <><p>{tip.tip}</p><p className="soven-fine">{tip.tip_source === "template" ? (ur ? "بنیادی رہنمائی" : "Basic word guidance") : tip.tip_source === "cache" ? (ur ? "محفوظ رہنمائی" : "Cached word guidance") : (ur ? "تیار کردہ رہنمائی" : "Generated word guidance")}</p></> : tipError ? <p role="status">{tipError}</p> : null}</div>}</section><section className="soven-panel"><h2>{ur ? "الفاظ اور رہنمائی" : "Practice & feedback"}</h2>{flagged.length ? flagged.map((w, i) => <div className="soven-review-row" dir="auto" key={i}><strong>{w.word}</strong><ArrowRight size={12}/><span>{w.spoken || (ur ? "سنائی نہیں دیا" : "Not recognized")}</span></div>) : <p>{result ? (ur ? "کوئی نشان زدہ لفظ نہیں۔" : "No flagged target words in this reading.") : (ur ? "ریکارڈنگ کے بعد الفاظ کا موازنہ دیکھیں۔" : "Your word comparisons appear after recording.")}</p>}{result && <div className="soven-coach">{prefs?.coach_enabled === false ? <p>{ur ? "رہنمائی بند ہے۔ ترجیحات میں بدلیں۔" : "Guidance is turned off in your preferences."}</p> : feedback ? <><p>{feedback.feedback_text}</p><button disabled={busy} className="soven-text-link mt-3" onClick={() => play(feedback.feedback_text || "")}><Volume2 size={15}/>{ur ? "رہنمائی سنیں" : "Hear guidance"}</button><p className="soven-fine">{feedback.feedback_source === "template_fallback" ? (ur ? "بنیادی رہنمائی" : "Basic fallback guidance") : (ur ? "تیار کردہ رہنمائی" : "Generated guidance")}</p></> : <p>{ur ? "نشان زدہ الفاظ آہستہ پڑھیں اور دوبارہ کوشش کریں۔ مزید رہنمائی دستیاب نہ ہو تو بھی مشق جاری رکھیں۔" : "Take a moment with the marked words, then try this page again. Additional guidance may be unavailable."}</p>}</div>}</section></aside></div>}
  </div>;
}
