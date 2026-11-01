"use client";

import { useAuth } from "@/components/auth/AuthProvider";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { fetchRoster, ManagedUser, RosterEntry } from "@/lib/api";
import { toError } from "@/lib/errors";
import { Clock, Copy, UserCheck, UserX } from "lucide-react";
import { useState } from "react";

export function ClassroomInvite() {
  const { user } = useAuth();
  const { addNotification } = useSpeakFlow();
  if (user?.role !== "teacher") return null;

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(user.classroom_code || "");
      addNotification({ title: "Code copied", message: "Share it with students for the signup page.", type: "success" });
    } catch {
      addNotification({ title: "Copy the code manually", message: "Select the classroom code shown here and copy it.", type: "info" });
    }
  };

  return (
    <section className="speakflow-card bg-white p-5" aria-label="Invite students">
      <h2 className="font-bold text-text-primary">Invite students to your class</h2>
      <p className="mt-1 text-sm text-text-secondary">Students sign up with this code, then you approve their account below.</p>
      {user.classroom_code ? (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="text-sm text-text-secondary">Classroom signup code</span>
          <strong className="select-all rounded-lg bg-gray-50 border border-gray-200 px-3 py-2 font-mono" data-testid="classroom-signup-code">{user.classroom_code}</strong>
          <button type="button" onClick={copyCode} className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-bold text-text-primary hover:bg-gray-50">
            <Copy className="h-4 w-4" /> Copy code
          </button>
        </div>
      ) : <p className="mt-3 text-sm text-amber-700">Reload the page to retrieve your classroom code. Contact the administrator if it is still missing.</p>}
      <p className="mt-3 text-xs text-text-secondary">After approval, the account is linked to one student profile. There is no need to add the child to the roster first.</p>
    </section>
  );
}

type Props = {
  accounts: ManagedUser[];
  loading: boolean;
  busyId: string | null;
  onApprove: (user: ManagedUser, studentId?: string) => Promise<void>;
  onReject: (user: ManagedUser) => Promise<void>;
};

export default function StudentApprovals({ accounts, loading, busyId, onApprove, onReject }: Props) {
  const [roster, setRoster] = useState<RosterEntry[]>([]);
  const [rosterLoading, setRosterLoading] = useState(true);
  const [rosterError, setRosterError] = useState("");
  const [selections, setSelections] = useState<Record<string, string>>({});
  useDeferredEffect(() => {
    let active = true;
    setRosterLoading(true);
    setRosterError("");
    fetchRoster().then((rows) => { if (active) setRoster(rows); })
      .catch((error) => { if (active) setRosterError(toError(error).message); })
      .finally(() => { if (active) setRosterLoading(false); });
    return () => { active = false; };
  }, [accounts]);

  const pending = accounts.filter((account) => account.role === "student" && account.status === "pending");
  const available = roster.filter((profile) => !profile.account_username);
  return (
    <section aria-label="Student signup approvals" className="space-y-3">
      <h2 className="flex items-center gap-2 text-sm font-bold text-text-primary"><Clock className="h-4 w-4 text-amber-500" /> Waiting for approval ({pending.length})</h2>
      <p className="text-xs text-text-secondary">Approve to create the child&apos;s student profile, or choose their existing profile to keep its reading history.</p>
      {loading ? <p className="text-sm text-text-muted">Loading signups…</p> : pending.length === 0 ? <p className="text-sm text-text-muted">No pending signups.</p> : (
        <div className="space-y-3">
          {rosterError && <p role="alert" className="text-sm text-red-600">Could not load student profiles: {rosterError}. Reload before approving.</p>}
          {pending.map((account) => {
            const matches = available.filter((profile) => profile.name.trim().toLowerCase() === account.name.trim().toLowerCase());
            const selected = selections[account.id] ?? account.student_id ?? (matches.length ? "" : "__new__");
            const busy = busyId !== null;
            return (
              <div key={account.id} className="rounded-xl border border-amber-200 bg-white p-4">
                <p className="font-bold text-text-primary">{account.name} <span className="text-xs font-normal text-text-muted">@{account.username}</span></p>
                <label className="mt-3 block text-xs font-bold text-text-secondary">
                  Student profile for @{account.username}
                  <select value={selected} onChange={(event) => setSelections((previous) => ({ ...previous, [account.id]: event.target.value }))}
                    disabled={busy || rosterLoading || !!rosterError || !!account.student_id}
                    className="mt-1 w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-normal">
                    <option value="" disabled>Choose a student profile</option>
                    <option value="__new__">Create a new student profile</option>
                    {account.student_id && <option value={account.student_id}>Keep current linked profile</option>}
                    {available.map((profile) => <option key={profile.id} value={profile.id}>{profile.name} · Grade {profile.grade} · {profile.level} · {profile.id}</option>)}
                  </select>
                </label>
                {matches.length > 0 && <p className="mt-2 text-xs text-amber-800">A profile with this name already exists. Choose it only if it belongs to this child, or explicitly create a new profile.</p>}
                <div className="mt-3 flex gap-2">
                  <button type="button" onClick={() => void onApprove(account, selected === "__new__" ? undefined : selected)}
                    disabled={busy || loading || rosterLoading || !!rosterError || !selected}
                    className="inline-flex items-center gap-1 rounded-lg bg-status-complete px-3 py-2 text-xs font-bold text-white disabled:opacity-50">
                    <UserCheck className="h-4 w-4" /> {busyId === account.id ? "Saving…" : "Approve"}
                  </button>
                  <button type="button" onClick={() => void onReject(account)} disabled={busy || loading}
                    className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs font-bold text-red-600 disabled:opacity-50">
                    <UserX className="h-4 w-4" /> Reject
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
