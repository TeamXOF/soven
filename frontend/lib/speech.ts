"use client";

/**
 * Text-to-speech via the browser's built-in speechSynthesis; voices may use the network,
 * no API key. Used to model the target sentence and to let a child hear a
 * single word. Voice availability for a language varies by device (English is
 * everywhere; Urdu voices exist on Windows/Edge and many Android devices).
 */

let voicesCache: SpeechSynthesisVoice[] = [];

function refreshVoices() {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  voicesCache = window.speechSynthesis.getVoices();
}
if (typeof window !== "undefined" && window.speechSynthesis) {
  refreshVoices();
  window.speechSynthesis.onvoiceschanged = refreshVoices;
}

export function speechLangFor(lang: string): string {
  return lang === "ur" ? "ur-PK" : "en-US";
}

/** True when a voice for the language exists on this device. */
export function hasVoiceFor(lang: string): boolean {
  if (typeof window === "undefined" || !window.speechSynthesis) return false;
  if (!voicesCache.length) refreshVoices();
  const prefix = speechLangFor(lang).slice(0, 2);
  return voicesCache.some((v) => v.lang.toLowerCase().startsWith(prefix));
}

/**
 * Speak `text`. rate < 1 sounds clearer for early readers.
 * Returns false when the browser has no speech synthesis at all.
 */
export function speak(text: string, lang = "en", rate = 0.92): boolean {
  if (typeof window === "undefined" || !window.speechSynthesis || !text) return false;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = speechLangFor(lang);
  utter.rate = rate;
  if (!voicesCache.length) refreshVoices();
  const prefix = utter.lang.slice(0, 2);
  const voice =
    voicesCache.find((v) => v.lang.toLowerCase().replace("_", "-").startsWith(utter.lang.toLowerCase())) ||
    voicesCache.find((v) => v.lang.toLowerCase().startsWith(prefix));
  if (!voice || (!navigator.onLine && !voice.localService)) return false;
  utter.voice = voice;
  window.speechSynthesis.speak(utter);
  return true;
}

export function stopSpeaking() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}
