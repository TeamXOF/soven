"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { ArrowRight, BookOpen, CheckCircle2, Mic, Star, Target } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { fetchStudentDashboard, fetchStories, type StudentDashboard, type StorySummary } from "@/lib/api";
import OfflineNotice from "@/components/soven/OfflineNotice";
import { bookArt } from "@/lib/book-art";
export default function ReaderOverview({ progress = false }: {
    progress?: boolean;
}) {
    const { user } = useAuth();
    const { language } = useSpeakFlow();
    const [data, setData] = useState<StudentDashboard | null>(null);
    const [books, setBooks] = useState<StorySummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [reload, setReload] = useState(0);
    const ur = language === "ur";
    useDeferredEffect(() => {
        let active = true;
        if (!user?.student_id)
            return;
        setLoading(true);
        setError("");
        Promise.all([fetchStudentDashboard(user.student_id), fetchStories(user.student_id, language)]).then(([dashboard, stories]) => {
            if (active) {
                setData(dashboard);
                setBooks(stories);
            }
        }).catch(e => {
            if (active)
                setError(e.message);
        }).finally(() => {
            if (active)
                setLoading(false);
        });
        return () => { active = false; };
    }, [user?.id, user?.student_id, language, reload]);
    const summary = data?.summary;
    const history = data?.recent_sessions ?? [];
    const readings = history.filter(r => r.language === language && r.avg_accuracy !== null).slice(0, 10).reverse();
    const next = books.find(b => !b.locked && b.status === "in_progress") ?? books.find(b => !b.locked && b.status !== "completed") ?? books[0];
    const continuing = next ? history.find(r => r.story_id === next.id && r.language === language && r.kind === "story" && !r.completed_at) : undefined;
    const href = next ? `/book/${next.id}?lang=${language}${continuing ? `&session=${encodeURIComponent(continuing.id)}` : ""}` : "/books";
    return <div className="soven-content"><OfflineNotice /><div className="soven-page-heading"><div><p className="soven-eyebrow">{ur ? "ہر صفحہ ایک نئی شروعات" : "EVERY PAGE IS A NEW BEGINNING"}</p><h1>{progress ? (ur ? "میری پیش رفت" : "My Progress") : (ur ? `خوش آمدید، ${user?.name.split(" ")[0] ?? ""}` : `Hello, ${user?.name.split(" ")[0] ?? "reader"}. A little reading today?`)}</h1><p>{progress ? (ur ? "آپ کی اصل ریکارڈنگ اور مشق کا خلاصہ۔" : "Your actual readings, small steps and words to revisit.") : (ur ? "اپنی رفتار سے پڑھیں۔ ہر کوشش اہم ہے۔" : "Pick up a story, find a quiet moment, and make it your own.")}</p></div><Link href="/books" className="soven-text-link">{ur ? "تمام کتابیں" : "Your bookshelf"}<ArrowRight size={15}/></Link></div>
  {!progress && <section className="soven-welcome"><div className="soven-welcome-copy"><span className="soven-kicker"><BookOpen size={15}/>{ur ? "آپ کی اگلی کہانی" : "YOUR NEXT CHAPTER"}</span><h2>{ur ? "پڑھیں، سنیں،\nپھر کوشش کریں۔" : "A step closer to\na story you’ll love."}</h2><p>{ur ? "کوئی جلدی نہیں۔ ایک صفحے سے شروع کریں۔" : "No rush. No race. Just you, a good story, and a little help along the way."}</p><Link href={href} className="soven-button soven-button-small">{ur ? "پڑھنا شروع کریں" : continuing ? "Continue reading" : "Start reading"}<ArrowRight size={16}/></Link></div><div className="soven-welcome-art"><Image src="/illustrations/reading-nook.webp" alt="A reader discovering a story" fill priority sizes="(max-width: 600px) 50vw, 550px"/></div></section>}
  {error && <div className="soven-error mt-5" role="alert">{error} <button className="underline" onClick={() => setReload(n => n + 1)}>Try again</button></div>}
  {loading ? <div className="soven-stats" role="status" aria-label="Loading reading history">{[1, 2, 3, 4].map(i => <div key={i} className="soven-skeleton"/>)}</div> : !error && <div className="soven-stats">{[
                { icon: BookOpen, label: ur ? "مکمل صفحات" : "Pages passed", value: summary?.checkpoints_passed ?? 0, hint: ur ? "تمام زبانوں میں" : "Across all reading languages" },
                { icon: Target, label: ur ? "الفاظ کی مطابقت" : "Average word match", value: summary?.avg_accuracy == null ? "—" : `${Math.round(summary.avg_accuracy)}%`, hint: ur ? "شناخت شدہ الفاظ کا موازنہ" : "Recognized words versus target text" },
                { icon: Mic, label: ur ? "پڑھنے کی نشستیں" : "Reading sessions", value: (summary?.classic_sessions ?? 0) + (summary?.story_sessions ?? 0), hint: ur ? "آپ کی محفوظ کوششیں" : "Your saved reading sessions" },
                { icon: Star, label: ur ? "حاصل کردہ ستارے" : "Stars earned", value: summary?.stars ?? 0, hint: ur ? "اصل محفوظ نتائج" : "From your recorded results" },
            ].map(({ icon: Icon, label, value, hint }) => <article className="soven-stat" key={label}><span className="soven-stat-icon"><Icon size={19}/></span><div><p>{label}</p><strong>{value}</strong><small>{hint}</small></div></article>)}</div>}
  <div className="soven-two-column"><section className="soven-panel"><div className="soven-panel-header"><div><h2>{ur ? "آپ کی حالیہ ریڈنگ" : "Your recent readings"}</h2><p className="soven-muted">{language === "ur" ? "اردو" : "English"} · {ur ? "الفاظ کی مطابقت" : "Word match"}</p></div><Link href="/my-progress">{ur ? "پیش رفت" : "View progress"} ↗</Link></div>{readings.length < 2 ? <div className="soven-empty"><BookOpen size={28}/><h2>{readings.length ? "Your first step is on the page." : "Your story starts with a page."}</h2><p>{readings.length ? "Read again in this language to see your recent results together." : "Complete a reading to see your own results here."}</p><Link href={href} className="soven-text-link">{ur ? "پڑھیں" : "Find a story"}<ArrowRight size={15}/></Link></div> : <><div className="soven-chart"><svg viewBox="0 0 600 245" role="img" aria-label={`Recent ${language === "ur" ? "Urdu" : "English"} word match percentages by reading, oldest first`} width="100%" height="100%">{[0, 25, 50, 75, 100].map(v => <g key={v}><line x1="42" x2="570" y1={210 - v * 1.7} y2={210 - v * 1.7} stroke="#e8e6e0" strokeDasharray="3 5"/><text x="6" y={215 - v * 1.7} fontSize="11" fill="#71808b">{v}%</text></g>)}<polyline fill="none" stroke="#e84e32" strokeWidth="3" strokeLinejoin="round" points={readings.map((r, i) => `${48 + i * 510 / (readings.length - 1)},${210 - Math.max(0, Math.min(100, r.avg_accuracy!)) * 1.7}`).join(" ")}/>{readings.map((r, i) => <g key={r.id}><circle cx={48 + i * 510 / (readings.length - 1)} cy={210 - Math.max(0, Math.min(100, r.avg_accuracy!)) * 1.7} r="5" fill="white" stroke="#e84e32" strokeWidth="2"/><text x={48 + i * 510 / (readings.length - 1)} y="235" textAnchor="middle" fontSize="11" fill="#71808b">{i + 1}</text></g>)}</svg></div><p className="soven-chart-caption">{ur ? "افقی محور: پرانی سے نئی ریڈنگ۔ مختلف جملوں کے نتائج سیکھنے میں بہتری کا ثبوت نہیں۔" : "Reading number, oldest to newest. Different passages can have different difficulty; this chart does not measure a learning gain."}</p></>}</section>
  <section className="soven-panel"><div className="soven-panel-header"><h2>{ur ? "دوبارہ دیکھنے والے الفاظ" : "A little focus goes a long way"}</h2><Link href="/practice">{ur ? "مشق" : "Practice"} ↗</Link></div><p className="soven-muted">{ur ? "آپ کی محفوظ ریڈنگ میں نشان زدہ الفاظ، تمام زبانوں میں۔" : "Words flagged in your saved readings, across all languages. Recognition can make mistakes too."}</p>{data?.struggling_words.length ? <div className="soven-word-tags">{data.struggling_words.slice(0, 10).map(w => <Link key={w.word} href="/practice" dir="auto">{w.word}<span className="ml-2 opacity-60 text-xs">{w.count}</span></Link>)}</div> : <div className="soven-empty"><CheckCircle2 size={26}/><p>{ur ? "ابھی کوئی نشان زدہ لفظ نہیں۔ پڑھنے کے بعد یہاں دیکھیں۔" : "No flagged words to show yet. Read a page and come back here."}</p></div>}<div className="soven-note">{ur ? "الفاظ کی مطابقت، آواز سے شناخت شدہ متن کا موازنہ ہے۔" : "Word match compares recognized text with the page. It is not a pronunciation diagnosis."}</div></section></div>
  <div className="soven-two-column"><section className="soven-panel"><div className="soven-panel-header"><h2>{ur ? "آپ کی کتاب" : "A book for your next quiet moment"}</h2><Link href="/books">{ur ? "تمام کتابیں" : "View all"} ↗</Link></div>{next ? <div className="flex gap-5 items-center"><Image src={bookArt(next.id).image} alt="" width={110} height={140} className="rounded-xl object-cover h-40 w-28"/><div><h3 className={`text-lg font-bold ${ur ? "font-urdu" : ""}`}>{ur ? next.title_ur : next.title}</h3><p className="soven-muted mt-2">{ur ? bookArt(next.id).ur : bookArt(next.id).description}</p><div className="soven-progress-bar"><span style={{ width: `${next.passed_checkpoints / next.total_checkpoints * 100}%` }}/></div><Link href={href} className="soven-text-link">{ur ? "جاری رکھیں" : "Open book"}<ArrowRight size={15}/></Link></div></div> : <p className="soven-muted">Your books will appear when the server is reachable.</p>}</section><section className="soven-panel"><h2>{ur ? "حالیہ سرگرمی" : "Little moments of reading"}</h2>{history.length ? <ul className="soven-history-list">{history.slice(0, 4).map(r => <li key={r.id}><span className="soven-stat-icon"><BookOpen size={16}/></span><div><p>{r.label}</p><small>{r.language.toUpperCase()} · {new Date(r.created_at.replace(" ", "T") + (!r.created_at.includes("Z") && !r.created_at.includes("+") ? "Z" : "")).toLocaleDateString()}</small></div><strong>{r.avg_accuracy == null ? "—" : `${Math.round(r.avg_accuracy)}%`}</strong></li>)}</ul> : <div className="soven-empty"><p>{ur ? "آپ کی پہلی ریڈنگ یہاں نظر آئے گی۔" : "Your first reading will show up here."}</p></div>}</section></div>
  </div>;
}
