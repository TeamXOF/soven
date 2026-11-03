"use client";
import { useDeferredEffect } from "@/hooks/useDeferredEffect";
import { useState } from "react";
import Link from "next/link";
import { Search, BookOpen } from "lucide-react";
import { useAuth } from "@/components/auth/AuthProvider";
import { useSpeakFlow } from "@/context/SpeakFlowContext";
import { fetchStories, type StorySummary } from "@/lib/api";
import BookCard from "@/components/soven/BookCard";
import OfflineNotice from "@/components/soven/OfflineNotice";

export default function Books() {
    const { user } = useAuth();
    const { language, setLanguage, controlsLocked } = useSpeakFlow();
    const [stories, setStories] = useState<StorySummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [query, setQuery] = useState("");
    const [reload, setReload] = useState(0);
    const ur = language === "ur";
    const es = language === "es";

    useDeferredEffect(() => {
        let active = true;
        if (!user?.student_id)
            return;
        setLoading(true);
        setError("");
        fetchStories(user.student_id, language).then(data => {
            if (active)
                setStories(data);
        }).catch(e => {
            if (active)
                setError(e.message);
        }).finally(() => {
            if (active)
                setLoading(false);
        });
        return () => { active = false; };
    }, [user?.id, user?.student_id, language, reload]);

    const visible = stories.filter(s => (s.title + " " + s.title_ur + (s.title_es ? " " + s.title_es : "")).toLocaleLowerCase().includes(query.toLocaleLowerCase()));

    return <div className="soven-content"><OfflineNotice />
      <div className="soven-page-heading">
        <div>
          <p className="soven-eyebrow">{ur ? "ایک نئی دنیا منتظر ہے" : es ? "HAY TODO UN MUNDO AQUÍ DENTRO" : "THERE’S A WHOLE WORLD IN HERE"}</p>
          <h1>{ur ? "میری کتابیں" : es ? "Mis Libros" : "My Books"}</h1>
          <p>{ur ? "کتاب چنیں اور اپنی رفتار سے پڑھیں۔" : es ? "Encuentra tu próxima pequeña aventura. Lee una página a tu propio ritmo." : "Find your next little adventure. Read a page at your own pace."}</p>
        </div>
        <Link className="soven-text-link" href="/read">{ur ? "سطحوں کا سفر" : es ? "Explorar niveles" : "Explore reading levels"} ↗</Link>
      </div>
      <div className="soven-library-toolbar">
        <label className="soven-search"><Search size={17}/>
          <input aria-label="Search books" placeholder={ur ? "کتاب تلاش کریں…" : es ? "Buscar libros…" : "Search your bookshelf…"} value={query} onChange={e => setQuery(e.target.value)}/>
        </label>
        <div className="soven-language-switch" role="group" aria-label="Book language">
          <button disabled={controlsLocked} aria-pressed={language === "en"} onClick={() => setLanguage("en")}>English</button>
          <button disabled={controlsLocked} aria-pressed={language === "ur"} onClick={() => setLanguage("ur")} lang="ur">اردو</button>
          <button disabled={controlsLocked} aria-pressed={language === "es"} onClick={() => setLanguage("es")} lang="es">Español</button>
          <Link className="px-3 py-2 text-xs self-center text-text-secondary" href="/languages">More languages</Link>
        </div>
      </div>
      {error ? <div className="soven-error" role="alert">{error} <button onClick={() => setReload(n => n + 1)} className="underline">Try again</button></div> : loading ? <div className="soven-books-grid" role="status" aria-label="Loading books">{[1, 2, 3].map(i => <div className="soven-skeleton h-96" key={i}/>)}</div> : visible.length ? <div className="soven-books-grid">{visible.map(story => <BookCard key={story.id} story={story} language={language}/>)}</div> : <div className="soven-panel soven-empty"><BookOpen /><h2>{ur ? "کوئی کتاب نہیں ملی" : es ? "No se encontraron libros" : "No books found"}</h2><p>{es ? "Prueba con otra búsqueda. Los libros disponibles aparecerán aquí cuando el servidor esté accesible." : "Try a different search. Available books appear here when the server is reachable."}</p></div>}
      <p className="soven-chart-caption">{ur ? "اگلی کتاب کھولنے کے لیے پچھلی کتاب کے صفحات مکمل کریں۔" : es ? "Completa las páginas de un libro para desbloquear el siguiente. El progreso se guarda por idioma." : "Pass the pages in one book to unlock the next. Progress is tracked separately for each reading language."}</p>
    </div>;
}
