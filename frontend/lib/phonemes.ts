/**
 * Human-readable labels for internal phoneme-mismatch codes.
 * "l_vs_w" → "l / w sounds" · "د_vs_ڈ" → "د / ڈ sounds"
 * "br blend" (AI free-text) passes through unchanged ·
 * "unclear"/"word-recall" get honest kid-friendly phrasing.
 */
export function prettyPhoneme(label: string | null | undefined): string {
  if (!label) return "";
  if (label.includes("_vs_")) {
    return label.split("_vs_").join(" / ") + " sounds";
  }
  if (label === "unclear") return "Unclear sound";
  if (label === "word-recall") return "Word recall";
  return label;
}
