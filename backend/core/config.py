"""
SpeakFlow v2 — central settings.
All v2 tunables live here; nothing else reads os.environ directly (roadmap Prompt 1).
Gen-1 modules keep their own env reads — untouched by design.
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_BACKEND_DIR, "data")


class Settings:
    # ── Meta AI reasoning layer (Meta Spark / Muse Glimmer open weights) ────
    SPEAKFLOW_LLM_BASE_URL = os.getenv("SPEAKFLOW_LLM_BASE_URL", os.getenv("REASONING_BASE_URL", "https://api.meta.ai/v1"))
    REASONING_PROVIDER = os.getenv("REASONING_PROVIDER", "meta")
    REASONING_MODEL = os.getenv("REASONING_MODEL", os.getenv("FEEDBACK_MODEL", "muse-spark-1.3"))
    FEEDBACK_MODEL = REASONING_MODEL
    FEEDBACK_MODEL_FALLBACK = os.getenv("FEEDBACK_MODEL_FALLBACK", "muse-glimmer")
    FEEDBACK_TIMEOUT_S = float(os.getenv("FEEDBACK_TIMEOUT_S", "10"))
    JUDGE_HESITATION_ENABLED = os.getenv("JUDGE_HESITATION_ENABLED", "0") == "1"
    HESITATION_TIMEOUT_S = float(os.getenv("HESITATION_TIMEOUT_S", "8"))

    # ── Key configuration & demo isolation ──────────────────────────────────
    ENV = os.getenv("ENV", "dev")
    META_API_KEY = os.getenv("META_API_KEY", os.getenv("REASONING_API_KEY", os.getenv("GROQ_API_KEY", "")))
    REASONING_API_KEY = META_API_KEY
    GEMINI_API_KEY_DEMO = os.getenv("GEMINI_API_KEY_DEMO", "")

    @property
    def active_gemini_key(self) -> str:
        # Compatibility property for reasoning adapters
        return self.META_API_KEY or os.getenv("GOOGLE_API_KEYS", os.getenv("GOOGLE_API_KEY", ""))

    # ── STT (Meta Voice Transcribe 1.0 online, local quantized Whisper fallback) ─
    META_STT_URL = os.getenv("META_STT_URL", os.getenv("GROQ_STT_URL", "https://api.meta.ai/v1/asr/transcribe"))
    META_STT_MODEL = os.getenv("META_STT_MODEL", os.getenv("GROQ_STT_MODEL", "muse-voice-transcribe-1.0"))
    GROQ_API_KEY = META_API_KEY
    GROQ_STT_MODEL = META_STT_MODEL
    GROQ_STT_URL = META_STT_URL
    STT_TIMEOUT_S = float(os.getenv("STT_TIMEOUT_S", "3"))

    # STT engine choice: "auto" = Meta Voice Transcribe when online with key, local otherwise
    @property
    def stt_mode(self) -> str:
        mode = (os.getenv("STT_MODE", "auto") or "auto").strip().lower()
        return mode if mode in ("auto", "online", "local", "groq") else "auto"

    # Classic-engine agent model (Settings → live-editable): "auto" resolves to
    # Flash-Lite; explicit names pin that model.
    @property
    def agent_model(self) -> str:
        model = (os.getenv("GEN1_AGENT_MODEL", "auto") or "auto").strip()
        return model or "auto"

    # ── Local Whisper (shared with Gen-1) ─────────────────────────────────────
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
    # YIN is sufficient for descriptive pitch features; pYIN remains opt-in.
    PITCH_ESTIMATOR = os.getenv("PITCH_ESTIMATOR", "yin").lower()

    # ── Scoring (roadmap Part 2.1: threshold is a tuning knob, not truth) ─────
    WORD_CORRECT_THRESHOLD = int(os.getenv("WORD_CORRECT_THRESHOLD", "70"))
    CHECKPOINT_PASS_THRESHOLD = int(os.getenv("CHECKPOINT_PASS_THRESHOLD", "70"))

    # ── Reference-vector dictionary (roadmap Phase D) ─────────────────────────
    # When a word has a hand-verified reference vector, blend the acoustic
    # distance into the composite score with this weight. Synthetic placeholder
    # references can be disabled entirely by setting USE_REFERENCE_VECTORS=0.
    USE_REFERENCE_VECTORS = os.getenv("USE_REFERENCE_VECTORS", "0") == "1"
    REFERENCE_BLEND_WEIGHT = float(os.getenv("REFERENCE_BLEND_WEIGHT", "0.25"))

    # ── Hesitation / pause flags ──────────────────────────────────────────────
    PAUSE_FLAG_MS = int(os.getenv("PAUSE_FLAG_MS", "400"))
    PAUSE_AMBIGUOUS_MS = int(os.getenv("PAUSE_AMBIGUOUS_MS", "900"))

    # ── Offline / sync (roadmap Part 1.3) ─────────────────────────────────────
    # Point this at a cloud ingest endpoint to enable sync-on-reconnect.
    # Unset = queue mechanics still work (synced flags tracked), nothing is pushed.
    CLOUD_SYNC_URL = os.getenv("CLOUD_SYNC_URL", "")
    NETWORK_PROBE_TTL_S = float(os.getenv("NETWORK_PROBE_TTL_S", "5"))
    SYNC_INTERVAL_S = int(os.getenv("SYNC_INTERVAL_S", "30"))

    # ── Story checkpoints count cap (roadmap Feature 4: 3-5 fixed) ────────────
    MAX_CHECKPOINTS = 5


settings = Settings()
