"use client";
import Image from "next/image";
import Link from "next/link";
import { Suspense, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRight } from "lucide-react";
import Brand from "@/components/soven/Brand";
import { useAuth } from "@/components/auth/AuthProvider";
import { homeFor } from "@/components/auth/AuthGate";
function LoginForm() {
    const { login } = useAuth();
    const router = useRouter();
    const params = useSearchParams();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);
    const lock = useRef(false);
    async function submit(event: React.FormEvent) {
        event.preventDefault();
        if (lock.current)
            return;
        lock.current = true;
        setBusy(true);
        setError("");
        try {
            const user = await login(username, password);
            const next = params.get("next");
            const safe = next?.startsWith("/") && !next.startsWith("//") && !next.includes("\\") && !/^\/(login|signup)(?:[/?#]|$)/.test(next);
            router.replace(safe ? next! : user.role !== "teacher" && user.profile_completed === false ? "/profile" : homeFor(user.role));
        }
        catch (error) {
            setError(error instanceof Error ? error.message : "Could not sign in.");
        }
        finally {
            setBusy(false);
            lock.current = false;
        }
    }
    return <div className="soven-auth-page"><header className="soven-public-nav"><Brand /><Link href="/signup">New here? <strong>Create an account</strong></Link></header><main className="soven-auth-grid"><aside className="soven-auth-art"><div><p className="soven-eyebrow">GOOD TO HAVE YOU BACK</p><h2>There’s always<br />another chapter.</h2><p>Pick up where your curiosity left off.</p></div><Image src="/illustrations/reading-nook.webp" alt="A quiet reading nook with a reader and a cat" width={960} height={640}/></aside><section className="soven-form-card"><p className="soven-eyebrow">YOUR READING SPACE</p><h1>Welcome back!</h1><p className="soven-muted">Sign in to continue your reading journey.</p><form onSubmit={submit} className="soven-form"><label>Username<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required placeholder="your username"/></label><label>Password<input autoComplete="current-password" type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="Your password"/></label>{error && <p role="alert" className="soven-error">{error}</p>}<button type="submit" className="soven-button" disabled={busy}>{busy ? "Signing in…" : "Sign In"}<ArrowRight size={17}/></button></form><p className="soven-fine">Classroom readers need their teacher’s approval first.</p><Link href="/signup" className="soven-text-link">Create your reading account <ArrowRight size={15}/></Link></section></main></div>;
}
export default function Login() { return <Suspense fallback={<div className="soven-loading" role="status">Opening sign in…</div>}><LoginForm /></Suspense>; }
