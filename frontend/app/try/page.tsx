"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import Link from "next/link";
import { useRef, useState } from "react";
import { Mic, Square, RotateCcw, ArrowRight, ShieldCheck } from "lucide-react";
import Brand from "@/components/soven/Brand";
import { useRecorder } from "@/hooks/useRecorder";
export default function MicrophoneSample() {
    const recorder = useRecorder(20);
    const [language, setLanguage] = useState<"en" | "ur">("en");
    const [url, setUrl] = useState("");
    const [error, setError] = useState("");
    const [opening, setOpening] = useState(false);
    const alive = useRef(true);
    const locked = useRef(false);
    const ur = language === "ur";
    useDeferredEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
    useDeferredEffect(() => {
        if (!recorder.blob)
            return;
        const source = URL.createObjectURL(recorder.blob);
        setUrl(source);
        return () => URL.revokeObjectURL(source);
    }, [recorder.blob]);
    async function record() {
        if (locked.current)
            return;
        locked.current = true;
        setOpening(true);
        setError("");
        setUrl("");
        try {
            await recorder.start();
        }
        catch (e) {
            if (alive.current)
                setError(e instanceof Error ? e.message : "Could not open your microphone. Check permission and try again.");
        }
        finally {
            locked.current = false;
            if (alive.current)
                setOpening(false);
        }
    }
    return <div className="soven-auth-page"><header className="soven-public-nav"><Brand /><Link href="/signup">Skip & create an account →</Link></header><main className="soven-sample"><p className="soven-eyebrow">A SMALL HELLO FROM YOUR MICROPHONE</p><h1>{ur ? "اپنی آواز سنیں" : "Let’s hear your reading voice."}</h1><p>{ur ? "جملہ پڑھیں، پھر اپنی ریکارڈنگ سنیں۔ یہ صرف مائیکروفون چیک ہے۔" : "Read a sentence, then listen back. This is a microphone check, not a reading assessment."}</p><div className="soven-language-switch justify-center mt-6"><button disabled={opening || recorder.isRecording} aria-pressed={!ur} onClick={() => setLanguage("en")}>English</button><button disabled={opening || recorder.isRecording} aria-pressed={ur} onClick={() => setLanguage("ur")}>اردو</button></div><div className="soven-sample-sentence"><span className="soven-eyebrow">{ur ? "بلند آواز میں پڑھیں" : "READ THIS SENTENCE ALOUD"}</span><p className={ur ? "font-urdu" : ""} dir={ur ? "rtl" : "ltr"}>{ur ? "چھوٹا لومڑ صبح جلدی اٹھا۔" : "The little fox woke up early in the morning."}</p></div>
    {recorder.isRecording ? <button className="soven-mic" aria-label="Stop microphone check" aria-pressed="true" onClick={() => void recorder.stop()}><Square fill="currentColor" size={26}/></button> : <button className="soven-mic" disabled={opening} aria-label="Start microphone check" onClick={record}><Mic size={31}/></button>}
    <div className="soven-wave" aria-hidden="true">{Array.from({ length: 19 }, (_, i) => <span key={i} style={{ height: recorder.isRecording ? `${6 + (recorder.volume / 255) * Math.max(6, 32 - Math.abs(i - 9) * 2)}px` : "5px" }}/>)}</div><p role="status" className="soven-status">{opening ? "Waiting for microphone permission…" : recorder.isRecording ? `${recorder.seconds}s / 20s · Read at your own pace, then stop.` : url ? "Recording complete. Listen back, or try another take." : "Tap the microphone when you’re ready. Stops after 20 seconds."}</p>
    {url && <div className="soven-panel mt-6"><audio controls src={url} className="w-full" aria-label="Your microphone check recording"/><button className="soven-text-link mt-5" onClick={() => { setUrl(""); recorder.cancel(); }}><RotateCcw size={15}/>Try another take</button></div>}{error && <p role="alert" className="soven-error mt-5">{error}</p>}<p className="soven-fine justify-center my-6"><ShieldCheck size={15}/>This check stays in this browser. No upload, no score, no saved recording.</p><Link href="/signup" className="soven-button">{ur ? "اکاؤنٹ بنائیں" : "Create your reading space"}<ArrowRight size={17}/></Link><p className="soven-fine justify-center mt-4">Word feedback becomes available after you sign in with an approved account.</p></main></div>;
}
