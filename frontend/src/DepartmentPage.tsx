import { useEffect, useState } from "react";
import type { DepartmentDetail, Lang } from "./types";
import { BlockRenderer } from "./blocks/BlockRenderer";
import { StaffGrid } from "./components/StaffGrid";

const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

export function DepartmentPage({ slug }: { slug: string }) {
  const [dept, setDept] = useState<DepartmentDetail | null>(null);
  const [lang, setLang] = useState<Lang>("uz");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/departments/${slug}/`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then(setDept)
      .catch((e) => setError(String(e)));
  }, [slug]);

  if (error) return <p className="p-8 text-red-600">Xatolik: {error}</p>;
  if (!dept) return <p className="p-8 text-foreground-500">Yuklanmoqda...</p>;

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

      <div className="page-card mb-8 flex items-center gap-4 p-5">
        {dept.logo && (
          <img
            src={dept.logo.file.startsWith("http") ? dept.logo.file : `http://127.0.0.1:8000${dept.logo.file}`}
            alt=""
            className="h-16 w-16 object-contain"
          />
        )}
        <h1 className="font-display text-2xl font-extrabold tracking-tight text-primary-900 text-balance">
          {dept.name[lang]}
        </h1>
      </div>

      <div className="space-y-5">
        {dept.page.blocks
          .slice()
          .sort((a, b) => a.order - b.order)
          .map((block) => (
            <BlockRenderer key={block.id} block={block} lang={lang} />
          ))}
      </div>

      {dept.staff.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 font-display text-xl font-bold text-primary-900">
            {lang === "uz" ? "Xodimlar" : lang === "ru" ? "Сотрудники" : "Staff"}
          </h2>
          <StaffGrid staff={dept.staff} lang={lang} />
        </div>
      )}
    </div>
  );
}
