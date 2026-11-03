import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BookOpen, Headphones, Mic, ShieldCheck, Sparkles, UserCheck } from "lucide-react";
import Brand from "@/components/soven/Brand";

export default function Landing() {
  return (
    <div className="soven-landing">
      <header className="soven-public-nav">
        <Brand />
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#languages">Languages</a>
          <Link href="/login">Sign in</Link>
        </nav>
        <Link className="soven-button soven-button-small" href="/onboarding/test">
          Start reading <ArrowRight size={16}/>
        </Link>
      </header>

      <main>
        <section className="soven-hero">
          <div className="soven-hero-copy">
            <span className="soven-kicker">
              <Sparkles size={15}/> Empowering Every Reader with Meta AI
            </span>
            <h1>Better reading.<br /><span>Brighter possibilities.</span></h1>
            <p>
              Over 700 million children and adults struggle with reading barriers and dyslexia.
              Soven eliminates reading anxiety with kind, acoustic AI coaching, dyslexia-friendly
              pacing waivers, and interactive 2D open-book stories in English, Urdu, and Spanish.
            </p>
            <div className="soven-hero-actions">
              <Link className="soven-button" href="/onboarding/test">
                Start 20s Voice Test <ArrowRight size={18}/>
              </Link>
              <Link className="soven-text-link" href="/signup">
                Direct Sign Up
              </Link>
            </div>
            <p className="soven-fine">
              <ShieldCheck size={15}/> Privacy Shield: No account or storage needed for the 20s voice diagnostic.
            </p>
            <div className="soven-hero-languages">
              <span>English</span>
              <span lang="ur" className="font-urdu">اردو</span>
              <span>Español</span>
              <span>70+ Candidate Languages</span>
            </div>
          </div>
          <div className="soven-hero-art">
            <Image
              src="/illustrations/reading-nook.webp"
              alt="A reader in a sunny reading nook, sharing a quiet moment with a book and a sleeping cat"
              fill
              priority
              sizes="(max-width: 800px) 100vw, 58vw"
            />
            <div className="soven-art-note">
              Your voice.<br />Your own pace.
              <span>Every page is a new beginning.</span>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="soven-how">
          <div>
            <p className="soven-eyebrow">YOUR 3-STEP JOURNEY TO FLUENCY</p>
            <h2>Small steps.<br />Stories worth coming back to.</h2>
            <p>A quiet, neurodiversity-affirming space powered by Meta AI open weights.</p>
          </div>
          <div className="soven-steps">
            {[
              {
                icon: Mic,
                title: "1. 20s Voice Test",
                copy: "Record a short 20-second reading sample to assess baseline WCPM fluency, pause gaps, and pitch stability without signing up."
              },
              {
                icon: UserCheck,
                title: "2. Pick Reader Mode",
                copy: "Select Child, Dyslexia Friendly (wide spacing, cream tint, waived speed penalties), or Adult Reader persona."
              },
              {
                icon: BookOpen,
                title: "3. Read in 2D AI Book",
                copy: "Open a story with warm center-spine pages, tap words for instant pronunciation, and receive conversational Meta AI voice coaching."
              },
            ].map(({ icon: Icon, title, copy }, i) => (
              <article key={title}>
                <span className="soven-step-icon"><Icon size={23}/></span>
                <div>
                  <span className="soven-eyebrow">0{i + 1}</span>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="languages" className="soven-language-banner">
          <div>
            <p className="soven-eyebrow">DIFFERENT LANGUAGES. THE SAME CURIOSITY.</p>
            <h2>A growing world of reading.</h2>
            <p>Start with English, Urdu and Spanish today. We’re building toward 70+ languages, one carefully checked reading experience at a time.</p>
          </div>
          <div className="soven-language-tags">
            <span>English <small>Read today</small></span>
            <span className="font-urdu" lang="ur">اردو <small className="font-sans">Read today</small></span>
            <span>Español <small>Read today</small></span>
            <span>70+ <small>Our goal</small></span>
          </div>
        </section>

        <section className="soven-last-call">
          <BookOpen size={30}/>
          <h2>Your next chapter starts here.</h2>
          <p>Take the 20-second pre-signup voice test or create your reading space now.</p>
          <Link href="/onboarding/test" className="soven-button">
            Try 20s Voice Test <ArrowRight size={18}/>
          </Link>
        </section>
      </main>

      <footer className="soven-footer">
        <Brand />
        <p>Made for reading, at your own pace. Powered by Meta AI.</p>
        <Link href="/privacy">How your data is used</Link>
        <Link href="/login">Teacher sign in</Link>
        <a href="https://github.com/TeamXOF/soven">TeamXOF / Soven</a>
      </footer>
    </div>
  );
}
