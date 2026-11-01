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
    const art = bookArt(story.id);
    return <article className="soven-book-card">
    <div className="soven-book-cover"><Image src={art.image} alt="" fill sizes="(max-width: 700px) 90vw, 380px"/>
      <span className="soven-book-badge">{ur ? "مختصر کہانی" : "A little adventure"}</span>
    </div>
    <div className="soven-book-copy">
      <p className="soven-eyebrow">{story.total_checkpoints} {ur ? "صفحات" : "reading pages"}</p>
      <h2 className={ur ? "font-urdu" : ""} dir={ur ? "rtl" : "ltr"}>{ur ? story.title_ur : story.title}</h2>
      <p dir={ur ? "rtl" : "ltr"}>{ur ? art.ur : art.description}</p>
      <div className="soven-book-footer"><span>{story.passed_checkpoints}/{story.total_checkpoints} {ur ? "مکمل" : "pages passed"}</span>
        {story.locked ? <span className="soven-locked"><Lock size={14}/>{ur ? "پہلی کہانی مکمل کریں" : "Finish the previous book"}</span>
            : <Link className="soven-button soven-button-small" href={`/book/${story.id}?lang=${language}`}>{ur ? "پڑھیں" : story.status === "in_progress" ? "Continue" : "Read book"}<ArrowUpRight size={16}/></Link>}
      </div>
    </div>
  </article>;
}
