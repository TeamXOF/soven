"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { toError } from "@/lib/errors";

import { useAuth } from "@/components/auth/AuthProvider";
import StudentSettings from "@/components/settings/StudentSettings";
import StudentApprovals, { ClassroomInvite } from "@/components/settings/StudentApprovals";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import {
AgentModel,API_ROOT,
approveUser,
deleteUserAccount,
fetchKeysStatus,
fetchSyncStatus,
fetchUsers,
fetchV1Health,
KeysStatus,
ManagedUser,
rejectUser,
saveKeys,
SttMode,
SyncStatus,
triggerSync,V1Health,
} from "@/lib/api";
import { Bell,Circle,Cloud,CloudOff,Cpu,Database,GraduationCap,HelpCircle,Key,RefreshCw,Shield,Trash2 } from "lucide-react";
import { useCallback,useState } from "react";

export default function SettingsPage() {
  const { addNotification } = useSpeakFlow();
  const { isTeacher } = useAuth();

  // API key management (teacher) — live-editable, persisted to backend/.env
  const [keysStatus, setKeysStatus] = useState<KeysStatus | null>(null);
  const [groqInput, setGroqInput] = useState("");
  const [googleInput, setGoogleInput] = useState("");
  const [savingKeys, setSavingKeys] = useState(false);
  const [sttMode, setSttMode] = useState<SttMode>("auto");
  const [agentModel, setAgentModel] = useState<AgentModel>("auto");

  const loadKeysStatus = useCallback(async () => {
    if (!isTeacher) return;
    try {
      const status = await fetchKeysStatus();
      setKeysStatus(status);
      if (status.stt_mode) setSttMode(status.stt_mode);
      if (status.agent_model) setAgentModel(status.agent_model);
    } catch {
      setKeysStatus(null);
    }
  }, [isTeacher]);

  useDeferredEffect(() => { loadKeysStatus(); }, [loadKeysStatus]);

  const handleSaveEngine = async () => {
    setSavingKeys(true);
    try {
      const status = await saveKeys({ stt_mode: sttMode, agent_model: agentModel });
      setKeysStatus(status);
      addNotification({
        title: "Engine settings updated",
        message: `Applied live: STT = ${status.stt_mode}, agents = ${status.agent_model}.`,
        type: "success",
      });
    } catch ( caught) {
      const err = toError(caught);
      addNotification({ title: "Save failed", message: err.message, type: "error" });
    } finally {
      setSavingKeys(false);
    }
  };

  const handleSaveKeys = async () => {
    if (!groqInput && !googleInput) {
      addNotification({ title: "Nothing to save", message: "Paste a new key first.", type: "info" });
      return;
    }
    setSavingKeys(true);
    try {
      const status = await saveKeys({
        ...(groqInput ? { groq_api_key: groqInput.trim() } : {}),
        ...(googleInput ? { google_api_keys: googleInput.trim() } : {}),
      });
      setKeysStatus(status);
      setGroqInput("");
      setGoogleInput("");
      addNotification({
        title: "API keys updated",
        message: `Saved and applied live: ${(status.updated || []).join(", ") || "nothing changed"}.`,
        type: "success",
      });
      checkV2();
    } catch ( caught) {
      const err = toError(caught);
      addNotification({ title: "Save failed", message: err.message, type: "error" });
    } finally {
      setSavingKeys(false);
    }
  };

  // Student account management (teacher role only)
  const [accounts, setAccounts] = useState<ManagedUser[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [accountBusy, setAccountBusy] = useState<string | null>(null);

  const loadAccounts = useCallback(async () => {
    if (!isTeacher) return;
    setAccountsLoading(true);
    try {
      setAccounts(await fetchUsers());
    } catch {
      /* role or backend issue — silent, section hides itself */
    } finally {
      setAccountsLoading(false);
    }
  }, [isTeacher]);

  useDeferredEffect(() => { loadAccounts(); }, [loadAccounts]);

  const handleApprove = async (u: ManagedUser, studentId?: string) => {
    setAccountBusy(u.id);
    try {
      await approveUser(u.id, studentId);
      addNotification({ title: "Account approved", message: `${u.name} can now log in and start reading.`, type: "success" });
      await loadAccounts();
    } catch ( caught) {
      const err = toError(caught);
      addNotification({ title: "Approval failed", message: err.message, type: "error" });
    } finally {
      setAccountBusy(null);
    }
  };

  const handleReject = async (u: ManagedUser) => {
    setAccountBusy(u.id);
    try {
      await rejectUser(u.id);
      addNotification({ title: "Account rejected", message: `${u.name}'s access request was declined.`, type: "info" });
      await loadAccounts();
    } catch ( caught) {
      const err = toError(caught);
      addNotification({ title: "Rejection failed", message: err.message, type: "error" });
    } finally {
      setAccountBusy(null);
    }
  };

  const handleDeleteAccount = async (u: ManagedUser) => {
    setAccountBusy(u.id);
    try {
      await deleteUserAccount(u.id);
      addNotification({ title: "Account removed", message: `${u.name}'s account was deleted.`, type: "success" });
      await loadAccounts();
    } catch ( caught) {
      const err = toError(caught);
      addNotification({ title: "Delete failed", message: err.message, type: "error" });
    } finally {
      setAccountBusy(null);
    }
  };

  // The keys stored in backend/.env — we show their status, not their values
  const [keyStatus, setKeyStatus] = useState<{
    total: number;
    active: number;
    status: "loading" | "ok" | "error";
  }>({ total: 0, active: 0, status: "loading" });

  const [activeModel, setActiveModel] = useState("gemma-4-31b-it");
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // v2 pipeline mode + sync (roadmap UI Prompts 3 & 6)
  const [v1Health, setV1Health] = useState<V1Health | null>(null);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);

  const checkV2 = useCallback(async () => {
    try {
      setV1Health(await fetchV1Health());
    } catch {
      setV1Health(null);
    }
    try {
      setSyncStatus(await fetchSyncStatus());
    } catch {
      setSyncStatus(null);
    }
  }, []);

  const handleSyncNow = async () => {
    setSyncing(true);
    try {
      const result = await triggerSync();
      addNotification({
        title: "Sync complete",
        message: `${result.synced_count} synced, ${result.failed_count} failed.${result.note ? ` ${result.note}` : ""}`,
        type: result.failed_count > 0 ? "warning" : "success",
      });
      await checkV2();
    } catch {
      addNotification({ title: "Sync failed", message: "Could not reach the backend sync endpoint.", type: "error" });
    } finally {
      setSyncing(false);
    }
  };

  // Ping backend health and key count on mount
  const checkBackend = useCallback(async () => {
    setKeyStatus(prev => ({ ...prev, status: "loading" }));
    setBackendOnline(null);
    checkV2();
    try {
      const res = await fetch(`${API_ROOT}/health`);
      if (res.ok) {
        const data = await res.json();
        setBackendOnline(true);
        setKeyStatus({
          total: data.api_key_count ?? 0,
          active: data.api_key_count ?? 0,
          status: "ok",
        });
      } else {
        setBackendOnline(false);
        setKeyStatus(prev => ({ ...prev, status: "error" }));
      }
    } catch {
      setBackendOnline(false);
      setKeyStatus(prev => ({ ...prev, status: "error" }));
    }
  }, [checkV2, setKeyStatus, setBackendOnline]);

  useDeferredEffect(() => { checkBackend(); }, [checkBackend]);

  // Students get their own settings (profile, reading prefs, password);
  // everything below is the teacher-only system settings console.
  if (!isTeacher) {
    return <StudentSettings />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <ClassroomInvite />
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold font-sans text-text-primary">System Settings</h1>
          <p className="text-sm text-text-secondary mt-1">Teacher console — keys, engines, accounts and sync.</p>
        </div>
      </div>

      <div className="speakflow-card bg-white overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-4 min-h-[500px]">
          {/* Sidebar */}
          <div className="col-span-1 bg-gray-50 border-r border-gray-200 p-4 space-y-2">
            <button className="w-full flex items-center px-3 py-2 bg-accent-primary-bg text-accent-primary-dark font-bold text-sm rounded-lg">
              <Key className="w-4 h-4 mr-2" /> API Keys
            </button>
            <button className="w-full flex items-center px-3 py-2 text-text-secondary hover:bg-gray-100 font-medium text-sm rounded-lg transition-colors">
              <Database className="w-4 h-4 mr-2" /> Database
            </button>
            <button className="w-full flex items-center px-3 py-2 text-text-secondary hover:bg-gray-100 font-medium text-sm rounded-lg transition-colors">
              <Bell className="w-4 h-4 mr-2" /> Notifications
            </button>
            <button className="w-full flex items-center px-3 py-2 text-text-secondary hover:bg-gray-100 font-medium text-sm rounded-lg transition-colors">
              <Shield className="w-4 h-4 mr-2" /> Privacy
            </button>
          </div>

          {/* Content */}
          <div className="col-span-3 p-8">
            <h2 className="text-lg font-bold text-text-primary mb-6 flex items-center">
              <Key className="w-5 h-5 mr-2 text-text-secondary" />
              API Key Management
            </h2>

            <div className="space-y-6">

              {/* ── API keys (teacher only, live-editable) ──────────────────── */}
              {isTeacher && (
                <div>
                  <label className="block text-sm font-bold text-text-secondary mb-3 flex items-center">
                    <Key className="w-4 h-4 mr-1.5" />
                    API Keys — applied live
                  </label>
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
                    <div className="flex gap-2 mb-1">
                      <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                        keysStatus?.groq_configured
                          ? "bg-green-50 border-green-200 text-green-700"
                          : "bg-gray-100 border-gray-200 text-gray-500"
                      }`}>
                        Meta Voice / STT {keysStatus?.groq_configured ? "configured" : "not set"}
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                        keysStatus?.google_configured
                          ? "bg-green-50 border-green-200 text-green-700"
                          : "bg-gray-100 border-gray-200 text-gray-500"
                      }`}>
                        Meta Muse ({keysStatus?.google_key_count ?? 0}) {keysStatus?.google_configured ? "configured" : "not set"}
                      </span>
                      {keysStatus?.env === "demo" && (
                        <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-violet-100 border border-violet-200 text-violet-700">
                          demo mode
                        </span>
                      )}
                    </div>

                    <div>
                      <label className="block text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-1.5">
                        Meta Voice Transcribe / STT API Key
                      </label>
                      <input
                        type="password"
                        value={groqInput}
                        onChange={(e) => setGroqInput(e.target.value)}
                        placeholder={keysStatus?.groq_configured ? "•••••••• (configured — paste to replace)" : "meta_stt_..."}
                        className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm font-mono bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-1.5">
                        Meta AI Reasoning Keys (Muse Spark 1.3 / Glimmer)
                      </label>
                      <input
                        type="password"
                        value={googleInput}
                        onChange={(e) => setGoogleInput(e.target.value)}
                        placeholder={keysStatus?.google_configured ? "•••••••• (configured — paste to replace)" : "key1,key2,key3"}
                        className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm font-mono bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary"
                      />
                    </div>

                    <button
                      onClick={handleSaveKeys}
                      disabled={savingKeys}
                      className="px-5 py-2.5 rounded-xl bg-text-primary text-white text-sm font-bold hover:bg-gray-800 disabled:opacity-60"
                    >
                      {savingKeys ? "Saving…" : "Save & Apply Now"}
                    </button>
                    <p className="text-xs text-text-muted">
                      Keys are written to <code className="bg-gray-200 px-1 rounded">backend/.env</code> and take effect
                      immediately — no restart needed. Stored masked; never displayed back.
                    </p>
                  </div>
                </div>
              )}

              {/* ── AI engine selection (teacher only, live-editable) ───────── */}
              {isTeacher && (
                <div>
                  <label className="block text-sm font-bold text-text-secondary mb-3 flex items-center">
                    <Cpu className="w-4 h-4 mr-1.5" />
                    Reading AI Engine — applied live
                  </label>
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-1.5">
                          Speech-to-Text Engine
                        </label>
                        <select
                          value={sttMode}
                          onChange={(e) => setSttMode(e.target.value as SttMode)}
                          className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary"
                        >
                          <option value="auto">Auto (recommended) — Meta Voice online, local offline</option>
                          <option value="groq">Meta Voice Transcribe — fast cloud ASR</option>
                          <option value="local">Local Whisper — offline only</option>
                        </select>
                        <p className="text-[11px] text-text-muted mt-1">
                          Used by both the 2D Book and Story Mode. Local reads work
                          with no internet; cloud ASR is ~10× faster and more accurate.
                        </p>
                      </div>
                      <div>
                        <label className="block text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-1.5">
                          Diagnosis Agents (Reasoning Engine)
                        </label>
                        <select
                          value={agentModel}
                          onChange={(e) => setAgentModel(e.target.value as AgentModel)}
                          className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent-primary"
                        >
                          <option value="auto">Auto (recommended) — Muse Spark 1.3</option>
                          <option value="gemini-3.5-flash-lite">Muse Spark 1.3 — standard reasoning</option>
                          <option value="gemma-4-31b-it">Muse Glimmer — lightweight open weights</option>
                        </select>
                        <p className="text-[11px] text-text-muted mt-1">
                          The conversational coaching and phonetic agents. Auto routes to Muse Spark 1.3
                          or local Muse Glimmer for Pakistan Geographic Use Policy compliance.
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleSaveEngine}
                      disabled={savingKeys ||
                        (sttMode === (keysStatus?.stt_mode ?? "auto") &&
                         agentModel === (keysStatus?.agent_model ?? "auto"))}
                      className="px-5 py-2.5 rounded-xl bg-text-primary text-white text-sm font-bold hover:bg-gray-800 disabled:opacity-60"
                    >
                      {savingKeys ? "Saving…" : "Save Engine Settings"}
                    </button>
                  </div>
                </div>
              )}

              {/* ── Student accounts & approvals (teacher only) ─────────────── */}
              {isTeacher && (
                <div>
                  <label className="block text-sm font-bold text-text-secondary mb-3 flex items-center">
                    <GraduationCap className="w-4 h-4 mr-1.5" />
                    Student Accounts
                  </label>
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    {accountsLoading ? (
                      <p className="text-sm text-text-muted py-2">Loading accounts…</p>
                    ) : (
                      <div className="space-y-4">
                        <StudentApprovals accounts={accounts} loading={accountsLoading} busyId={accountBusy} onApprove={handleApprove} onReject={handleReject} />

                        {/* All accounts */}
                        <div>
                          <p className="text-xs font-mono font-bold uppercase tracking-wider text-text-muted mb-2">
                            All accounts ({accounts.length})
                          </p>
                          <div className="space-y-1.5">
                            {accounts.map((u) => (
                              <div key={u.id} className="flex items-center gap-3 bg-white rounded-lg border border-gray-100 px-3 py-2">
                                <span className={`h-2 w-2 rounded-full ${u.status === "approved" ? "bg-status-complete" : u.status === "pending" ? "bg-amber-400" : "bg-red-400"}`} />
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-bold text-text-primary truncate">
                                    {u.name}
                                    {u.role === "teacher" && (
                                      <span className="ml-2 px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-accent-primary-bg text-accent-primary-dark">teacher</span>
                                    )}
                                  </p>
                                  <p className="text-xs text-text-muted font-mono">@{u.username}{u.student_id ? ` · ${u.student_id}` : ""}</p>
                                </div>
                                <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-full ${
                                  u.status === "approved" ? "bg-green-100 text-green-700" :
                                  u.status === "pending" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-600"
                                }`}>
                                  {u.status}
                                </span>
                                {u.role !== "teacher" && (
                                  <button
                                    onClick={() => handleDeleteAccount(u)}
                                    disabled={accountBusy === u.id}
                                    title="Delete account"
                                    className="p-1.5 rounded-lg text-text-muted hover:text-red-500 hover:bg-red-50 disabled:opacity-50"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Backend status card */}
              <div className={`p-4 rounded-xl border ${backendOnline === true ? "bg-green-50 border-green-200" : backendOnline === false ? "bg-red-50 border-red-200" : "bg-gray-50 border-gray-200"}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-bold text-text-primary">
                      Backend Server
                      <span className={`ml-2 text-xs font-mono px-2 py-0.5 rounded-full ${
                        backendOnline === true ? "bg-green-100 text-green-700" :
                        backendOnline === false ? "bg-red-100 text-red-700" :
                        "bg-gray-100 text-gray-500"
                      }`}>
                        {backendOnline === true ? "ONLINE" : backendOnline === false ? "OFFLINE" : "CHECKING..."}
                      </span>
                    </p>
                    <p className="text-xs text-text-secondary mt-1">
                      {backendOnline === true
                        ? "Connected to the backend API (port 8000)"
                        : "Cannot reach FastAPI backend. Is uvicorn running?"}
                    </p>
                  </div>
                  <button
                    onClick={checkBackend}
                    className="p-2 rounded-lg hover:bg-white transition-colors"
                    title="Re-check backend"
                  >
                    <RefreshCw className="w-4 h-4 text-text-secondary" />
                  </button>
                </div>
              </div>

              {/* API Key pool status */}
              <div>
                <label className="block text-sm font-bold text-text-secondary mb-3">
                  Google API Key Pool
                </label>
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-text-primary font-medium">
                      Keys configured in <code className="text-xs bg-gray-200 px-1 rounded">backend/.env</code>
                    </span>
                    <span className={`text-xs font-mono font-bold px-2 py-1 rounded-full ${
                      keyStatus.status === "ok" ? "bg-green-100 text-green-700" :
                      keyStatus.status === "error" ? "bg-red-100 text-red-700" :
                      "bg-gray-200 text-gray-500"
                    }`}>
                      {keyStatus.status === "loading" ? "..." :
                       keyStatus.status === "ok" ? `${keyStatus.total} ACTIVE` : "UNREACHABLE"}
                    </span>
                  </div>

                  {/* Show key slots */}
                  <div className="space-y-2">
                    {Array.from({ length: Math.max(keyStatus.total, 3) }).map((_, i) => (
                      <div key={i} className="flex items-center gap-3 px-3 py-2 bg-white rounded-lg border border-gray-100">
                        <Circle className={`w-2 h-2 fill-current ${
                          i < keyStatus.active && keyStatus.status === "ok"
                            ? "text-status-good"
                            : "text-gray-300"
                        }`} />
                        <span className="text-xs font-mono text-text-muted">
                          {i < keyStatus.active && keyStatus.status === "ok"
                            ? `API Key ${i + 1} — ●●●●●●●●●●●●●●●●●●●●●●●●●●●● (active)`
                            : `API Key ${i + 1} — not configured`}
                        </span>
                      </div>
                    ))}
                  </div>

                  <p className="text-xs text-text-muted mt-3">
                    Keys are read from <code className="bg-gray-200 px-1 rounded">backend/.env → GOOGLE_API_KEYS</code>.
                    The orchestrator rotates between them automatically on rate-limit errors.
                    To add or change keys, edit the file directly and restart the backend.
                  </p>
                </div>
              </div>

              <hr className="border-gray-100" />

              {/* Pipeline mode + sync (roadmap UI Prompts 3 & 6) */}
              <div>
                <label className="block text-sm font-bold text-text-secondary mb-3">
                  Pipeline Mode &amp; Sync
                </label>
                <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-text-primary flex items-center gap-2">
                        {v1Health ? (
                          v1Health.mode === "online"
                            ? <Cloud className="w-4 h-4 text-sky-500" />
                            : <CloudOff className="w-4 h-4 text-amber-500" />
                        ) : (
                          <HelpCircle className="w-4 h-4 text-gray-400" />
                        )}
                        {v1Health
                          ? v1Health.mode === "online" ? "Cloud (online)" : "Local host (offline)"
                          : "Backend unreachable"}
                      </p>
                      <p className="text-xs text-text-secondary mt-1">
                        {v1Health
                          ? v1Health.mode === "online"
                            ? "Online STT (Meta Voice) and Meta Muse coaching are available."
                            : "Running fully local — offline Whisper + phonetic templates."
                          : "Start the FastAPI backend to see pipeline mode."}
                      </p>
                    </div>
                    <button onClick={checkV2} className="p-2 rounded-lg hover:bg-white transition-colors" title="Re-check pipeline mode">
                      <RefreshCw className="w-4 h-4 text-text-secondary" />
                    </button>
                  </div>

                  <div className="flex gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                      v1Health?.groq_reachable
                        ? "bg-green-50 border-green-200 text-green-700"
                        : "bg-gray-100 border-gray-200 text-gray-500"
                    }`}>
                      Meta Voice STT {v1Health?.groq_configured ? "configured · connection unchecked" : "not configured"}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold border ${
                      v1Health?.gemini_reachable
                        ? "bg-green-50 border-green-200 text-green-700"
                        : "bg-gray-100 border-gray-200 text-gray-500"
                    }`}>
                      Meta Muse Reasoning {v1Health?.gemini_configured ? "configured · connection unchecked" : "not configured"}
                    </span>
                  </div>

                  {/* Sync queue */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                    <div>
                      <p className="text-sm font-bold text-text-primary">
                        Sync queue: {syncStatus ? syncStatus.queued : "--"} session{syncStatus?.queued === 1 ? "" : "s"} waiting
                      </p>
                      <p className="text-xs text-text-secondary mt-0.5">
                        Offline sessions sync automatically on reconnect{syncStatus && !syncStatus.cloud_configured ? " (no cloud target configured — queue is retained locally)" : ""}.
                      </p>
                    </div>
                    <button
                      onClick={handleSyncNow}
                      disabled={syncing}
                      className="px-4 py-2 bg-text-primary text-white text-xs font-bold rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 ml-2 whitespace-nowrap"
                    >
                      {syncing ? "Syncing..." : "Sync Now"}
                    </button>
                  </div>
                </div>
              </div>

              <hr className="border-gray-100" />

              {/* Active model */}
              <div>
                <label className="block text-sm font-bold text-text-secondary mb-2">Active AI Model</label>
                <select
                  value={activeModel}
                  onChange={(e) => setActiveModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-1 focus:ring-accent-primary"
                >
                  <option value="gemma-4-31b-it">gemma-4-31b-it — Recommended (Text reasoning)</option>
                  <option value="gemma-4-26b-it">gemma-4-26b-it — MoE variant (faster)</option>
                </select>
                <p className="text-xs text-text-muted mt-2">
                  Model selection is configured in <code className="bg-gray-100 px-1 rounded">backend/agents/orchestrator.py</code>.
                  Only text-capable models are listed here. Audio preprocessing is handled by Whisper + Librosa.
                </p>
              </div>

              {/* Info box — honest architecture description (roadmap UI Prompt 3) */}
              <div className="p-4 bg-accent-primary-bg rounded-xl border border-accent-primary/20">
                <p className="text-xs font-bold text-accent-primary-dark mb-1">How the pipeline works</p>
                <p className="text-xs text-text-secondary leading-relaxed">
                  SOVEN runs two processing layers. <strong>Story Mode (v2):</strong> speech-to-text via the
                  Groq Whisper API when online, or a local Whisper model offline; acoustic evidence via
                  <strong> librosa</strong>; and <strong>Gemini</strong> for feedback text plus an optional judgment
                  on ambiguous pauses — note that this hesitation call sends a short raw audio clip to
                  Google&apos;s API, unlike the rest of the pipeline. <strong>Live Dashboard (classic pipeline):</strong>{" "}
                  local Whisper + Librosa processing with 5 parallel <strong>Gemma</strong> reasoning agents — only
                  text telemetry goes to the Google API. Raw audio files are deleted immediately after
                  processing; only aggregated results are stored.
                </p>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
