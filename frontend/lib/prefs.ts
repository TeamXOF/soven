"use client";

import { isReadingLanguage } from "./languages";
import type { ReadingLanguage } from "./languages";

/**
 * Student reading preferences — client-side only (localStorage), no account
 * changes. Applied by the Story Mode pages and the mic capture context:
 *   preferredMic  — audio input device id for recordings
 *   storyLanguage — default story language on the Story Mode map
 *   wordTips      — show the tap-a-word pronunciation popovers
 *   biggerText    — larger reading text in Story Mode
 */

export type StudentPrefs = {
  preferredMic: string | null;
  storyLanguage: ReadingLanguage;
  wordTips: boolean;
  biggerText: boolean;
};

const KEY = "sf_student_prefs";

const DEFAULTS: StudentPrefs = {
  preferredMic: null,
  storyLanguage: "en",
  wordTips: true,
  biggerText: false,
};

export function loadPrefs(): StudentPrefs {
  if (typeof window === "undefined") return DEFAULTS;
  try {
    const raw = window.localStorage.getItem(KEY);
    const merged = raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
    if (!isReadingLanguage(merged.storyLanguage)) merged.storyLanguage = DEFAULTS.storyLanguage;
    return merged;
  } catch {
    return DEFAULTS;
  }
}

export function savePrefs(prefs: Partial<StudentPrefs>): StudentPrefs {
  const merged = { ...loadPrefs(), ...prefs };
  if (!isReadingLanguage(merged.storyLanguage)) merged.storyLanguage = DEFAULTS.storyLanguage;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(merged));
  } catch {
    /* storage unavailable — prefs just won't persist */
  }
  return merged;
}
