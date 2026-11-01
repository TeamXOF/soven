"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { toError } from "@/lib/errors";

import type { AgentResult } from "@/lib/agentTypes";
import { getStoredUser, runPipeline } from "@/lib/api";
import { useAuth } from "@/components/auth/AuthProvider";
import { loadPrefs,savePrefs } from "@/lib/prefs";
import React,{ createContext,ReactNode,useContext,useState,useCallback } from "react";

// Types for the global state
export type SessionState = "idle" | "listening" | "processing" | "complete";

export interface AgentStatus {
  id: string;
  name: string;
  status: "pending" | "processing" | "complete" | "error";
  result?: AgentResult;
}

export interface Student {
  id: string;
  name: string;
  grade: string;
  level: string;
}

export interface AppNotification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
  dismissed: boolean;
}

export type SpokenWord = {
  word: string; start: number; end: number;
  duration_ms?: number; probability?: number;
};

export type ScoredWord = {
  word: string;
  spoken?: string;
  correct: boolean;
  phoneme_mismatch: string | null;
  extra?: boolean;
};

interface SpeakFlowState {
  // Session State
  sessionState: SessionState;
  startSession: () => void;
  stopListening: () => void;
  resetSession: () => void;
  controlsLocked: boolean;

  // Active Data
  activeStudent: Student | null;
  setActiveStudent: (student: Student | null) => void;

  // Target Sentence Selection
  targetSentence: string;
  setTargetSentence: (sentence: string) => void;
  availableSentences: string[];
  addAvailableSentence: (sentence: string) => void;

  // Reading language for this dashboard ("en" | "ur") — persisted to prefs
  language: "en" | "ur";
  setLanguage: (lang: "en" | "ur") => void;
  replaceSentences: (sentences: string[]) => void;

  // Real-time Text & Audio
  transcript: string;
  setTranscript: (text: string) => void;
  recordingTime: number;
  audioVolume: number;

  // Session Results
  overallScore: number | null;
  wpm: number | null;
  accuracy: number | null;
  pauses: number | null;
  spokenWords: SpokenWord[];
  scoredWords: ScoredWord[];

  // Agents
  agents: AgentStatus[];
  setAgentStatus: (id: string, status: AgentStatus["status"], result?: AgentResult) => void;

  // Notifications
  notifications: AppNotification[];
  addNotification: (notification: Omit<AppNotification, 'id' | 'timestamp' | 'read' | 'dismissed'>) => void;
  markNotificationsAsRead: () => void;
  dismissNotification: (id: string) => void;
}

const defaultAgents: AgentStatus[] = [
  { id: "phonetic", name: "Phonetic Analyst", status: "pending" },
  { id: "difficulty", name: "Difficulty Assessor", status: "pending" },
  { id: "engagement", name: "Engagement Tracker", status: "pending" },
  { id: "practice", name: "Practice Generator", status: "pending" },
  { id: "progress", name: "Progress Synthesizer", status: "pending" },
];

const SpeakFlowContext = createContext<SpeakFlowState | undefined>(undefined);
const EN_SENTENCES = ["The cat sat on the mat.", "The little fox woke up early in the morning."];
const UR_SENTENCES = ["وہ یہاں تھا۔", "میں کتاب پڑھتا ہوں۔"];

export function SpeakFlowProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [activeStudent, setActiveStudent] = useState<Student | null>(null);
  const [starting, setStarting] = useState(false);
  const controlsLocked = starting || sessionState === "listening" || sessionState === "processing";

  const [availableSentences, setAvailableSentences] = useState<string[]>(() => loadPrefs().storyLanguage === "ur" ? UR_SENTENCES : EN_SENTENCES);

  const [targetSentence, setTargetSentenceState] = useState<string>(availableSentences[0]);
  const [language, setLanguageState] = useState<"en" | "ur">(() => loadPrefs().storyLanguage);

  const [spokenWords, setSpokenWords] = useState<SpokenWord[]>([]);
  const [scoredWords, setScoredWords] = useState<ScoredWord[]>([]);
  const [transcript, setTranscript] = useState("");
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioVolume, setAudioVolume] = useState(0);

  const [overallScore, setOverallScore] = useState<number | null>(null);
  const [wpm, setWpm] = useState<number | null>(null);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [pauses, setPauses] = useState<number | null>(null);

  const [agents, setAgents] = useState<AgentStatus[]>(defaultAgents);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);

  const addNotification = useCallback((notif: Omit<AppNotification, 'id' | 'timestamp' | 'read' | 'dismissed'>) => {
    const newNotif: AppNotification = {
      ...notif,
      id: Math.random().toString(36).substring(7),
      timestamp: new Date(),
      read: false,
      dismissed: false
    };
    setNotifications(prev => [newNotif, ...prev].slice(0, 100));
  }, []);

  const markNotificationsAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);
  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, dismissed: true } : n));
  }, []);

  // Refs for audio processing
  const mediaRecorderRef = React.useRef<MediaRecorder | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const audioChunksRef = React.useRef<Blob[]>([]);
  const timerRef = React.useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = React.useRef<AudioContext | null>(null);
  const analyserRef = React.useRef<AnalyserNode | null>(null);
  const animationFrameRef = React.useRef<number | null>(null);
  const phaseRef = React.useRef<"starting" | "recording" | "processing" | null>(null);
  const versionRef = React.useRef(0);
  const attemptRef = React.useRef<{ studentId: string; name: string; target: string; language: "en" | "ur"; ownerId: string; version: number } | null>(null);

  const cleanupAudio = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    const recorder = mediaRecorderRef.current;
    if (recorder?.state === "recording") recorder.stop();
    recorder?.stream.getTracks().forEach(track => track.stop());
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
    mediaRecorderRef.current = null;
    if (audioContextRef.current?.state !== "closed") void audioContextRef.current?.close();
    audioContextRef.current = null;
    analyserRef.current = null;
  }, []);

  const invalidateAttempt = useCallback(() => {
    versionRef.current++;
    phaseRef.current = null;
    attemptRef.current = null;
    cleanupAudio();
  }, [cleanupAudio]);
  const resetSession = useCallback(() => {
    invalidateAttempt();
    setStarting(false);
    setSessionState("idle");
    setAgents(defaultAgents);
    setRecordingTime(0);
    setAudioVolume(0);
    setTranscript("");
    setOverallScore(null);
    setWpm(null);
    setAccuracy(null);
    setPauses(null);
    setSpokenWords([]);
    setScoredWords([]);
  }, [invalidateAttempt]);

  const addAvailableSentence = (sentence: string) => {
    if (!availableSentences.includes(sentence)) {
      setAvailableSentences(prev => [...prev, sentence]);
    }
  };

  /** Swap the whole warm-up pool (dynamic sentence generator) and target the first. */
  const replaceSentences = (sentences: string[]) => {
    if (phaseRef.current) return;
    const clean = sentences.filter(Boolean);
    if (!clean.length) return;
    resetSession();
    setAvailableSentences(clean);
    setTargetSentenceState(clean[0]);
  };


  const setTargetSentence = (sentence: string) => {
    if (phaseRef.current) return;
    resetSession();
    setTargetSentenceState(sentence);
  };

  // Reading language — initialized from the student's saved preference

  const setLanguage = (lang: "en" | "ur") => {
    if (phaseRef.current || lang === language) return;
    resetSession();
    setLanguageState(lang);
    const pool = lang === "ur" ? UR_SENTENCES : EN_SENTENCES;
    setAvailableSentences(pool);
    setTargetSentenceState(pool[0]);
    savePrefs({ storyLanguage: lang });
  };


  useDeferredEffect(() => {
    resetSession();
    setNotifications([]);
    return invalidateAttempt;
  }, [user?.id, resetSession, invalidateAttempt]);

  const startSession = async () => {
    if (phaseRef.current || !activeStudent || !user) return;
    resetSession();
    const version = ++versionRef.current;
    phaseRef.current = "starting";
    setStarting(true);
    const attempt = { studentId: activeStudent.id, name: activeStudent.name, target: targetSentence, language, ownerId: user.id, version };
    attemptRef.current = attempt;
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("Use localhost or HTTPS and enable microphone access.");
      // Honor the student's preferred mic (Settings → Reading Preferences);
      // fall back to the system default if that device has vanished.
      const savedMic = loadPrefs().preferredMic;
      // noiseSuppression OFF: Chrome's suppressor smears quiet word endings
      // (the -ed/-t sounds) that reading assessment depends on
      const micConstraints: MediaTrackConstraints = { noiseSuppression: false };
      let stream: MediaStream;
      if (savedMic) {
        try {
          stream = await navigator.mediaDevices.getUserMedia({
            audio: { deviceId: { exact: savedMic }, ...micConstraints },
          });
        } catch {
          stream = await navigator.mediaDevices.getUserMedia({ audio: micConstraints });
        }
      } else {
        stream = await navigator.mediaDevices.getUserMedia({ audio: micConstraints });
      }
      if (versionRef.current !== version || getStoredUser()?.id !== attempt.ownerId) {
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      phaseRef.current = "recording";
      streamRef.current = stream;
      setStarting(false);

      setSessionState("listening");
      setTranscript(""); // Clear transcript for new session
      setAgents(defaultAgents); // Reset agents
      setRecordingTime(0);
      audioChunksRef.current = [];

      // Setup Audio Analyser for volume visualization
      audioContextRef.current = new window.AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const updateVolume = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((acc, val) => acc + val, 0) / bufferLength;
          setAudioVolume(average);
        }
        animationFrameRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      // Setup MediaRecorder — high bitrate so word endings survive compression
      let mediaRecorder: MediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, { audioBitsPerSecond: 128000 });
      } catch {
        mediaRecorder = new MediaRecorder(stream);
      }
      mediaRecorderRef.current = mediaRecorder;
      const chunks = audioChunksRef.current;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.start(100); // collect 100ms chunks of data

      // Start Timer — the displayed 30s cap is now actually enforced
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (err) {
      if (versionRef.current !== version || getStoredUser()?.id !== attempt.ownerId) return;
      cleanupAudio();
      phaseRef.current = null;
      setStarting(false);
      setSessionState("idle");
      console.error("Error accessing microphone:", err);
      addNotification({
        title: "Microphone Access Denied",
        message: toError(err).message || "Please allow microphone access to start a reading session.",
        type: "error"
      });
    }
  };

  const stopListening = async () => {
    if (phaseRef.current !== "recording" || !attemptRef.current) return;
    phaseRef.current = "processing";
    const attempt = attemptRef.current;
    const current = () => versionRef.current === attempt.version && getStoredUser()?.id === attempt.ownerId;
    const recorder = mediaRecorderRef.current;
    const chunks = audioChunksRef.current;
    setSessionState("processing");
    setAgents(defaultAgents.map(a => ({ ...a, status: "processing" })));

    // Stop recording and wait for final chunks
    await new Promise<void>((resolve) => {
      if (recorder && recorder.state !== "inactive") {
        recorder.onstop = () => {
          recorder.stream.getTracks().forEach(track => track.stop());
          resolve();
        };
        recorder.stop();
      } else {
        resolve();
      }
    });

    if (!current()) return;
    cleanupAudio();

    setAudioVolume(0);
    setSessionState("processing");

    // Convert audio blob to base64
    const audioBlob = new Blob(chunks, { type: recorder?.mimeType || chunks[0]?.type || 'audio/webm' });

    try {
      const base64Audio = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64String = (reader.result as string).split(',')[1];
          resolve(base64String);
        };
        reader.onerror = reject;
      });
      if (!current()) return;

      // Call the REAL Python FastAPI backend with base64 audio
      const response = await runPipeline(
        attempt.studentId,
        base64Audio,
        attempt.target,
        attempt.language
      );
      if (!current()) return;

      // Set transcript from Whisper output
      if (response.transcript) {
        setTranscript(response.transcript);
      }

      // Set score, WPM, and telemetry from real backend computation
      if (response.overall_score != null) setOverallScore(response.overall_score);
      if (response.wpm != null) setWpm(response.wpm);
      if (response.accuracy != null) setAccuracy(response.accuracy);
      if (response.pauses != null) setPauses(response.pauses);
      setSpokenWords(response.words_spoken || []);
      setScoredWords(response.words || []);

      // Update each agent with its real result
      const diagnosis = response.diagnosis || {};
      setAgents(prev => prev.map(agent => {
        const result = diagnosis[agent.id];
        return {
          ...agent,
          status: result && !result.error ? "complete" : "error",
          result: result ?? null,
        };
      }));

      setSessionState("complete");
      phaseRef.current = null;
      addNotification({
        title: "Session Complete",
        message: attempt.language === "ur" ? `پڑھنا مکمل۔ لفظی موازنہ: ${response.accuracy ?? "--"}٪۔` : `Reading saved for ${attempt.name}. Word match: ${response.accuracy ?? "--"}%.`,
        type: "success",
      });
    } catch ( caught) {
      if (!current()) return;
      phaseRef.current = null;
      const error = toError(caught);
      console.error("Pipeline execution failed:", error);
      setAgents(prev => prev.map(a => ({ ...a, status: "error" })));
      setSessionState("idle");
      addNotification({
        title: "Session Failed",
        message: error?.message || "Failed to connect to backend AI agents.",
        type: "error",
      });
    }
  };

  // Enforce the 30-second cap shown in the UI (auto-stop)
  useDeferredEffect(() => {
    if (sessionState === "listening" && recordingTime >= 30) {
      stopListening();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordingTime, sessionState]);

  const setAgentStatus = useCallback((id: string, status: AgentStatus["status"], result?: AgentResult) => {
    setAgents(prev => prev.map(a => a.id === id ? { ...a, status, result } : a));
  }, []);

  return (
    <SpeakFlowContext.Provider value={{
      sessionState, startSession, stopListening, resetSession, controlsLocked,
      activeStudent, setActiveStudent,
      targetSentence, setTargetSentence, availableSentences, addAvailableSentence, replaceSentences,
      language, setLanguage,
      transcript, setTranscript,
      recordingTime, audioVolume,
      overallScore, wpm, accuracy, pauses, spokenWords, scoredWords,
      agents, setAgentStatus,
      notifications, addNotification, markNotificationsAsRead, dismissNotification
    }}>
      {children}
    </SpeakFlowContext.Provider>
  );
}

export function useSpeakFlow() {
  const context = useContext(SpeakFlowContext);
  if (context === undefined) {
    throw new Error("useSpeakFlow must be used within a SpeakFlowProvider");
  }
  return context;
}
