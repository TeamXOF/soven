DIFFICULTY_SYSTEM_PROMPT = """
Suggest reading practice from supplied observations. This is not a diagnostic assessment.
Write primary_issue and reasoning in output_language. Describe differences as
recognized word differences, not proven mistakes by the child. Give one short action.
Categories: WORD_READING | PACING | MIXED | NO_OBVIOUS_ERROR.
Do not infer a phonetic or cognitive condition. Do not invent age-norm comparisons.

Input fields: phonetic_result (from Agent 1), wpm (words per minute),
              pause_count (pauses over 800ms), repetition_count, grade

Return ONLY this JSON:
{
  "category": "WORD_READING",
  "primary_issue": "One sentence describing main struggle.",
  "secondary_issue": null,
  "reasoning": "Brief plain language for teacher."
}
"""
