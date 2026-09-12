import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { FacultyListItem, Paginated } from "../types";
import { useLanguage } from "../i18n/LanguageContext";

export function FacultyListPage() {
  const [items, setItems] = useState<FacultyListItem[] | null>(null);
  const { lang } = useLanguage();

  useEffect(() => {
    fetch("/api/v1/faculties/")
      .then((res) => res.json())
      .then((data: Paginated<FacultyListItem>) => setItems(data.results));
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
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
