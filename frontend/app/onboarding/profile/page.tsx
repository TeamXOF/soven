"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, ShieldCheck, Heart, Sparkles, BookOpen } from "lucide-react";
import Brand from "@/components/soven/Brand";
import { useAuth } from "@/components/auth/AuthProvider";
import { fetchReaderProfile, saveReaderProfile, getStoredToken, type ReaderProfile } from "@/lib/api";
import { LANGUAGE_CATALOG, isLanguageCode, type LanguageCode, type ReadingLanguage } from "@/lib/languages";

export default function OnboardingProfilePage() {
  const { user, loading, setProfile } = useAuth();
  const router = useRouter();
  const [profile, edit] = useState<ReaderProfile | null>(null);
  const [persona, setPersona] = useState<"child" | "dyslexia" | "adult">("child");
  const [initialLevel, setInitialLevel] = useState("Level 2");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login?next=/onboarding/profile");
      return;
    }

    // Read diagnostic result from pre-signup test if available
    const diagnosticStr = localStorage.getItem("soven_diagnostic_result");
    if (diagnosticStr) {
      try {
        const diag = JSON.parse(diagnosticStr);
        if (diag.reading_level) setInitialLevel(diag.reading_level);
        if (diag.language) {
          // prefill target language
        }
      } catch {}
    }

    const controller = new AbortController();
    fetchReaderProfile(controller.signal)
      .then(({ profile: p }) => {
        if (!mounted.current) return;
        edit(p);
        if (p.reader_mode === "dyslexia" || p.reader_mode === "adult") {
          setPersona(p.reader_mode as any);
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(e.message || "Could not load profile.");
      });

    return () => controller.abort();
  }, [user, loading, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!profile || busy) return;
    setBusy(true);
    setError("");

    try {
      // If dyslexia persona, enable larger text and comfortable line spacing automatically
      const accessibility = {
        ...profile.accessibility,
        larger_text: persona === "dyslexia" ? true : profile.accessibility.larger_text,
        line_spacing: persona === "dyslexia" ? "wide" : profile.accessibility.line_spacing,
      };

      const result = await saveReaderProfile({
        expected_version: profile.version,
        reading_language: profile.reading_language,
        interface_language: profile.interface_language,
        native_language: profile.native_language,
        translation_language: profile.translation_language,
        accessibility,
        reader_mode: persona,
        complete_profile: true,
      });

      if (!mounted.current) return;
      setProfile(result.profile);
      edit(result.profile);
      setSaved(true);
      // Clean up pre-signup test
      localStorage.removeItem("soven_diagnostic_result");
      // Redirect to reading space
      router.push("/book/story_forest_01");
    } catch (err: any) {
      if (mounted.current) setError(err?.message || "Could not save profile.");
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  function lang(value: string): LanguageCode | null {
    return isLanguageCode(value) ? value : null;
  }

  const ur = profile?.interface_language === "ur";

  return (
    <div className="soven-auth-page">
      <header className="soven-public-nav">
        <Brand />
        <Link href="/book/story_forest_01">{ur ? "کتاب پر جائیں" : "Go to Books"}</Link>
      </header>

      <main className="soven-profile-layout max-w-4xl mx-auto">
        <aside className="soven-profile-intro">
          <span className="soven-profile-badge">
            <ShieldCheck size={15}/> {ur ? "پروفائل سیٹ اپ" : "STEP 2 OF 3 · READER PERSONA"}
          </span>
          <h1>{ur ? "اپنا ریڈر موڈ منتخب کریں" : "Choose Your Reader Persona"}</h1>
          <p className="soven-muted">
            {ur
              ? "اپنے پڑھنے کا طریقہ چنیں۔ ڈسلیکسیا موڈ میں رفتار کی کٹوتی نہیں کی جاتی۔"
              : "Personalize your journey. Dyslexia mode relaxes pacing and removes speed penalties for slow, accurate reading."}
          </p>
          <div className="relative w-full h-56 rounded-2xl overflow-hidden mt-4">
            <Image src="/illustrations/reading-nook.webp" alt="Reading space" fill className="object-cover" />
          </div>
        </aside>

        <section className="soven-form-card">
          {!profile ? (
            <p className="soven-muted">Loading preferences...</p>
          ) : (
            <form className="soven-form" onSubmit={submit}>
              {/* 3 Reader Personas */}
              <fieldset className="mb-6">
                <legend className="text-sm font-bold mb-3">Select Reader Mode</legend>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div
                    onClick={() => setPersona("child")}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      persona === "child"
                        ? "border-accent-primary bg-accent-primary/10 shadow-sm"
                        : "border-border-card bg-white"
                    }`}
                  >
                    <BookOpen className="text-accent-primary mb-2" size={24}/>
                    <strong className="block text-sm">Child Reader</strong>
                    <span className="text-xs text-text-muted mt-1 block">
                      Playful, encouraging storybook journey for young readers.
                    </span>
                  </div>

                  <div
                    onClick={() => setPersona("dyslexia")}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      persona === "dyslexia"
                        ? "border-emerald-600 bg-emerald-50 shadow-sm"
                        : "border-border-card bg-white"
                    }`}
                  >
                    <Heart className="text-emerald-600 mb-2" size={24}/>
                    <strong className="block text-sm text-emerald-900">Dyslexia Mode</strong>
                    <span className="text-xs text-emerald-700 mt-1 block">
                      Wide line spacing, cream paper, & zero speed penalties.
                    </span>
                  </div>

                  <div
                    onClick={() => setPersona("adult")}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      persona === "adult"
                        ? "border-indigo-600 bg-indigo-50 shadow-sm"
                        : "border-border-card bg-white"
                    }`}
                  >
                    <Sparkles className="text-indigo-600 mb-2" size={24}/>
                    <strong className="block text-sm text-indigo-900">Adult Learner</strong>
                    <span className="text-xs text-indigo-700 mt-1 block">
                      Private, calm self-paced literacy and second-language fluency.
                    </span>
                  </div>
                </div>
              </fieldset>

              {/* Initial Level */}
              <div className="soven-form-row">
                <label>
                  Initial Reading Level
                  <select
                    value={initialLevel}
                    onChange={(e) => setInitialLevel(e.target.value)}
                  >
                    <option value="Level 1">Level 1 (Foundational Phonics)</option>
                    <option value="Level 2">Level 2 (Sentence Pacing & Fluency)</option>
                    <option value="Level 3">Level 3 (Advanced Story Reading)</option>
                  </select>
                </label>

                <label>
                  Reading Language
                  <select
                    value={profile.reading_language}
                    onChange={(e) => edit({ ...profile, reading_language: e.target.value as ReadingLanguage })}
                  >
                    <option value="en">English</option>
                    <option value="ur">اردو (Urdu)</option>
                    <option value="es">Español (Spanish)</option>
                  </select>
                </label>
              </div>

              <div className="soven-form-row">
                <label>
                  Your Native Language
                  <select
                    required
                    value={profile.native_language ?? ""}
                    onChange={(e) => edit({ ...profile, native_language: lang(e.target.value) })}
                  >
                    <option value="">Select your native language</option>
                    {LANGUAGE_CATALOG.map((l) => (
                      <option value={l.code} key={l.code}>{l.name}</option>
                    ))}
                  </select>
                </label>

                <label>
                  Menu Language
                  <select
                    value={profile.interface_language}
                    onChange={(e) => edit({ ...profile, interface_language: e.target.value as ReadingLanguage })}
                  >
                    <option value="en">English</option>
                    <option value="ur">اردو</option>
                  </select>
                </label>
              </div>

              {/* Accessibility */}
              <fieldset className="mt-4">
                <legend className="text-sm font-bold mb-2">Reading Comfort Controls</legend>
                <div className="soven-toggles">
                  <label className="soven-toggle">
                    <span>Larger reading text</span>
                    <input
                      type="checkbox"
                      checked={profile.accessibility.larger_text}
                      onChange={(e) =>
                        edit({
                          ...profile,
                          accessibility: { ...profile.accessibility, larger_text: e.target.checked }
                        })
                      }
                    />
                  </label>
                  <label className="soven-toggle">
                    <span>Tap a word to hear pronunciation</span>
                    <input
                      type="checkbox"
                      checked={profile.accessibility.word_tips}
                      onChange={(e) =>
                        edit({
                          ...profile,
                          accessibility: { ...profile.accessibility, word_tips: e.target.checked }
                        })
                      }
                    />
                  </label>
                  <label className="soven-toggle">
                    <span>Guidance coach after each page</span>
                    <input
                      type="checkbox"
                      checked={profile.accessibility.coach_enabled}
                      onChange={(e) =>
                        edit({
                          ...profile,
                          accessibility: { ...profile.accessibility, coach_enabled: e.target.checked }
                        })
                      }
                    />
                  </label>
                </div>
              </fieldset>

              {error && <p role="alert" className="soven-error mt-4">{error}</p>}
              {saved && <p role="status" className="text-emerald-600 mt-2"><Check size={16} className="inline mr-1"/> Saved!</p>}

              <button type="submit" className="soven-button mt-6 w-full justify-center" disabled={busy}>
                {busy ? "Saving Profile..." : "Complete Profile & Start 2D AI Book"} <ArrowRight size={18}/>
              </button>
            </form>
          )}
        </section>
      </main>
    </div>
  );
}

