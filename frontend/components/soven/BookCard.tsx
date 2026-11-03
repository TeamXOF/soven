import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Lock } from "lucide-react";
import type { StorySummary } from "@/lib/api";
import type { ReadingLanguage } from "@/lib/languages";
import { bookArt } from "@/lib/book-art";
export default function BookCard({ story, language }: {
    story: StorySummary;
    language: ReadingLanguage;
}) {
    const ur = language === "ur";
    const es = language === "es";
    const art = bookArt(story.id);
    const title = ur ? story.title_ur : es ? (story.title_es || story.title) : story.title;
    const desc = ur ? art.ur : es ? art.es : art.description;
    const badge = ur ? "مختصر کہانی" : es ? "Una pequeña aventura" : "A little adventure";
    return <article className="soven-book-card">
    <div className="soven-book-cover"><Image src={art.image} alt="" fill sizes="(max-width: 700px) 90vw, 380px"/>
      <span className="soven-book-badge">{badge}</span>
    </div>
    <div className="soven-book-copy">
      <p className="soven-eyebrow">{story.total_checkpoints} {ur ? "صفحات" : es ? "páginas de lectura" : "reading pages"}</p>
      <h2 className={ur ? "font-urdu" : ""} dir={ur ? "rtl" : "ltr"}>{title}</h2>
      <p dir={ur ? "rtl" : "ltr"}>{desc}</p>
      <div className="soven-book-footer"><span>{story.passed_checkpoints}/{story.total_checkpoints} {ur ? "مکمل" : es ? "páginas completadas" : "pages passed"}</span>
        {story.locked ? <span className="soven-locked"><Lock size={14}/>{ur ? "پہلی کہانی مکمل کریں" : es ? "Termina el libro anterior" : "Finish the previous book"}</span>
            : <Link className="soven-button soven-button-small" href={`/book/${story.id}?lang=${language}`}>{ur ? "پڑھیں" : es ? (story.status === "in_progress" ? "Continuar" : "Leer libro") : story.status === "in_progress" ? "Continue" : "Read book"}<ArrowUpRight size={16}/></Link>}
      </div>
    </div>
  </article>;
}
