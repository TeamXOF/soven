"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Activity, Volume2, Mic, PauseCircle, Award, BarChart2 } from "lucide-react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";
import Brand from "@/components/soven/Brand";
import { useAuth } from "@/components/auth/AuthProvider";

// Pitch contour sample (65Hz C2 - 2093Hz C7)
const DEFAULT_PITCH_DATA = [
  { time: "0.0s", pitch: 180, loudness: -28, pause: 0 },
  { time: "0.4s", pitch: 195, loudness: -22, pause: 0 },
  { time: "0.8s", pitch: 210, loudness: -18, pause: 0 },
  { time: "1.2s", pitch: 205, loudness: -20, pause: 0 },
  { time: "1.6s", pitch: null, loudness: -45, pause: 0.6 }, // pause
  { time: "2.0s", pitch: null, loudness: -46, pause: 0.6 },
  { time: "2.4s", pitch: 175, loudness: -24, pause: 0 },
  { time: "2.8s", pitch: 185, loudness: -19, pause: 0 },
  { time: "3.2s", pitch: 190, loudness: -21, pause: 0 },
  { time: "3.6s", pitch: 195, loudness: -22, pause: 0 },
  { time: "4.0s", pitch: null, loudness: -48, pause: 0.5 },
  { time: "4.4s", pitch: 182, loudness: -20, pause: 0 },
  { time: "4.8s", pitch: 178, loudness: -26, pause: 0 },
];

const FLUENCY_COMPARISON = [
  { attempt: "Attempt 1", raw_wpm: 82, wcpm: 58, accuracy: 78 },
  { attempt: "Attempt 2", raw_wpm: 76, wcpm: 66, accuracy: 88 },
  { attempt: "Attempt 3", raw_wpm: 72, wcpm: 69, accuracy: 94 },
  { attempt: "Attempt 4", raw_wpm: 70, wcpm: 68, accuracy: 96 },
];

export default function AudioStatsDashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(DEFAULT_PITCH_DATA);
  const [fluency, setFluency] = useState(FLUENCY_COMPARISON);

  useEffect(() => {
    // If local diagnostic test was taken, inject real values
    const saved = localStorage.getItem("soven_diagnostic_result");
    if (saved) {
      try {
        const diag = JSON.parse(saved);
        if (diag.wcpm && diag.wpm) {
          setFluency(prev => [
            ...prev,
            { attempt: "Voice Test", raw_wpm: diag.wpm, wcpm: diag.wcpm, accuracy: diag.accuracy }
          ]);
        }
      } catch {}
    }
  }, []);

  return (
    <div className="soven-content py-8 px-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8 pb-4 border-b">
        <div className="flex items-center gap-4">
          <Link href="/my-progress" className="soven-icon-button" aria-label="Back">
            <ArrowLeft size={18}/>
          </Link>
          <div>
            <span className="text-xs uppercase tracking-wider text-accent-primary font-bold">
              Acoustic Telemetry & Recharts Engine
            </span>
            <h1 className="text-2xl font-extrabold text-text-primary">
              Full Audio Statistics Dashboard
            </h1>
          </div>
        </div>
        <div className="flex gap-2">
          <Link href="/book/story_forest_01" className="soven-button soven-button-small">
            Open 2D Book
          </Link>
        </div>
      </div>

      {/* Top Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Activity size={16} className="text-accent-primary"/>
            <span>Pitch Stability</span>
          </div>
          <strong className="text-2xl font-bold text-text-primary">88.5%</strong>
          <small className="block text-[11px] text-text-muted mt-1">65Hz–2093Hz range</small>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Award size={16} className="text-emerald-600"/>
            <span>WCPM Fluency</span>
          </div>
          <strong className="text-2xl font-bold text-emerald-600">68 WCPM</strong>
          <small className="block text-[11px] text-text-muted mt-1">Words Correct Per Minute</small>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <PauseCircle size={16} className="text-amber-600"/>
            <span>Pause Gaps</span>
          </div>
          <strong className="text-2xl font-bold text-amber-600">2 detected</strong>
          <small className="block text-[11px] text-text-muted mt-1">&gt;0.4s hesitation events</small>
        </div>

        <div className="p-4 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
            <Volume2 size={16} className="text-indigo-600"/>
            <span>Loudness Consistency</span>
          </div>
          <strong className="text-2xl font-bold text-indigo-600">-21 dB avg</strong>
          <small className="block text-[11px] text-text-muted mt-1">RMS power curve</small>
        </div>
      </div>

      {/* Chart 1: Pitch Contour & Pause Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <section className="p-6 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-text-primary">Pitch Contour (Hz) & Voicing</h2>
            <p className="text-xs text-text-muted">
              Continuous fundamental frequency (F0) tracking between 65 Hz (C2) and 2093 Hz (C7).
            </p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ede8"/>
                <XAxis dataKey="time" stroke="#71808b" fontSize={11}/>
                <YAxis domain={[120, 240]} stroke="#71808b" fontSize={11} unit="Hz"/>
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }}/>
                <Legend wrapperStyle={{ fontSize: 12 }}/>
                <Line
                  type="monotone"
                  dataKey="pitch"
                  name="Vocal Pitch (F0)"
                  stroke="#e84e32"
                  strokeWidth={3}
                  connectNulls={false}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Chart 2: Loudness / Energy (dB) */}
        <section className="p-6 bg-white rounded-2xl border border-border-card shadow-sm">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-text-primary">Loudness & Energy Envelope (dB)</h2>
            <p className="text-xs text-text-muted">
              RMS decibel energy curve displaying speech projection and silent pauses (&gt;0.4s).
            </p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0ede8"/>
                <XAxis dataKey="time" stroke="#71808b" fontSize={11}/>
                <YAxis domain={[-50, -10]} stroke="#71808b" fontSize={11} unit="dB"/>
                <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }}/>
                <Legend wrapperStyle={{ fontSize: 12 }}/>
                <Area
                  type="monotone"
                  dataKey="loudness"
                  name="Energy (dB)"
                  stroke="#08776b"
                  fill="#08776b"
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      {/* Chart 3: WCPM vs Raw WPM (Anti-Mumble Metric) */}
      <section className="p-6 bg-white rounded-2xl border border-border-card shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-text-primary">
              Fluency Breakdown: WCPM vs Raw WPM
            </h2>
            <p className="text-xs text-text-muted">
              Words Correct Per Minute (WCPM) eliminates rewards for fast mumbling. Dyslexia mode waives pause penalties.
            </p>
          </div>
          <span className="text-xs px-3 py-1 bg-accent-primary/10 text-accent-primary font-bold rounded-full">
            Acoustic Formula Applied
          </span>
        </div>
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={fluency} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0ede8"/>
              <XAxis dataKey="attempt" stroke="#71808b" fontSize={11}/>
              <YAxis domain={[0, 100]} stroke="#71808b" fontSize={11}/>
              <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }}/>
              <Legend wrapperStyle={{ fontSize: 12 }}/>
              <Bar dataKey="raw_wpm" name="Raw Speed (WPM)" fill="#c3ced7" radius={[4, 4, 0, 0]}/>
              <Bar dataKey="wcpm" name="Words Correct Per Minute (WCPM)" fill="#e84e32" radius={[4, 4, 0, 0]}/>
              <Bar dataKey="accuracy" name="Word Accuracy %" fill="#08776b" radius={[4, 4, 0, 0]}/>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

