"use client";

/**
 * Weekly Progress chart on the engine dashboard — REAL data from the active
 * student's actual session history (accuracy + WPM per session). Empty state
 * when no sessions exist yet; nothing is mocked.
 */

import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { fetchSessions } from "@/lib/api";
import { LineChart as ChartIcon } from "lucide-react";
import { useEffect,useState } from "react";
import { CartesianGrid,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis } from "recharts";

type Point = { name: string; wpm: number | null; accuracy: number | null };

export default function ProgressChart() {
  const { activeStudent, sessionState, language } = useSpeakFlow();
  const ur = language === "ur";
  const [points, setPoints] = useState<Point[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!activeStudent) { setPoints([]); setLoading(false); return; }
      setLoading(true);
      try {
        const sessions = await fetchSessions(activeStudent.id);
        if (cancelled) return;
        const recent = sessions.filter(s => (s.language || "en") === language)
          .sort((a, b) => (a.timestamp > b.timestamp ? 1 : -1))
          .slice(-7);
        setPoints(recent.map((s) => ({
          name: new Date(s.timestamp.replace(" ", "T") + "Z").toLocaleString(ur ? "ur-PK" : "en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }),
          wpm: s.wpm != null ? Math.round(s.wpm) : null,
          accuracy: s.accuracy != null ? Math.round(s.accuracy * 100) : null,
        })));
      } catch {
        if (!cancelled) setPoints([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [activeStudent, sessionState, language, ur]);

  return (
    <div className="speakflow-card p-6 h-full bg-white flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold font-sans text-text-primary flex items-center">
            <ChartIcon className="w-5 h-5 mr-2 text-text-muted" />
            {ur ? "پچھلی ریکارڈنگز" : "Recent Readings"}
          </h2>
          <p className="text-sm text-text-secondary">{ur ? "اردو کی آخری سات ریکارڈنگز" : language === "es" ? "Last seven Spanish readings" : "Last seven English readings"} · {activeStudent?.name}</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-accent-primary mr-2"></div>
            <span className="text-xs font-mono text-text-muted">WPM</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-status-good mr-2"></div>
            <span className="text-xs font-mono text-text-muted">{ur ? "الفاظ کا موازنہ" : "WORD MATCH %"}</span>
          </div>
        </div>
      </div>

      <div className="flex-1 w-full min-h-[200px]">
        {loading ? (
          <div className="h-full flex items-center justify-center text-sm text-text-muted">Loading history…</div>
        ) : points.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <p className="text-sm text-text-muted">
              {ur ? "اس زبان میں ابھی کوئی ریکارڈنگ نہیں ہے۔" : "No readings yet in this language. Complete a recording to see it here."}
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
              <XAxis
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#9CA3AF", fontSize: 12, fontFamily: "monospace" }}
                dy={10}
              />
              <YAxis yAxisId="left" width={55} label={{ value: "WPM", angle: -90, position: "insideLeft" }} axisLine={false} tickLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} width={55} label={{ value: "%", angle: 90, position: "insideRight" }} axisLine={false} tickLine={false} tick={{ fill: "#9CA3AF", fontSize: 12 }} />
              <Tooltip contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="wpm"
                name="WPM"
                stroke="var(--accent-primary-dark)"
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2 }}
                activeDot={{ r: 6 }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="accuracy"
                name={ur ? "الفاظ کا موازنہ %" : "Word Match %"}
                stroke="var(--status-good)"
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
