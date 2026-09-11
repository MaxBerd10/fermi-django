import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { FacultyListItem, Lang, Paginated } from "../types";

const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "O'zbekcha" },
  { code: "ru", label: "Русский" },
  { code: "en", label: "English" },
];

export function FacultyListPage() {
  const [items, setItems] = useState<FacultyListItem[] | null>(null);
  const [lang, setLang] = useState<Lang>("uz");

  useEffect(() => {
    fetch("/api/v1/faculties/")
      .then((res) => res.json())
      .then((data: Paginated<FacultyListItem>) => setItems(data.results));
  }, []);

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

      <h1 className="mb-6 font-display text-2xl font-extrabold text-primary-900">
        {lang === "uz" ? "Fakultetlar" : lang === "ru" ? "Факультеты" : "Faculties"}
      </h1>

      {items === null ? (
        <p className="text-foreground-500">Yuklanmoqda...</p>
      ) : items.length === 0 ? (
        <p className="text-foreground-500">Hozircha fakultetlar yo'q.</p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/fakultetlar/${item.slug}`}
              className="page-card block p-5 font-display text-lg font-bold text-primary-900 hover:border-primary-200"
            >
              {item.name[lang]}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
