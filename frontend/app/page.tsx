import Image from "next/image";
import Link from "next/link";
import { ArrowRight, BookOpen, Headphones, Mic, ShieldCheck, Sparkles } from "lucide-react";
import Brand from "@/components/soven/Brand";
export default function Landing() {
    return <div className="soven-landing">
    <header className="soven-public-nav"><Brand /><nav aria-label="Main navigation"><a href="#how-it-works">How it works</a><a href="#languages">Languages</a><Link href="/login">Sign in</Link></nav><Link className="soven-button soven-button-small" href="/signup">Start reading <ArrowRight size={16}/></Link></header>
    <main>
      <section className="soven-hero">
        <div className="soven-hero-copy"><span className="soven-kicker"><Sparkles size={15}/> A little practice. A world of stories.</span>
          <h1>Better reading.<br /><span>Brighter possibilities.</span></h1>
          <p>A place to find your reading voice. Explore stories, read aloud, and take the next small step with thoughtful word feedback.</p>
          <div className="soven-hero-actions"><Link className="soven-button" href="/try">Try your microphone <ArrowRight size={18}/></Link><Link className="soven-text-link" href="/signup">Find your next story</Link></div>
          <p className="soven-fine"><ShieldCheck size={15}/> No account needed for the microphone check.</p>
          <div className="soven-hero-languages"><span>English</span><span lang="ur" className="font-urdu">اردو</span><span>More languages on the way</span></div>
        </div>
        <div className="soven-hero-art"><Image src="/illustrations/reading-nook.webp" alt="A reader in a sunny reading nook, sharing a quiet moment with a book and a sleeping cat" fill priority sizes="(max-width: 800px) 100vw, 58vw"/><div className="soven-art-note">Your voice.<br />Your own pace.<span>Every page is a new beginning.</span></div></div>
      </section>
      <section id="how-it-works" className="soven-how"><div><p className="soven-eyebrow">MAKE ROOM FOR A LITTLE READING</p><h2>Small steps.<br />Stories worth coming back to.</h2><p>You bring your curiosity. We give you a quiet space to practise.</p></div><div className="soven-steps">{[
            { icon: BookOpen, title: "Find a story", copy: "Choose a short illustrated book in English or Urdu." },
            { icon: Mic, title: "Give the words a voice", copy: "Read a sentence aloud. Pause, listen or try again at your pace." },
            { icon: Headphones, title: "Notice. Practise. Grow.", copy: "Compare the recognized words with the page and choose what to practise next." },
        ].map(({ icon: Icon, title, copy }, i) => <article key={title}><span className="soven-step-icon"><Icon size={23}/></span><div><span className="soven-eyebrow">0{i + 1}</span><h3>{title}</h3><p>{copy}</p></div></article>)}</div></section>
      <section id="languages" className="soven-language-banner"><div><p className="soven-eyebrow">DIFFERENT LANGUAGES. THE SAME CURIOSITY.</p><h2>A growing world of reading.</h2><p>Start with English and Urdu today. We’re building toward 70+ languages, one carefully checked reading experience at a time.</p></div><div className="soven-language-tags"><span>English <small>Read today</small></span><span className="font-urdu" lang="ur">اردو <small className="font-sans">Read today</small></span><span>Español <small>In development</small></span><span>70+ <small>Our goal</small></span></div></section>
      <section className="soven-last-call"><BookOpen size={30}/><h2>Your next chapter starts here.</h2><p>Independent readers can create an account. Classroom readers join with their teacher’s code.</p><Link href="/signup" className="soven-button">Let’s begin <ArrowRight size={18}/></Link></section>
    </main>
    <footer className="soven-footer"><Brand /><p>Made for reading, at your own pace.</p><Link href="/privacy">How your data is used</Link><Link href="/login">Teacher sign in</Link><a href="https://github.com/TeamXOF/soven">TeamXOF</a></footer>
  </div>;
}
