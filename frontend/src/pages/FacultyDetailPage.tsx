import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import type { FacultyDetail } from "../types";
import { BlockRenderer } from "../blocks/BlockRenderer";
import { StaffGrid } from "../components/StaffGrid";
import { useLanguage } from "../i18n/LanguageContext";

export function FacultyDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [faculty, setFaculty] = useState<FacultyDetail | null>(null);
  const { lang } = useLanguage();
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
              <Link
                key={dept.id}
                to={`/kafedralar/${dept.slug}`}
                className="page-card block p-4 font-semibold text-primary-900 hover:border-primary-200"
              >
                {dept.name_uz}
              </Link>
            ))}
          </div>
        </div>
      )}

      {faculty.leaders.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 font-display text-xl font-bold text-primary-900">
            {lang === "uz" ? "Rahbariyat" : lang === "ru" ? "Руководство" : "Leadership"}
          </h2>
          <StaffGrid staff={faculty.leaders} lang={lang} />
        </div>
      )}
    </div>
  );
}
