import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { NewsPostListItem, Paginated } from "../types";
import { useLanguage } from "../i18n/LanguageContext";

export function NewsListPage() {
  const [items, setItems] = useState<NewsPostListItem[] | null>(null);
  const { lang } = useLanguage();

  useEffect(() => {
    fetch("/api/v1/news/")
      .then((res) => res.json())
      .then((data: Paginated<NewsPostListItem>) => setItems(data.results));
  }, []);

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="mb-6 font-display text-2xl font-extrabold text-primary-900">
        {lang === "uz" ? "Yangiliklar" : lang === "ru" ? "Новости" : "News"}
      </h1>

      {items === null ? (
        <p className="text-foreground-500">Yuklanmoqda...</p>
      ) : items.length === 0 ? (
        <p className="text-foreground-500">Hozircha yangiliklar yo'q.</p>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <Link key={item.id} to={`/yangiliklar/${item.slug}`} className="page-card block p-5 hover:border-primary-200">
              <p className="text-xs font-semibold uppercase tracking-wide text-primary-600">
                {new Date(item.published_at).toLocaleDateString(lang)}
              </p>
              <h2 className="mt-1 font-display text-lg font-bold text-primary-900">{item.title[lang]}</h2>
              {item.excerpt[lang] && <p className="mt-1 text-sm text-foreground-600">{item.excerpt[lang]}</p>}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
