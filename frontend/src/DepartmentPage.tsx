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
  if (!dept) return <p className="p-8 text-slate-500">Yuklanmoqda...</p>;

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <div className="mb-6 flex gap-2">
        {LANGS.map((l) => (
          <button
            key={l.code}
            onClick={() => setLang(l.code)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              lang === l.code ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {l.label}
          </button>
        ))}
      </div>

      <div className="mb-8 flex items-center gap-4">
        {dept.logo && (
          <img
            src={dept.logo.file.startsWith("http") ? dept.logo.file : `http://127.0.0.1:8000${dept.logo.file}`}
            alt=""
            className="h-16 w-16 object-contain"
          />
        )}
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 text-balance">{dept.name[lang]}</h1>
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
          <h2 className="mb-4 text-xl font-semibold text-slate-900">
            {lang === "uz" ? "Xodimlar" : lang === "ru" ? "Сотрудники" : "Staff"}
          </h2>
          <StaffGrid staff={dept.staff} lang={lang} />
        </div>
      )}
    </div>
  );
}
