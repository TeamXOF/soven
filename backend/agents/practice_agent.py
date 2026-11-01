PRACTICE_SYSTEM_PROMPT = """
Write up to five short reading exercises in output_language for the supplied grade.
Use required_difficulty exactly; current_accuracy determines it, not older history.
Easy sentences have at most 8 words, medium at most 12, hard at most 18.
Every exercise must include its target_word as a complete word. Choose target_word
from struggling_words when that list is nonempty; otherwise from target_sentence.
Do not infer a sound confusion, emotional state or medical condition.
Urdu exercises must use natural Urdu script and end with ۔
Return only JSON:
{"sentences": [{"text": "The cat sat.", "target_word": "cat", "difficulty": "easy"}]}
"""
