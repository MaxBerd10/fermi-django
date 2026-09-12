import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import type { NewsPostDetail } from "../types";
import { BlockRenderer } from "../blocks/BlockRenderer";
import { useLanguage } from "../i18n/LanguageContext";

export function NewsDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [post, setPost] = useState<NewsPostDetail | null>(null);
  const { lang } = useLanguage();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/v1/news/${slug}/`)
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        return res.json();
      })
      .then(setPost)
      .catch((e) => setError(String(e)));
  }, [slug]);

  if (error) return <p className="p-8 text-red-600">Xatolik: {error}</p>;
  if (!post) return <p className="p-8 text-foreground-500">Yuklanmoqda...</p>;

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary-600">
        {new Date(post.published_at).toLocaleDateString(lang)}
      </p>
      <h1 className="mb-6 font-display text-2xl font-extrabold tracking-tight text-primary-900 text-balance">
        {post.title[lang]}
      </h1>

      <div className="space-y-5">
        {post.page.blocks
          .slice()
          .sort((a, b) => a.order - b.order)
          .map((block) => (
            <BlockRenderer key={block.id} block={block} lang={lang} />
          ))}
      </div>
    </div>
  );
}
