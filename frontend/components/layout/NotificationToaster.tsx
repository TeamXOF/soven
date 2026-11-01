"use client";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { X } from "lucide-react";

/** Page-flow feedback. Dismissal is stored independently of bell history/read state. */
export default function NotificationRegion() {
  const { notifications, dismissNotification } = useSpeakFlow();
  const alert = notifications.find(n => !n.dismissed && (n.type === "error" || n.type === "warning"));
  const latest = notifications[0];
  return <section aria-label="Page notifications" className={alert ? "mx-3 mt-3 sm:mx-6 shrink-0" : ""}>
    <p className="sr-only" role="status" aria-live="polite">{latest && latest.type !== "error" && latest.type !== "warning" ? latest.message : ""}</p>
    {alert && <div role="alert" className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div className="min-w-0 flex-1"><p className="font-bold">{alert.title}</p><p className="text-sm mt-1 break-words">{alert.message}</p></div>
      <button aria-label="Dismiss message" onClick={() => dismissNotification(alert.id)} className="shrink-0 p-1"><X className="w-5 h-5" /></button>
    </div>}
  </section>;
}
