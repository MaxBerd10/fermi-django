import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { FacultyDetail, Lang } from "../types";
import { BlockRenderer } from "../blocks/BlockRenderer";

const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

export function FacultyDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [faculty, setFaculty] = useState<FacultyDetail | null>(null);
  const [lang, setLang] = useState<Lang>("uz");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/faculties/${slug}/`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then(setFaculty)
      .catch((e) => setError(String(e)));
  }, [slug]);

  if (error) return <p className="p-8 text-red-600">Xatolik: {error}</p>;
  if (!faculty) return <p className="p-8 text-foreground-500">Yuklanmoqda...</p>;

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <div className="mb-6 flex gap-2">
        {LANGS.map((l) => (
          <button
            key={l.code}
            onClick={() => setLang(l.code)}
            className={`rounded-full px-3.5 py-1.5 text-sm font-semibold transition-colors ${
              lang === l.code ? "bg-primary-900 text-white" : "bg-primary-50 text-primary-700 hover:bg-primary-100"
            }`}
          >
            {l.label}
          </button>
        ))}
      </div>

      <h1 className="mb-6 font-display text-2xl font-extrabold tracking-tight text-primary-900 text-balance">
        {faculty.name[lang]}
      </h1>

      <div className="space-y-5">
        {faculty.page.blocks
          .slice()
          .sort((a, b) => a.order - b.order)
          .map((block) => (
            <BlockRenderer key={block.id} block={block} lang={lang} />
          ))}
      </div>

      {faculty.departments.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 font-display text-xl font-bold text-primary-900">
            {lang === "uz" ? "Kafedralar" : lang === "ru" ? "Кафедры" : "Departments"}
          </h2>
          <div className="space-y-2">
            {faculty.departments.map((dept) => (
              <Link key={dept.id} to="/" className="page-card block p-4 font-semibold text-primary-900 hover:border-primary-200">
                {dept.name_uz}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
