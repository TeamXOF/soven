// API Client for FastAPI Backend
import type { ReadingLanguage, PlatformCapabilities } from "./languages";
// ── Gen-1 (5-agent pipeline) functions kept as-is ───────────────────────────
// ── v2 (checkpoint/two-phase contract) added per the roadmap ────────────────

// Set NEXT_PUBLIC_API_URL for separate hosting. HTTPS defaults to same-origin.
const configuredRoot = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || undefined;
const localRoot = (() => {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  const origin = new URL(window.location.origin);
  if (origin.protocol === "http:") origin.port = "8000";
  return origin.origin;
})();
export const API_ROOT = configuredRoot ?? localRoot;
export const API_BASE_URL = `${API_ROOT}/api`;

async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getStoredToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401 && token && getStoredToken() === token) {
    clearSession();
    if (typeof window !== "undefined") window.dispatchEvent(new Event("sf-auth-expired"));
  }
  return response;
}

// ═══════════════════════════ GEN-1 (unchanged) ═══════════════════════════════

export async function fetchStudents() {
  const res = await apiFetch(`${API_BASE_URL}/students`);
  if (!res.ok) throw new Error("Failed to fetch students");
  return res.json();
}

export async function createStudent(data: { name: string, grade: number, level: string }) {
  const res = await apiFetch(`${API_BASE_URL}/students`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to create student");
  return res.json();
}

export async function updateStudent(id: string, data: { name: string, grade: number, level: string }) {
  const res = await apiFetch(`${API_BASE_URL}/students/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error("Failed to update student");
  return res.json();
}

export async function deleteStudent(id: string) {
  const res = await apiFetch(`${API_BASE_URL}/students/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Failed to delete student");
  return res.json();
}

export type ClassicSession = {
  id: string; student_id: string; student_name: string; target_sentence: string | null;
  transcript: string | null; wpm: number | null; accuracy: number | null;
  overall_score: number | null; timestamp: string; language: ReadingLanguage;
};
export async function fetchSessions(studentId?: string): Promise<ClassicSession[]> {
  const url = studentId
    ? `${API_BASE_URL}/sessions?student_id=${studentId}`
    : `${API_BASE_URL}/sessions`;
  const res = await apiFetch(url);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function fetchSessionDiagnosis(sessionId: string) {
  const res = await apiFetch(`${API_BASE_URL}/sessions/${sessionId}/diagnosis`);
  if (!res.ok) throw new Error("Failed to fetch diagnosis");
  return res.json();
}

export async function runPipeline(studentId: string, audioBase64: string, targetSentence: string, language: ReadingLanguage = "en") {
  // Construct the payload expected by the FastAPI PipelineRunRequest
  const payload = {
    student_id: studentId,
    target_sentence: targetSentence,
    audio_base64: audioBase64,
    language
  };

  const res = await apiFetch(`${API_ROOT}/pipeline/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Pipeline execution failed");
  }

  return res.json();
}

// ═══════════════════════════ v2 CONTRACT TYPES ═══════════════════════════════

export type SttSource = "groq" | "local_fallback";
export type FeedbackSource = "gemini" | "meta" | "chat_completions" | "model_unknown" | "template_fallback";
export type EngagementState = "confident" | "anxious" | "frustrated" | "unknown" | "pauses_detected" | "steady_reading" | "practice_recommended";
export type Language = ReadingLanguage;

export type Phase1Word = {
  word: string;
  correct: boolean;
  phoneme_mismatch: string | null;
  spoken?: string;
};

export type Hesitation = {
  after_word: string;
  pause_ms: number;
  flagged_ambiguous: boolean;
};

export type SpeechEvidence = {
  schema_version: number; origin: "recognizer" | "simulation"; language: string;
  provider: string; engine: string; fallback_reason: string | null;
  word_timing: "available" | "partial" | "unavailable";
  recognition_confidence: "available" | "partial" | "unavailable";
  confidence_basis: string; word_count: number; timed_word_count: number;
  pause_assessment: "available" | "unavailable"; quality_validated: false;
};
export type Phase1Response = {
  speech_evidence?: SpeechEvidence | null;
  session_id: string;
  checkpoint_id: string;
  phase: 1;
  transcript: string;
  words: Phase1Word[];
  wpm: number;
  accuracy: number;
  passed: boolean;
  stars: number;
  hesitations: Hesitation[];
  stt_source: SttSource;
  latency_ms: { stt: number; acoustic: number; scoring: number; total_phase1: number };
  warnings: string[];
};

export type Phase2Response = {
  session_id: string;
  checkpoint_id: string;
  phase: 2;
  status?: "pending";
  feedback_text?: string;
  engagement_state?: EngagementState;
  comprehension_question?: string | null;
  practice_recommendation?: string | null;
  teacher_note?: string | null;
  feedback_source?: FeedbackSource;
  latency_ms?: { gemini_feedback?: number; gemini_hesitation?: number };
};

export type StoryCheckpoint = {
  checkpoint_id: string;
  target_text: string;
  text_en?: string;
  text_ur?: string;
  text_es?: string;
};

export type StorySummary = {
  id: string;
  title: string;
  title_ur: string;
  title_es?: string;
  emoji: string;
  color: string;
  total_checkpoints: number;
  passed_checkpoints: number;
  status: "completed" | "in_progress" | "available";
  locked: boolean;
};

export type CreatedSession = {
  session_id: string;
  id?: string;
  student_id: string;
  story_id: string;
  language: Language;
  created_at: string;
  checkpoints: StoryCheckpoint[];
};

export type SessionCheckpointDetail = StoryCheckpoint & {
  speech_evidence?: SpeechEvidence | null;
  status: "pending" | "attempted";
  passed: boolean;
  accuracy: number | null;
  wpm: number | null;
  stars: number;
  transcript: string | null;
  feedback_text: string | null;
  engagement_state: EngagementState | null;
  comprehension_question: string | null;
  practice_recommendation: string | null;
  stt_source: SttSource | null;
  feedback_source: FeedbackSource | null;
  hesitations: Hesitation[];
  words: Phase1Word[];
};

export type SessionDetail = {
  session_id: string;
  student_id: string;
  student_name: string | null;
  story_id: string;
  story_title: string | null;
  story_emoji: string | null;
  language: Language;
  created_at: string;
  completed_at: string | null;
  mode: string;
  synced: boolean;
  checkpoints: SessionCheckpointDetail[];
  totals: {
    checkpoints_total: number;
    checkpoints_attempted: number;
    checkpoints_passed: number;
    stars: number;
    avg_accuracy: number | null;
    is_complete: boolean;
  };
};

export type StudentDashboard = {
  student: { id: string; name: string; grade: number; level: string };
  summary: {
    stars: number;
    checkpoints_passed: number;
    checkpoints_attempted: number;
    avg_accuracy: number | null;
    recent_score: number | null;
    progress_pct: number;
    classic_sessions: number;
    story_sessions: number;
  };
  trend: { date: string; accuracy: number; wpm: number; checkpoints: number }[];
  struggling_words: { word: string; count: number }[];
  phoneme_errors: { phoneme: string; count: number }[];
  stories: { story_id: string; title: string; emoji: string; passed: number; total: number; stars: number }[];
  recent_sessions: {
    id: string; story_id: string | null; language: string; created_at: string;
    completed_at: string | null; attempted: number; avg_accuracy: number | null; stars: number | null;
    kind: "story" | "classic"; label: string; wpm?: number | null;
  }[];
};

export type ClassroomOverview = {
  totals: {
    active_students: number;
    sessions_today: number;
    class_accuracy: number | null;
    stars_awarded: number;
  };
  weekly: { day: string; accuracy: number; sessions: number }[];
  struggling_areas: { label: string; count: number; rate: number }[];
  phoneme_heatmap: { phoneme: string; count: number; rate: number }[];
  words_analyzed: number;
  checkpoint_progress: {
    story_id: string; story_title: string; story_emoji: string;
    checkpoint_id: string; checkpoint_label: string;
    attempted: number; passed: number; avg_accuracy: number;
  }[];
};

export type V1Health = {
  mode: "online" | "offline";
  groq_reachable: boolean | null;
  gemini_reachable: boolean | null;
  groq_configured: boolean;
  gemini_configured: boolean;
  server_time: string;
};

export type RecordedActivity = {
  id: string; student_id: string; engine: string; created_at: string; accuracy: number;
  language: string; latency_ms: Record<string, number>; status: string;
};

export async function fetchRecordedActivity(): Promise<RecordedActivity[]> {
  const response = await apiFetch(`${API_ROOT}/api/v1/activity`);
  if (!response.ok) throw new Error(await parseError(response, "Could not load recorded activity"));
  return (await response.json()).attempts;
}

export type SyncStatus = { queued: number; cloud_configured: boolean; mode: string };

export type V2SessionListItem = {
  id: string;
  student_id: string;
  student_name: string | null;
  story_id: string;
  language: string;
  created_at: string;
  completed_at: string | null;
  synced: boolean;
  mode: string;
  attempted: number;
  passed: number;
  stars: number;
  avg_accuracy: number | null;
  duration_s: number | null;
};

// ═══════════════════════════ AUTH & ROLES ════════════════════════════════════

export type Role = "teacher" | "student";
export type AuthUser = {
  account_scope?: "classroom" | "personal";
  reader_mode?: ReaderMode;
  profile_completed?: boolean;
  profile?: ReaderProfile;
  classroom_code?: string;
  classroom_id?: string;
  is_admin?: number;
  id: string;
  username: string;
  name: string;
  role: Role;
  status: "approved" | "pending" | "rejected";
  student_id: string | null;
  created_at?: string;
};

const TOKEN_KEY = "sf_token";
const USER_KEY = "sf_user";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function storeSession(token: string, user: AuthUser) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

function authHeaders(): HeadersInit {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiLogin(username: string, password: string): Promise<{ token: string; user: AuthUser }> {
  const res = await apiFetch(`${API_ROOT}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Login failed"));
  return res.json();
}

export async function apiRegister(name: string, username: string, password: string, classroomCode: string): Promise<{ message: string }> {
  const res = await apiFetch(`${API_ROOT}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, username, password, classroom_code: classroomCode }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Registration failed"));
  return res.json();
}

export async function apiLogout() {
  try {
    await apiFetch(`${API_ROOT}/api/auth/logout`, {
      method: "POST",
      headers: { ...authHeaders() },
    });
  } catch { /* best-effort */ }
  clearSession();
}

export type ManagedUser = AuthUser;

export async function fetchUsers(): Promise<ManagedUser[]> {
  const res = await apiFetch(`${API_ROOT}/api/auth/users`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load accounts"));
  return res.json();
}

export async function approveUser(userId: string, studentId?: string): Promise<{ student_id: string; created_profile: boolean }> {
  const res = await apiFetch(`${API_ROOT}/api/auth/users/${userId}/approve`, {
    method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(studentId ? { student_id: studentId } : {}),
  });
  if (!res.ok) throw new Error(await parseError(res, "Approval failed"));
  return res.json();
}

export async function rejectUser(userId: string): Promise<void> {
  const res = await apiFetch(`${API_ROOT}/api/auth/users/${userId}/reject`, {
    method: "POST", headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await parseError(res, "Rejection failed"));
}

export async function deleteUserAccount(userId: string): Promise<void> {
  const res = await apiFetch(`${API_ROOT}/api/auth/users/${userId}`, {
    method: "DELETE", headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await parseError(res, "Delete failed"));
}

// ═══════════════════════ TEACHER MANAGEMENT ══════════════════════════════════

export type RosterEntry = {
  id: string;
  name: string;
  grade: number;
  level: string;
  checkpoints_passed: number;
  checkpoints_attempted: number;
  stars: number;
  avg_accuracy: number | null;
  last_active: string | null;
  parent_update_enabled: boolean;
  account_username: string | null;
  account_status: string | null;
};

export async function fetchRoster(): Promise<RosterEntry[]> {
  const res = await apiFetch(`${API_ROOT}/api/v1/teacher/roster`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load roster"));
  return res.json();
}

export async function toggleParentUpdates(studentId: string, enabled: boolean): Promise<void> {
  const res = await apiFetch(`${API_ROOT}/api/v1/teacher/students/${studentId}/parent-toggle`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Toggle failed"));
}

export type ParentUpdate = { enabled: boolean; message: string | null; student_name?: string };

export async function fetchParentMessage(studentId: string): Promise<ParentUpdate> {
  const res = await apiFetch(`${API_ROOT}/api/v1/students/${studentId}/parent-message`, {
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load parent update"));
  return res.json();
}

export type StudentReport = {
  student_id: string;
  name: string;
  grade: number;
  level: string;
  trend: string;
  checkpoints_passed: number;
  checkpoints_attempted: number;
  stars: number;
  avg_accuracy: number | null;
  recent_checkpoints: {
    checkpoint_id: string; accuracy: number; stars: number; created_at: string;
    story_id: string; language: string; story_title: string | null;
  }[];
};

export async function fetchReports(): Promise<{ generated_at: string; reports: StudentReport[] }> {
  const res = await apiFetch(`${API_ROOT}/api/v1/reports`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load reports"));
  return res.json();
}

export type PracticeLibrary = {
  exercises: {
    id: string; focus: string; frequency: number; words: string[];
    sentence: string | null; story_id: string | null; checkpoint_id: string | null;
    sources?: string[]; trend?: "improving" | "worsening" | "new" | "steady";
  }[];
  struggling_words: { word: string; count: number }[];
  scope: "student" | "class";
  total_words_analyzed: number;
  progress?: {
    improving: string[];
    worsening: string[];
    new_sounds: string[];
    conquered_words: string[];
  };
};

export async function fetchPracticeLibrary(): Promise<PracticeLibrary> {
  const res = await apiFetch(`${API_ROOT}/api/v1/practice/library`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load practice library"));
  return res.json();
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<{ ok: boolean; message: string }> {
  const res = await apiFetch(`${API_ROOT}/api/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Could not change the password"));
  return res.json();
}

export type SttMode = "auto" | "groq" | "local";
export type AgentModel = "auto" | "gemini-3.5-flash-lite" | "gemma-4-31b-it";

export type KeysStatus = {
  groq_configured: boolean;
  google_configured: boolean;
  google_key_count: number;
  env: string;
  stt_mode?: SttMode;
  agent_model?: AgentModel;
  updated?: string[];
};

export async function fetchKeysStatus(): Promise<KeysStatus> {
  const res = await apiFetch(`${API_ROOT}/api/v1/config/keys`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to load key status"));
  return res.json();
}

export async function saveKeys(body: {
  groq_api_key?: string;
  google_api_keys?: string;
  stt_mode?: SttMode;
  agent_model?: AgentModel;
}): Promise<KeysStatus> {
  const res = await apiFetch(`${API_ROOT}/api/v1/config/keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to save keys"));
  return res.json();
}

// ═══════════════════════════ v2 API CLIENT ═══════════════════════════════════

/** Parse the shared error envelope ({error:{code,message,retryable}}) or a
 *  legacy FastAPI `detail` string into one message. */
async function parseError(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (body?.error?.message) return body.error.message;
    if (typeof body?.detail === "string") return body.detail;
  } catch { /* no body */ }
  return fallback;
}

let baseCache: { baseUrl: string; mode: string; ts: number } | null = null;

export async function resolveApiBase(): Promise<{ baseUrl: string; mode: string }> {
  // Cached for 5s per the roadmap — avoids probing on every call.
  if (baseCache && Date.now() - baseCache.ts < 5000) {
    return { baseUrl: baseCache.baseUrl, mode: baseCache.mode };
  }
  let mode = "unknown";
  try {
    const res = await apiFetch(`${API_ROOT}/api/v1/health`);
    if (res.ok) mode = (await res.json()).mode ?? "unknown";
  } catch {
    mode = "unreachable";
  }
  baseCache = { baseUrl: API_ROOT, mode, ts: Date.now() };
  return { baseUrl: API_ROOT, mode };
}

export type WordTip = {
  word: string;
  letters: string[];
  syllables: string[];
  tip: string;
  tip_source: "gemini" | "meta" | "chat_completions" | "model_unknown" | "template" | "cache";
};

export async function fetchWordTip(word: string, lang: Language, mismatch = "", spoken = ""): Promise<WordTip> {
  const q = new URLSearchParams({ word, lang, mismatch, spoken });
  const res = await apiFetch(`${API_ROOT}/api/v1/words/tip?${q}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Could not load a tip for that word"));
  return res.json();
}


// ── Dynamic Story Mode (dual-track endless levels) ──────────────────────────
export type StoryTrack = ReadingLanguage;

export type StoryMapLevel = {
  level: number; theme: string; difficulty: string; boss: boolean;
  stars: number; best_accuracy: number | null; attempts: number;
  status: "completed" | "current" | "locked"; unlocked: boolean;
};

export type StoryMap = {
  track: StoryTrack; world: number; world_name: string;
  levels: StoryMapLevel[]; total_stars: number; next_level: number;
  unlocked_upto: number; levels_completed: number;
};

export type StoryPlay = {
  track: StoryTrack; level: number; sentence: string; theme: string;
  difficulty: string; best_stars: number; attempts: number;
};

export type StoryWord = {
  word: string; correct: boolean; phoneme_mismatch: string | null;
  spoken?: string; extra?: boolean; score?: number;
};

export type StoryAttemptResult = {
  speech_evidence?: SpeechEvidence | null;
  attempt_id: string; track: StoryTrack; level: number; sentence: string;
  theme: string; difficulty: string; transcript: string; words: StoryWord[];
  accuracy: number; stars: number; passed: boolean; wpm: number;
  stt_source?: string;
};

export type StoryTrackSummary = {
  track: StoryTrack; total_stars: number; levels_completed: number;
  attempts: number; unlocked_upto: number; next_level: number;
};

export async function fetchStoryMap(track: StoryTrack, world?: number): Promise<StoryMap> {
  const q = new URLSearchParams({ track });
  if (world) q.set("world", String(world));
  const res = await apiFetch(`${API_ROOT}/api/v1/story/map?${q}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Could not load the story map"));
  return res.json();
}

export async function fetchStorySummary(track: StoryTrack): Promise<StoryTrackSummary> {
  const res = await apiFetch(`${API_ROOT}/api/v1/story/summary?track=${track}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Could not load story progress"));
  return res.json();
}

export async function fetchStoryPlay(track: StoryTrack, level: number): Promise<StoryPlay> {
  const res = await apiFetch(`${API_ROOT}/api/v1/story/play?track=${track}&level=${level}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Could not load that level"));
  return res.json();
}

export async function storyAnalyze(track: StoryTrack, level: number, blob: Blob): Promise<StoryAttemptResult> {
  const fd = new FormData();
  fd.append("audio", blob, "reading.webm");
  fd.append("track", track);
  fd.append("level", String(level));
  const res = await apiFetch(`${API_ROOT}/api/v1/story/analyze`, {
    method: "POST", headers: { ...authHeaders() }, body: fd,
  });
  if (!res.ok) throw new Error(await parseError(res, "Analysis failed"));
  return res.json();
}

export async function storyAnalyzeMock(track: StoryTrack, level: number, words: string[]): Promise<StoryAttemptResult> {
  const res = await apiFetch(`${API_ROOT}/api/v1/story/analyze-mock`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ track, level, words }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Analysis failed"));
  return res.json();
}

export async function fetchStoryFeedback(attemptId: string): Promise<Record<string, unknown> | null> {
  const res = await apiFetch(`${API_ROOT}/api/v1/story/feedback/${attemptId}`, { headers: { ...authHeaders() } });
  if (!res.ok) return null;
  const data = await res.json();
  return data && data.status === "pending" ? null : data;
}

export async function fetchV1Health(): Promise<V1Health> {
  const res = await apiFetch(`${API_ROOT}/api/v1/health`);
  if (!res.ok) throw new Error("Failed to reach v1 health");
  return res.json();
}

export async function fetchStories(studentId?: string, language?: ReadingLanguage): Promise<StorySummary[]> {
  const url = studentId
    ? `${API_ROOT}/api/v1/stories?student_id=${encodeURIComponent(studentId)}`
    : `${API_ROOT}/api/v1/stories`;
  const res = await apiFetch(url + (language ? `${studentId ? "&" : "?"}language=${language}` : ""));
  if (!res.ok) throw new Error("Failed to fetch stories");
  return res.json();
}

export async function createSession(
  studentId: string, storyId: string, language: Language
): Promise<CreatedSession> {
  const res = await apiFetch(`${API_ROOT}/api/v1/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ student_id: studentId, story_id: storyId, language }),
  });
  if (!res.ok) throw new Error(await parseError(res, "Failed to create session"));
  return res.json();
}

export async function fetchV2Sessions(): Promise<V2SessionListItem[]> {
  const res = await apiFetch(`${API_ROOT}/api/v1/sessions`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error(await parseError(res, "Failed to fetch story sessions"));
  return res.json();
}

export async function analyzeCheckpoint(
  sessionId: string, checkpointId: string, audioBlob: Blob
): Promise<Phase1Response> {
  const form = new FormData();
  form.append("audio", audioBlob, "reading.webm");
  form.append("checkpoint_id", checkpointId);
  const res = await apiFetch(`${API_ROOT}/api/v1/sessions/${sessionId}/analyze`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await parseError(res, "Checkpoint analysis failed"));
  return res.json();
}

export async function fetchFeedback(
  sessionId: string, checkpointId: string
): Promise<Phase2Response | null> {
  const res = await apiFetch(
    `${API_ROOT}/api/v1/sessions/${sessionId}/feedback/${checkpointId}`);
  if (!res.ok) return null;
  const data: Phase2Response = await res.json();
  return data.feedback_text ? data : null;
}

export async function fetchSessionDetail(sessionId: string): Promise<SessionDetail> {
  const res = await apiFetch(`${API_ROOT}/api/v1/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session");
  return res.json();
}

export async function fetchStudentDashboard(
  studentId: string, range: "session" | "week" | "all" = "all"
): Promise<StudentDashboard> {
  const res = await apiFetch(
    `${API_ROOT}/api/v1/students/${studentId}/dashboard?range=${range}`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error("Failed to fetch student dashboard");
  return res.json();
}

export async function fetchClassroomOverview(): Promise<ClassroomOverview> {
  const res = await apiFetch(`${API_ROOT}/api/v1/classroom/overview`, { headers: { ...authHeaders() } });
  if (!res.ok) throw new Error("Failed to fetch classroom overview");
  return res.json();
}

export async function triggerSync(): Promise<{ synced_count: number; failed_count: number; note: string }> {
  const res = await apiFetch(`${API_ROOT}/api/v1/sync`, { method: "POST", headers: { ...authHeaders() } });
  if (!res.ok) throw new Error("Sync failed");
  return res.json();
}

export async function fetchSyncStatus(): Promise<SyncStatus> {
  const res = await apiFetch(`${API_ROOT}/api/v1/sync/status`);
  if (!res.ok) throw new Error("Failed to fetch sync status");
  return res.json();
}


// Read-only inventory for future onboarding. Planned languages remain disabled.
export async function fetchPlatformCapabilities(signal?: AbortSignal): Promise<PlatformCapabilities> {
  const response = await apiFetch(`${API_ROOT}/api/v1/capabilities`, { signal });
  if (!response.ok) throw new Error("Could not load language capabilities");
  return response.json();
}

export type ReaderMode = "child" | "adult" | "teacher" | "dyslexia";
export type ProfileAccessibility = {
  larger_text: boolean;
  word_tips: boolean;
  high_contrast: boolean;
  line_spacing: "normal" | "comfortable" | "wide";
  coach_enabled: boolean;
  autoplay_coach: boolean;
};
export type ReaderProfile = {
  user_id: string;
  reader_mode: ReaderMode;
  reading_language: ReadingLanguage;
  interface_language: ReadingLanguage;
  native_language: import("./language-types").LanguageCode | null;
  translation_language: import("./language-types").LanguageCode | null;
  accessibility: ProfileAccessibility;
  profile_completed: boolean;
  version: number;
  updated_at: string | null;
};
export type ReaderProfileUpdate = {
  expected_version: number;
  reading_language?: ReadingLanguage;
  interface_language?: ReadingLanguage;
  native_language?: import("./language-types").LanguageCode | null;
  translation_language?: import("./language-types").LanguageCode | null;
  accessibility?: Partial<ProfileAccessibility>;
  reader_mode?: ReaderMode;
  persona_type?: ReaderMode;
  complete_profile?: boolean;
};

export async function apiRegisterAdult(name: string, username: string, password: string): Promise<{
  ok: boolean; status: "approved"; profile_required: boolean; message: string;
}> {
  const response = await apiFetch(`${API_ROOT}/api/auth/register-adult`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, username, password }),
  });
  if (!response.ok) throw new Error(await parseError(response, "Could not create your account"));
  return response.json();
}

export async function fetchReaderProfile(signal?: AbortSignal): Promise<{ profile: ReaderProfile }> {
  const response = await apiFetch(`${API_ROOT}/api/auth/profile`, { signal });
  if (!response.ok) throw new Error(await parseError(response, "Could not load your profile"));
  return response.json();
}

export async function saveReaderProfile(body: ReaderProfileUpdate): Promise<{ profile: ReaderProfile }> {
  const response = await apiFetch(`${API_ROOT}/api/auth/profile`, {
    method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(await parseError(response, "Could not save your profile"));
  return response.json();
}
