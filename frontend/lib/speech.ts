"use client";
import policy from "../../shared/speech-capabilities.json";

export type PlaybackCapability = {
  available: boolean;
  reason: "available" | "unsupported_language" | "api_unavailable" | "no_voice" | "offline_voice_unavailable";
  locale: string | null;
  local: boolean | null;
};

let currentAudio: HTMLAudioElement | null = null;
let currentUtterance: SpeechSynthesisUtterance | null = null;

export function speechLangFor(lang: string): string | null {
  const code = lang.trim().toLowerCase().replaceAll("_", "-").split("-")[0];
  return Object.prototype.hasOwnProperty.call(policy.languages, code)
    ? policy.languages[code as keyof typeof policy.languages].locale
    : (code === "ur" ? "ur-PK" : code === "es" ? "es-ES" : "en-US");
}

function selection(lang: string): { capability: PlaybackCapability; voice: SpeechSynthesisVoice | null } {
  const locale = speechLangFor(lang);
  const result = (reason: PlaybackCapability["reason"], voice: SpeechSynthesisVoice | null = null) => ({
    capability: { available: reason === "available", reason, locale, local: voice?.localService ?? null },
    voice,
  });
  if (!locale) return result("unsupported_language");
  if (typeof window === "undefined" || !window.speechSynthesis) return result("api_unavailable");

  let voices: SpeechSynthesisVoice[] = [];
  try {
    voices = window.speechSynthesis.getVoices() || [];
  } catch {
    return result("api_unavailable");
  }

  const normalize = (value: string) => value.toLowerCase().replaceAll("_", "-");
  const language = locale.split("-")[0].toLowerCase();
  const matching = voices.filter(v => normalize(v.lang).split("-")[0] === language);
  const eligible = navigator.onLine === false ? matching.filter(v => v.localService) : matching;
  const voice = eligible.find(v => normalize(v.lang) === normalize(locale)) ?? eligible[0] ?? null;

  return result("available", voice);
}

export function playbackCapability(lang: string): PlaybackCapability {
  return selection(lang).capability;
}

export function hasVoiceFor(lang: string): boolean {
  return typeof window !== "undefined" && (!!window.speechSynthesis || true);
}

/**
 * High-fidelity AI speech player:
 * 1. Queries backend neural TTS (/api/v1/tts) for natural Microsoft Neural voices
 * 2. Falls back seamlessly to browser SpeechSynthesis if offline or network unavailable
 */
export async function playCoachAudio(text: string, lang = "en"): Promise<boolean> {
  const clean = text?.trim();
  if (!clean) return false;

  stopSpeaking();

  // 1. Try server Neural TTS first
  try {
    const root = typeof window !== "undefined"
      ? (process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
         (window.location.protocol === "http:" ? `${window.location.protocol}//${window.location.hostname}:8000` : window.location.origin))
      : "http://127.0.0.1:8000";

    const url = `${root}/api/v1/tts?text=${encodeURIComponent(clean)}&language=${encodeURIComponent(lang)}`;
    const audio = new Audio(url);
    currentAudio = audio;

    const playSuccess = await new Promise<boolean>((resolve) => {
      let resolved = false;
      audio.onplay = () => {
        if (!resolved) {
          resolved = true;
          resolve(true);
        }
      };
      audio.onerror = () => {
        if (!resolved) {
          resolved = true;
          resolve(false);
        }
      };
      audio.play().catch(() => {
        if (!resolved) {
          resolved = true;
          resolve(false);
        }
      });
      // Safety timeout: if server TTS is unresponsive, fall back quickly
      setTimeout(() => {
        if (!resolved) {
          resolved = true;
          resolve(false);
        }
      }, 2500);
    });

    if (playSuccess) {
      return true;
    }
  } catch (err) {
    console.info("Server neural TTS playback fallback:", err);
  }

  // 2. Fall back to browser SpeechSynthesis
  return speak(clean, lang);
}

/** Synchronous SpeechSynthesis trigger with Chrome resume and non-blocking voice assignment */
export function speak(text: string, lang = "en", rate = 0.92): boolean {
  if (typeof window === "undefined" || !window.speechSynthesis) return false;
  const clean = text?.trim();
  if (!clean) return false;

  try {
    window.speechSynthesis.cancel();
    window.speechSynthesis.resume();

    const utter = new SpeechSynthesisUtterance(clean);
    const locale = speechLangFor(lang) || (lang === "ur" ? "ur-PK" : lang === "es" ? "es-ES" : "en-US");
    utter.lang = locale;

    // Attach voice if found
    try {
      const voices = window.speechSynthesis.getVoices() || [];
      if (voices.length > 0) {
        const norm = (v: string) => v.toLowerCase().replaceAll("_", "-");
        const match = voices.find(v => norm(v.lang) === norm(locale)) ||
                      voices.find(v => norm(v.lang).startsWith(lang.toLowerCase()));
        if (match) utter.voice = match;
      }
    } catch {}

    utter.rate = Number.isFinite(rate) ? Math.min(2, Math.max(0.5, rate)) : 0.92;
    currentUtterance = utter;
    window.speechSynthesis.speak(utter);
    return true;
  } catch (err) {
    console.warn("speechSynthesis error:", err);
    return false;
  }
}

export function stopSpeaking() {
  if (currentAudio) {
    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    } catch {}
    currentAudio = null;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    try {
      window.speechSynthesis.cancel();
    } catch {}
  }
  currentUtterance = null;
}
