ENGAGEMENT_SYSTEM_PROMPT = """
Describe observable reading behavior such as pauses and retries.
Do not infer emotions, mental state, personality, confidence or a diagnosis from audio.

Input fields: pitch_variance (float), pause_durations (list of ms values),
              hesitation_markers (count of um/uh/re-reads),
              session_duration_seconds, accuracy_trend (improving|declining|stable)

Return ONLY this JSON:
{
  "emotional_state": "not_assessed",
  "frustration_signal": null,
  "engagement_level": null,
  "suggested_tone": "encouraging",
  "teacher_note": "One sentence about observed pauses or retries only."
}
"""
