"use client";
import Image from "next/image";
import Link from "next/link";
import { useRef, useState } from "react";
import { ArrowRight, CheckCircle2, GraduationCap, UserRound } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { apiRegisterAdult } from "@/lib/api";
import Brand from "@/components/soven/Brand";
export default function SignupPage() {
    const { register } = useAuth();
    const [mode, setMode] = useState<"child" | "adult">("child");
    const [name, setName] = useState("");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [classroomCode, setClassroomCode] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [done, setDone] = useState(false);
    const locked = useRef(false);
    async function submit(event: React.FormEvent) {
        event.preventDefault();
        if (locked.current)
            return;
        locked.current = true;
        setBusy(true);
        setError("");
        try {
            if (mode === "adult")
                await apiRegisterAdult(name, username, password);
            else
                await register(name, username, password, classroomCode);
            setDone(true);
        }
        catch (error) {
            setError(error instanceof Error ? error.message : "Could not create your account. Please try again.");
        }
        finally {
            setBusy(false);
            locked.current = false;
        }
    }
    return <div className="soven-auth-page"><header className="soven-public-nav"><Brand /><Link href="/login">Already reading with us? <strong>Sign in</strong></Link></header>
    <main className="soven-auth-grid"><aside className="soven-auth-art"><div><p className="soven-eyebrow">A CHAPTER JUST FOR YOU</p><h2>A little practice.<br />A little more possibility.</h2><p>There’s no rush. Start where you are.</p></div><Image src="/illustrations/reading-nook.webp" alt="A reader enjoying a book in a sunny room" width={960} height={640}/></aside>
      <section className="soven-form-card">{done ? <div className="soven-success"><CheckCircle2 size={42}/><h1>Account created!</h1><p>{mode === "child" ? "Your teacher needs to approve and link your account before you can sign in. Ask them to check their Students page." : "Your personal reading space is ready. Sign in next to choose your languages and reading preferences."}</p><Link href="/login" className="soven-button">Go to sign in <ArrowRight size={17}/></Link></div> : <>
        <p className="soven-eyebrow">LET’S GET TO KNOW YOU</p><h1>{mode === "child" ? "Join your class" : "Your reading journey starts here"}</h1><p className="soven-muted">Choose the reading space that’s right for you.</p>
        <div className="soven-mode-switch" role="group" aria-label="Account type"><button disabled={busy} aria-pressed={mode === "child"} onClick={() => setMode("child")}><GraduationCap size={18}/>Classroom reader</button><button disabled={busy} aria-pressed={mode === "adult"} onClick={() => setMode("adult")}><UserRound size={18}/>Independent adult</button></div>
        <form onSubmit={submit} className="soven-form">
          {mode === "child" && <label>Classroom code<input value={classroomCode} onChange={e => setClassroomCode(e.target.value)} required maxLength={100} placeholder="Ask your teacher for the code"/><small>Your teacher approves new accounts before first login.</small></label>}
          {mode === "adult" && <p className="soven-note">For adults reading independently. Your records belong to your own private reading space.</p>}
          <label>Your name<input autoComplete="name" value={name} onChange={e => setName(e.target.value)} required maxLength={120} placeholder="What should we call you?"/></label>
          <label>Username<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required maxLength={64} placeholder="letters, numbers, . _ -"/></label>
          <label>Password<input autoComplete="new-password" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={10} maxLength={256} placeholder="at least 10 characters"/></label>
          <p className="soven-fine">Recordings in reading sessions go to the server for analysis. <Link href="/privacy">Read how data is used.</Link></p>
          {error && <p role="alert" className="soven-error">{error}</p>}
          <button disabled={busy} className="soven-button" type="submit">{busy ? "Creating your account…" : "Create My Account"}<ArrowRight size={17}/></button>
        </form><p className="soven-fine">Want to check your microphone first? <Link href="/try">Try it here</Link></p>
      </>}</section>
    </main>
  </div>;
}
