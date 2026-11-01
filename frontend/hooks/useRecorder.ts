"use client";
import { loadPrefs } from "@/lib/prefs";
import { useCallback, useEffect, useRef, useState } from "react";
/** Bounded capture, including delayed permission and unmount cancellation. */
export function useRecorder(limitSeconds = 30) {
    const [isRecording, setIsRecording] = useState(false);
    const [volume, setVolume] = useState(0);
    const [seconds, setSeconds] = useState(0);
    const [blob, setBlob] = useState<Blob | null>(null);
    const recorder = useRef<MediaRecorder | null>(null);
    const stream = useRef<MediaStream | null>(null);
    const context = useRef<AudioContext | null>(null);
    const frame = useRef<number | null>(null);
    const timer = useRef<ReturnType<typeof setInterval> | null>(null);
    const chunks = useRef<Blob[]>([]);
    const generation = useRef(0);
    const pending = useRef(false);
    const last = useRef<Blob | null>(null);
    const waiters = useRef<((value: Blob) => void)[]>([]);
    const cleanup = useCallback(() => {
        if (frame.current !== null)
            cancelAnimationFrame(frame.current);
        if (timer.current)
            clearInterval(timer.current);
        context.current?.close().catch(() => { });
        stream.current?.getTracks().forEach(t => t.stop());
        frame.current = null;
        timer.current = null;
        context.current = null;
        stream.current = null;
    }, []);
    const cancel = useCallback(() => {
        generation.current++;
        pending.current = false;
        const r = recorder.current;
        if (r && r.state !== "inactive") {
            r.onstop = null;
            r.stop();
        }
        cleanup();
        recorder.current = null;
        chunks.current = [];
        last.current = null;
        for (const resolve of waiters.current)
            resolve(new Blob());
        waiters.current = [];
        setIsRecording(false);
        setVolume(0);
        setBlob(null);
    }, [cleanup]);
    useEffect(() => () => {
        generation.current++;
        pending.current = false;
        const r = recorder.current;
        if (r && r.state !== "inactive") {
            r.onstop = null;
            r.stop();
        }
        cleanup();
        for (const resolve of waiters.current)
            resolve(new Blob());
        waiters.current = [];
    }, [cleanup]);
    const start = useCallback(async () => {
        if (pending.current || recorder.current?.state === "recording")
            return;
        if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined")
            throw new Error("Recording requires a supported browser on HTTPS or localhost.");
        pending.current = true;
        const epoch = ++generation.current;
        setBlob(null);
        last.current = null;
        setSeconds(0);
        try {
            let audio: MediaStream;
            const saved = loadPrefs().preferredMic;
            try {
                audio = await navigator.mediaDevices.getUserMedia({ audio: { noiseSuppression: false, ...(saved ? { deviceId: { exact: saved } } : {}) } });
            }
            catch (error) {
                if (!saved)
                    throw error;
                audio = await navigator.mediaDevices.getUserMedia({ audio: { noiseSuppression: false } });
            }
            if (generation.current !== epoch) {
                audio.getTracks().forEach(t => t.stop());
                return;
            }
            stream.current = audio;
            chunks.current = [];
            const ctx = new window.AudioContext();
            context.current = ctx;
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;
            ctx.createMediaStreamSource(audio).connect(analyser);
            const data = new Uint8Array(analyser.frequencyBinCount);
            const tick = () => {
                if (generation.current !== epoch)
                    return;
                analyser.getByteFrequencyData(data);
                setVolume(data.reduce((a, v) => a + v, 0) / data.length);
                frame.current = requestAnimationFrame(tick);
            };
            tick();
            let r: MediaRecorder;
            try {
                r = new MediaRecorder(audio, { audioBitsPerSecond: 128000 });
            }
            catch {
                r = new MediaRecorder(audio);
            }
            recorder.current = r;
            r.ondataavailable = e => {
                if (generation.current === epoch && e.data.size)
                    chunks.current.push(e.data);
            };
            r.onstop = () => {
                if (generation.current !== epoch)
                    return;
                const captured = new Blob(chunks.current, { type: r.mimeType || "audio/webm" });
                last.current = captured;
                cleanup();
                setVolume(0);
                setIsRecording(false);
                setBlob(captured);
                for (const resolve of waiters.current)
                    resolve(captured);
                waiters.current = [];
            };
            r.start(100);
            setIsRecording(true);
            let elapsed = 0;
            timer.current = setInterval(() => {
                setSeconds(++elapsed);
                if (elapsed >= limitSeconds && r.state === "recording")
                    r.stop();
            }, 1000);
        }
        catch (error) {
            if (generation.current === epoch) {
                cleanup();
                setVolume(0);
                setIsRecording(false);
            }
            throw error;
        }
        finally {
            if (generation.current === epoch)
                pending.current = false;
        }
    }, [cleanup, limitSeconds]);
    const stop = useCallback((): Promise<Blob> => {
        const r = recorder.current;
        if (!r || r.state === "inactive")
            return Promise.resolve(last.current ?? new Blob(chunks.current, { type: r?.mimeType || "audio/webm" }));
        return new Promise(resolve => { waiters.current.push(resolve); r.stop(); });
    }, []);
    return { isRecording, volume, seconds, blob, start, stop, cancel };
}
