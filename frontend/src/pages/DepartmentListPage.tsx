import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { DepartmentListItem, Paginated } from "../types";
import { useLanguage } from "../i18n/LanguageContext";

const API_BASE = "http://127.0.0.1:8000";
const toAbsoluteUrl = (path: string) => (path.startsWith("http") ? path : `${API_BASE}${path}`);

export function DepartmentListPage() {
  const [items, setItems] = useState<DepartmentListItem[] | null>(null);
  const { lang } = useLanguage();

  useEffect(() => {
    let cancelled = false;

    async function loadAllPages() {
      const all: DepartmentListItem[] = [];
      // 30 departments is already past the default page size (20), so the
      // first page alone would silently drop the rest -- follow `next`
      // until the list is exhausted instead of showing a partial result.
      let path: string | null = "/api/v1/departments/";
      while (path) {
        const res = await fetch(path);
        const data: Paginated<DepartmentListItem> = await res.json();
        all.push(...data.results);
        path = data.next ? new URL(data.next).pathname + new URL(data.next).search : null;
      }
      if (!cancelled) setItems(all);
    }

    loadAllPages();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="mb-6 font-display text-2xl font-extrabold text-primary-900">
        {lang === "uz" ? "Kafedralar" : lang === "ru" ? "Кафедры" : "Departments"}
      </h1>

      {items === null ? (
        <p className="text-foreground-500">Yuklanmoqda...</p>
      ) : items.length === 0 ? (
        <p className="text-foreground-500">Hozircha kafedralar yo'q.</p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/kafedralar/${item.slug}`}
              className="page-card flex items-center gap-4 p-4 hover:border-primary-200"
            >
              {item.logo && (
                <img
                  src={toAbsoluteUrl(item.logo.file)}
                  alt={item.logo.alt_text}
                  className="h-12 w-12 shrink-0 rounded-full object-cover"
                />
              )}
              <span className="font-display text-lg font-bold text-primary-900">{item.name[lang]}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
