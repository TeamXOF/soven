"use client";

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
  storyLanguage: "en" | "ur";
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
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS;
  } catch {
    return DEFAULTS;
  }
}

export function savePrefs(prefs: Partial<StudentPrefs>): StudentPrefs {
  const merged = { ...loadPrefs(), ...prefs };
  try {
    window.localStorage.setItem(KEY, JSON.stringify(merged));
  } catch {
    /* storage unavailable — prefs just won't persist */
  }
  return merged;
}
