"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import Image from "next/image";
import Link from "next/link";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, ShieldCheck } from "lucide-react";
import Brand from "@/components/soven/Brand";
import { useAuth } from "@/components/auth/AuthProvider";
import { fetchReaderProfile, getStoredToken, saveReaderProfile, type ReaderProfile } from "@/lib/api";
import { isLanguageCode, LANGUAGE_CATALOG, type LanguageCode, type ReadingLanguage } from "@/lib/languages";
import { loadPrefs } from "@/lib/prefs";
export default function ProfilePage() {
    const { user, loading, setProfile } = useAuth();
    const userId = user?.id;
    const router = useRouter();
    const [profile, edit] = useState<ReaderProfile | null>(null);
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);
    const [saved, setSaved] = useState(false);
    const guard = useRef(false);
    const mounted = useRef(true);
    useDeferredEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
    useDeferredEffect(() => {
        if (!loading && !user)
            router.replace("/login?next=/profile");
    }, [user, loading, router]);
    useDeferredEffect(() => {
        if (!userId)
            return;
        const controller = new AbortController();
        const token = getStoredToken();
        setError("");
        fetchReaderProfile(controller.signal).then(({ profile: p }) => {
            if (controller.signal.aborted || getStoredToken() !== token)
                return;
            const local = loadPrefs();
            edit(p.version === 1 && !p.native_language ? { ...p, reading_language: local.storyLanguage, accessibility: { ...p.accessibility, larger_text: local.biggerText, word_tips: local.wordTips } } : p);
        }).catch(e => {
            if (!controller.signal.aborted)
                setError(e.message || "Could not load your profile.");
        });
        return () => controller.abort();
    }, [userId]);
    const ur = profile?.interface_language === "ur";
    async function submit(event: React.FormEvent) {
        event.preventDefault();
        if (!profile || guard.current)
            return;
        guard.current = true;
        setBusy(true);
        setError("");
        setSaved(false);
        const token = getStoredToken();
        try {
            const result = await saveReaderProfile({ expected_version: profile.version, reading_language: profile.reading_language, interface_language: profile.interface_language, native_language: profile.native_language, translation_language: profile.translation_language, accessibility: profile.accessibility, complete_profile: true });
            if (!mounted.current || getStoredToken() !== token)
                return;
            setProfile(result.profile);
            edit(result.profile);
            setSaved(true);
            router.push(user?.role === "teacher" ? "/teacher" : "/home");
        }
        catch (e) {
            if (mounted.current && getStoredToken() === token)
                setError(e instanceof Error ? e.message : "Could not save. Please try again.");
        }
        finally {
            guard.current = false;
            if (mounted.current)
                setBusy(false);
        }
    }
    function lang(value: string): LanguageCode | null { return isLanguageCode(value) ? value : null; }
    return <div className="soven-auth-page"><header className="soven-public-nav"><Brand /><Link href={user?.role === "teacher" ? "/teacher" : "/home"}>{ur ? "واپس" : "Back to your reading space"}</Link></header><main className="soven-profile-layout"><aside className="soven-profile-intro"><span className="soven-profile-badge"><ShieldCheck size={15}/>{ur ? "آپ کا اپنا پڑھنے کا انداز" : "YOUR SPACE. YOUR PACE."}</span><h1>{ur ? "اپنا پروفائل مکمل کریں" : "Make yourself at home."}</h1><p className="soven-muted">{ur ? "اپنی زبانیں اور پڑھنے کا انداز منتخب کریں۔ آپ بعد میں بھی بدل سکتے ہیں۔" : "Choose your languages and make reading comfortable for you. You can change these any time."}</p><Image src="/illustrations/reading-nook.webp" alt="" width={960} height={640}/><p className="soven-fine">{ur ? "یہ پڑھنے کی ترجیحات ہیں، طبی جانچ نہیں۔" : "These are reading preferences, not a medical assessment."}</p></aside><section className="soven-form-card">
      {!profile ? <><div className="soven-skeleton"/><p className="soven-muted" role="status">Loading your preferences…</p>{error && <p className="soven-error" role="alert">{error} <button onClick={() => window.location.reload()}>Reload</button></p>}</> : <><p className="soven-eyebrow">{user?.reader_mode === "adult" ? "INDEPENDENT READER" : user?.role === "teacher" ? "TEACHER" : "CLASSROOM READER"}</p><h2 className="text-xl font-bold">{ur ? "آپ کے بارے میں" : "Tell us about yourself"}</h2><p className="soven-muted">{user?.name}</p><form className="soven-form" onSubmit={submit}>
      <div className="soven-form-row"><label>{ur ? "پڑھنے کی زبان" : "Reading language"}<select aria-label="Reading language" value={profile.reading_language} onChange={e => edit({ ...profile, reading_language: e.target.value as ReadingLanguage })}><option value="en">English</option><option value="ur">اردو</option></select><small>Stories, recognition and reading feedback.</small></label><label>{ur ? "مینو کی زبان" : "Interface language"}<select aria-label="Interface language" value={profile.interface_language} onChange={e => edit({ ...profile, interface_language: e.target.value as ReadingLanguage })}><option value="en">English</option><option value="ur">اردو</option></select><small>New navigation and reader controls. Some existing pages use English.</small></label></div>
      <label>{ur ? "آپ کی مادری زبان" : "Your native language"}<select aria-label="Your native language" required value={profile.native_language ?? ""} onChange={e => edit({ ...profile, native_language: lang(e.target.value) })}><option value="">Choose your language</option>{LANGUAGE_CATALOG.map(l => <option value={l.code} key={l.code}>{l.name}</option>)}</select></label>
      <label>{ur ? "ترجمے کی ترجیح (اختیاری)" : "Translation preference (optional)"}<select aria-label="Translation preference" value={profile.translation_language ?? ""} onChange={e => edit({ ...profile, translation_language: lang(e.target.value) })}><option value="">No preference</option>{LANGUAGE_CATALOG.map(l => <option value={l.code} key={l.code}>{l.name}</option>)}</select><small>This saves a future preference. Translation and additional reading languages are still in development.</small></label>
      <fieldset><legend className="text-sm font-bold">{ur ? "آرام سے پڑھیں" : "Make reading comfortable"}</legend><div className="soven-toggles">{([
                ["larger_text", ur ? "بڑے حروف" : "Larger reading text"], ["word_tips", ur ? "الفاظ سننے میں مدد" : "Tap a word to hear it"], ["high_contrast", ur ? "زیادہ واضح رنگ" : "Higher contrast"], ["coach_enabled", ur ? "صفحے کے بعد رہنمائی" : "Guidance after each reading"],
            ] as const).map(([key, label]) => <label className="soven-toggle" key={key}><span>{label}</span><input type="checkbox" checked={profile.accessibility[key]} onChange={e => edit({ ...profile, accessibility: { ...profile.accessibility, [key]: e.target.checked } })}/></label>)}</div><label>{ur ? "سطروں کے درمیان فاصلہ" : "Line spacing"}<select aria-label="Line spacing" value={profile.accessibility.line_spacing} onChange={e => edit({ ...profile, accessibility: { ...profile.accessibility, line_spacing: e.target.value as "normal" | "comfortable" | "wide" } })}><option value="normal">Standard</option><option value="comfortable">Comfortable</option><option value="wide">Extra space</option></select></label></fieldset>
      {error && <p role="alert" className="soven-error">{error} <button type="button" className="underline" onClick={() => window.location.reload()}>Reload latest preferences</button></p>}{saved && <p role="status"><Check size={15}/>Preferences saved.</p>}
      <button type="submit" className="soven-button" disabled={busy}>{busy ? (ur ? "محفوظ ہو رہا ہے…" : "Saving your preferences…") : (ur ? "محفوظ کریں اور جاری رکھیں" : "Save & continue")}<ArrowRight size={17}/></button></form></>}
    </section></main></div>;
}
