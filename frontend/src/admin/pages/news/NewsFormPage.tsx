import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminResource, translateTexts, type TranslationLang } from "@/api/admin";
import type { AdminPost, AdminPostcategory } from "@/admin/types";
import GalleryPicker from "@/admin/components/GalleryPicker";
import MediaPicker from "@/admin/components/MediaPicker";
import RichTextEditor from "@/admin/components/RichTextEditor";
import { ApiError } from "@/types/api";

const postsApi = adminResource<AdminPost>("news");
const categoriesApi = adminResource<AdminPostcategory>("postcategories");

const EMPTY: Partial<AdminPost> = {
  title_uz: "",
  title_ru: "",
  title_en: "",
  content_uz: "",
  content_ru: "",
  content_en: "",
  status: 1,
  img: "",
  gallery: [],
};

const TARGET_LANGS = ["ru", "en"] as const;

/** RichTextEditor's "empty" is still markup ("<p></p>"), so compare on visible text. */
function isBlank(html: string | null | undefined) {
  return !(html ?? "").replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim();
}

export default function NewsFormPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();

  const [form, setForm] = useState<Partial<AdminPost>>(EMPTY);
  const [categories, setCategories] = useState<AdminPostcategory[]>([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [translating, setTranslating] = useState(false);
  const [notice, setNotice] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    categoriesApi.list({ pageSize: 100 }).then((r) => setCategories(r.items));
    if (!isNew) {
      postsApi.get(Number(id)).then((data) => {
        setForm(data);
        setLoading(false);
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function set<K extends keyof AdminPost>(key: K, value: AdminPost[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  /** Fills ru/en title+content from the uz ones. `onlyEmpty` leaves anything the editor already wrote untouched. */
  async function translateFromUz(source: Partial<AdminPost>, onlyEmpty: boolean): Promise<Partial<AdminPost>> {
    const targets = TARGET_LANGS.filter(
      (lang) => !onlyEmpty || !source[`title_${lang}`]?.trim() || isBlank(source[`content_${lang}`]),
    );
    if (targets.length === 0 || (!source.title_uz?.trim() && isBlank(source.content_uz))) return source;

    const result = await translateTexts(
      { title: source.title_uz ?? "", content: isBlank(source.content_uz) ? "" : source.content_uz ?? "" },
      targets as TranslationLang[],
    );
    const next = { ...source };
    for (const lang of targets) {
      const t = result[lang];
      if (!t) continue;
      if (!onlyEmpty || !next[`title_${lang}`]?.trim()) next[`title_${lang}`] = t.title;
      if (!onlyEmpty || isBlank(next[`content_${lang}`])) next[`content_${lang}`] = t.content;
    }
    return next;
  }

  async function onTranslateClick() {
    const hasExisting = TARGET_LANGS.some((lang) => form[`title_${lang}`]?.trim() || !isBlank(form[`content_${lang}`]));
    if (hasExisting && !window.confirm("RU va EN maydonlaridagi mavjud matn UZ tarjimasi bilan almashtiriladi. Davom etasizmi?")) return;
    setTranslating(true);
    setError("");
    setNotice("");
    try {
      setForm(await translateFromUz(form, false));
      setNotice("RU va EN tarjimalari to'ldirildi — saqlashdan oldin tekshirib chiqing.");
    } catch {
      setError("Tarjima qilib bo'lmadi. Internet aloqasini tekshirib, qayta urinib ko'ring.");
    } finally {
      setTranslating(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    setFieldErrors({});
    try {
      // Anything left empty in RU/EN gets a machine translation of UZ instead
      // of silently falling back to the Uzbek text on the public site.
      let payload = form;
      try {
        payload = await translateFromUz(form, true);
        if (payload !== form) setForm(payload);
      } catch {
        setNotice("Avtomatik tarjima ishlamadi — bo'sh RU/EN maydonlari o'rniga UZ matni ko'rsatiladi.");
      }
      if (isNew) {
        const created = await postsApi.create(payload);
        navigate(`/admin/news/${created.id}`, { replace: true });
      } else {
        setForm(await postsApi.update(Number(id), payload));
        setNotice((n) => n || "Saqlandi.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setFieldErrors(err.fields ?? {});
      } else {
        setError("Saqlashda xatolik yuz berdi.");
      }
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="py-16 flex justify-center">
        <i className="ri-loader-4-line w-8 h-8 flex items-center justify-center animate-spin text-primary-500 text-3xl" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <h1 className="font-heading text-2xl font-bold text-foreground-950 mb-6">
        {isNew ? "Yangi yangilik" : "Yangilikni tahrirlash"}
      </h1>

      {error && <div className="mb-4 p-3 rounded-md bg-accent-50 border border-accent-200 text-sm text-accent-800">{error}</div>}
      {notice && <div className="mb-4 p-3 rounded-md bg-primary-50 border border-primary-200 text-sm text-primary-800">{notice}</div>}

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="bg-background-50 border border-background-200 rounded-lg p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1.5">Kategoriya *</label>
              <select
                value={form.category_id ?? ""}
                onChange={(e) => set("category_id", Number(e.target.value))}
                required
                className="w-full h-11 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="">Tanlang</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.title_uz}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1.5">Holat</label>
              <select
                value={form.status ?? 1}
                onChange={(e) => set("status", Number(e.target.value))}
                className="w-full h-11 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              >
                <option value={1}>Faol</option>
                <option value={0}>Nofaol</option>
              </select>
            </div>
          </div>
          <MediaPicker label="Asosiy rasm (muqova)" value={form.img} onChange={(path) => set("img", path)} />
          <GalleryPicker label="Qo'shimcha rasmlar (galereya)" value={form.gallery} onChange={(paths) => set("gallery", paths)} />
        </div>

        {(["uz", "ru", "en"] as const).map((lang) => (
          <div key={lang} className="bg-background-50 border border-background-200 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-semibold text-foreground-800 uppercase text-xs tracking-wide">{lang}</h2>
              {lang === "uz" ? (
                <button
                  type="button"
                  onClick={onTranslateClick}
                  disabled={translating || (!form.title_uz?.trim() && isBlank(form.content_uz))}
                  className="h-9 px-3 rounded-md border border-primary-300 text-primary-700 text-sm font-medium hover:bg-primary-50 cursor-pointer disabled:opacity-50 flex items-center gap-2"
                >
                  <i className={`w-4 h-4 flex items-center justify-center ${translating ? "ri-loader-4-line animate-spin" : "ri-translate-2"}`} />
                  {translating ? "Tarjima qilinmoqda..." : "RU va EN ga tarjima qilish"}
                </button>
              ) : (
                <span className="text-xs text-foreground-500">Bo'sh qolsa, saqlashda UZ dan avtomatik tarjima qilinadi</span>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1.5">
                Sarlavha {lang === "uz" && "*"}
              </label>
              <input
                value={(form[`title_${lang}` as keyof AdminPost] as string) ?? ""}
                onChange={(e) => set(`title_${lang}` as keyof AdminPost, e.target.value as never)}
                required={lang === "uz"}
                className="w-full h-11 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              />
              {fieldErrors[`title_${lang}`] && <p className="mt-1 text-xs text-accent-600">{fieldErrors[`title_${lang}`][0]}</p>}
            </div>
            <RichTextEditor
              label="Matn"
              value={(form[`content_${lang}` as keyof AdminPost] as string) ?? ""}
              onChange={(v) => set(`content_${lang}` as keyof AdminPost, v as never)}
            />
          </div>
        ))}

        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="h-11 px-6 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer disabled:opacity-60">
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          <button type="button" onClick={() => navigate("/admin/news")} className="h-11 px-6 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer">
            Bekor qilish
          </button>
        </div>
      </form>
    </div>
  );
}
