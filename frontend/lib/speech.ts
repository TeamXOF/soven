"use client";
import policy from "../../shared/speech-capabilities.json";

export type PlaybackCapability = { available: boolean; reason: "available" | "unsupported_language" | "api_unavailable" | "no_voice" | "offline_voice_unavailable"; locale: string | null; local: boolean | null };
export function speechLangFor(lang: string): string | null {
  const code=lang.trim().toLowerCase().replaceAll("_","-").split("-")[0];
  return Object.prototype.hasOwnProperty.call(policy.languages,code) ? policy.languages[code as keyof typeof policy.languages].locale : null;
}
function selection(lang: string): {capability: PlaybackCapability; voice: SpeechSynthesisVoice | null} {
  const locale=speechLangFor(lang);
  const result=(reason: PlaybackCapability["reason"],voice: SpeechSynthesisVoice | null=null) => ({capability:{available:reason==="available",reason,locale,local:voice?.localService ?? null},voice});
  if(!locale)return result("unsupported_language");
  if(typeof window==="undefined" || !window.speechSynthesis)return result("api_unavailable");
  // Always refresh: browser voices can arrive late or change after installation.
  let voices: SpeechSynthesisVoice[];
  try {voices=window.speechSynthesis.getVoices();}catch{return result("api_unavailable");}
  const normalize=(value:string)=>value.toLowerCase().replaceAll("_","-");
  const language=locale.split("-")[0].toLowerCase();
  const matching=voices.filter(v=>normalize(v.lang).split("-")[0]===language);
  const eligible=navigator.onLine===false ? matching.filter(v=>v.localService) : matching;
  const voice=eligible.find(v=>normalize(v.lang)===normalize(locale)) ?? eligible[0] ?? null;
  if(!voice)return result(matching.length ? "offline_voice_unavailable" : "no_voice");
  return result("available",voice);
}
export function playbackCapability(lang:string): PlaybackCapability {return selection(lang).capability;}
export function hasVoiceFor(lang:string):boolean {return playbackCapability(lang).available;}

/** True means the browser accepted a request, not that audible playback completed. */
export function speak(text:string,lang="en",rate=.92):boolean {
  const {capability,voice}=selection(lang);
  if(!capability.available || !voice || !text.trim())return false;
  try {
    window.speechSynthesis.cancel();
    const utter=new SpeechSynthesisUtterance(text);
    utter.lang=capability.locale!;utter.voice=voice;
    utter.rate=Number.isFinite(rate) ? Math.min(2,Math.max(.5,rate)) : .92;
    window.speechSynthesis.speak(utter);return true;
  }catch{return false;}
}
export function stopSpeaking(){
  if(typeof window!=="undefined" && window.speechSynthesis)window.speechSynthesis.cancel();
}
