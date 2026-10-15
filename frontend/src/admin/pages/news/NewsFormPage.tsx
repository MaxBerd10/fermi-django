import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminResource, translateTexts, type TranslationLang } from "@/api/admin";
import type { AdminPost, AdminPostcategory } from "@/admin/types";
import FormActionBar from "@/admin/components/FormActionBar";
import GalleryPicker from "@/admin/components/GalleryPicker";
import LangTabs, { type Lang } from "@/admin/components/LangTabs";
import MediaPicker from "@/admin/components/MediaPicker";
import PageHeader from "@/admin/components/PageHeader";
import RichTextEditor from "@/admin/components/RichTextEditor";
import { useConfirm } from "@/admin/components/ConfirmDialog";
import { useToast } from "@/admin/components/Toast";
import { nowLabel, useUnsavedGuard } from "@/admin/components/useUnsavedGuard";
import { ApiError } from "@/types/api";
import { adminErrorMessage } from "../../hooks/useAdminList";
import { fromTashkentInput, toTashkentInput } from "../../format";

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

const INPUT = "w-full h-11 px-4 rounded-lg border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500";

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-background-200 bg-background-50 p-4 sm:p-5">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wide text-foreground-500">{title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

export default function NewsFormPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const toast = useToast();
  const confirm = useConfirm();

  const [form, setForm] = useState<Partial<AdminPost>>(EMPTY);
  const [initial, setInitial] = useState(() => JSON.stringify(EMPTY));
  const [categories, setCategories] = useState<AdminPostcategory[]>([]);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [translating, setTranslating] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [lang, setLang] = useState<Lang>("uz");
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const dirty = JSON.stringify(form) !== initial;
  useUnsavedGuard(dirty);

  useEffect(() => {
    categoriesApi
      .list({ pageSize: 100 })
      .then((r) => setCategories(r.items))
      .catch((err) => setError(adminErrorMessage(err, "Kategoriyalarni yuklab bo'lmadi.")));
    if (!isNew) {
      postsApi
        .get(Number(id))
        .then((data) => {
          setForm(data);
          setInitial(JSON.stringify(data));
        })
        .catch((err) => setError(adminErrorMessage(err, "Yangilikni yuklab bo'lmadi.")))
        .finally(() => setLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function set<K extends keyof AdminPost>(key: K, value: AdminPost[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  /** Fills ru/en title+content from the uz ones. `onlyEmpty` leaves anything the editor already wrote untouched. */
  async function translateFromUz(source: Partial<AdminPost>, onlyEmpty: boolean): Promise<Partial<AdminPost>> {
    const targets = TARGET_LANGS.filter(
      (l) => !onlyEmpty || !source[`title_${l}`]?.trim() || isBlank(source[`content_${l}`]),
    );
    if (targets.length === 0 || (!source.title_uz?.trim() && isBlank(source.content_uz))) return source;

    const result = await translateTexts(
      { title: source.title_uz ?? "", content: isBlank(source.content_uz) ? "" : source.content_uz ?? "" },
      targets as TranslationLang[],
    );
    const next = { ...source };
    for (const l of targets) {
      const t = result[l];
      if (!t) continue;
      if (!onlyEmpty || !next[`title_${l}`]?.trim()) next[`title_${l}`] = t.title;
      if (!onlyEmpty || isBlank(next[`content_${l}`])) next[`content_${l}`] = t.content;
    }
    return next;
  }

  async function onTranslateClick() {
    const hasExisting = TARGET_LANGS.some((l) => form[`title_${l}`]?.trim() || !isBlank(form[`content_${l}`]));
    if (
      hasExisting &&
      !(await confirm({
        title: "Mavjud RU va EN matnlar almashtirilsinmi?",
        message: "RU va EN maydonlaridagi yozilgan matn UZ matnining yangi tarjimasi bilan almashtiriladi.",
        confirmLabel: "Ha, tarjima qilish",
      }))
    )
      return;
    setTranslating(true);
    setError("");
    try {
      setForm(await translateFromUz(form, false));
      toast.info("RU va EN tarjimalari to'ldirildi — saqlashdan oldin tekshirib chiqing.");
    } catch {
      toast.error("Tarjima qilib bo'lmadi. Internet aloqasini tekshirib, qayta urinib ko'ring.");
    } finally {
      setTranslating(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title_uz?.trim()) {
      // The Uzbek title is the one required field; it may be on a tab that is not open right now.
      setLang("uz");
      toast.error("O'zbekcha sarlavhani kiriting.");
      window.setTimeout(() => document.getElementById("news-title")?.focus(), 50);
      return;
    }
    setSaving(true);
    setError("");
    setFieldErrors({});
    try {
      // Anything left empty in RU/EN gets a machine translation of UZ instead
      // of silently falling back to the Uzbek text on the public site.
      let payload = form;
      try {
        payload = await translateFromUz(form, true);
        if (payload !== form) setForm(payload);
      } catch {
        toast.info("Avtomatik tarjima ishlamadi — bo'sh RU/EN maydonlari o'rniga UZ matni ko'rsatiladi.");
      }
      if (isNew) {
        const created = await postsApi.create(payload);
        toast.success("Yangilik qo'shildi.");
        setInitial(JSON.stringify(created));
        navigate(`/admin/news/${created.id}`, { replace: true });
      } else {
        const updated = await postsApi.update(Number(id), payload);
        setForm(updated);
        setInitial(JSON.stringify(updated));
        setSavedAt(nowLabel());
        toast.success("Saqlandi.");
      }
    } catch (err) {
      let message: string;
      if (err instanceof ApiError && err.status === 400) {
        message = err.message;
        setFieldErrors(err.fields ?? {});
        // Open the language tab that holds the first error.
        const bad = (["uz", "ru", "en"] as const).find((l) => err.fields?.[`title_${l}`] || err.fields?.[`content_${l}`]);
        if (bad) setLang(bad);
      } else {
        message = adminErrorMessage(err, "Saqlashda xatolik yuz berdi.");
      }
      setError(message);
      toast.error(message);
      window.scrollTo({ top: 0, behavior: "smooth" });
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

  const filled = {
    uz: !!form.title_uz?.trim() || !isBlank(form.content_uz),
    ru: !!form.title_ru?.trim() || !isBlank(form.content_ru),
    en: !!form.title_en?.trim() || !isBlank(form.content_en),
  };
  const invalid = {
    uz: !!(fieldErrors.title_uz || fieldErrors.content_uz),
    ru: !!(fieldErrors.title_ru || fieldErrors.content_ru),
    en: !!(fieldErrors.title_en || fieldErrors.content_en),
  };
  const titleKey = `title_${lang}` as keyof AdminPost;
  const contentKey = `content_${lang}` as keyof AdminPost;
  const published = (form.status ?? 1) === 1;

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        back={{ to: "/admin/news", label: "Yangiliklar" }}
        title={isNew ? "Yangi yangilik" : "Yangilikni tahrirlash"}
      />

      {error && (
        <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          <i className="ri-error-warning-line mt-0.5 text-base" aria-hidden="true" />
          {error}
        </div>
      )}

      <form onSubmit={onSubmit}>
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="space-y-4">
            <section className="rounded-xl border border-background-200 bg-background-50 p-4 sm:p-5">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <LangTabs value={lang} onChange={setLang} filled={filled} invalid={invalid} />
                {lang === "uz" ? (
                  <button
                    type="button"
                    onClick={onTranslateClick}
                    disabled={translating || (!form.title_uz?.trim() && isBlank(form.content_uz))}
                    className="h-9 px-3 rounded-lg border border-primary-300 text-primary-700 text-sm font-medium hover:bg-primary-50 cursor-pointer disabled:opacity-50 flex items-center gap-2"
                  >
                    <i className={`w-4 h-4 flex items-center justify-center ${translating ? "ri-loader-4-line animate-spin" : "ri-translate-2"}`} />
                    {translating ? "Tarjima qilinmoqda..." : "RU va EN ga tarjima qilish"}
                  </button>
                ) : (
                  <span className="text-xs text-foreground-500">Bo'sh qolsa, saqlashda UZ dan avtomatik tarjima qilinadi</span>
                )}
              </div>

              {lang === "uz" && (
                <p className="mb-4 text-xs text-foreground-500">
                  O'zbekcha matn lotin alifbosida bo'lishi kerak. Kirill harfida yozilsa, saqlashda avtomatik lotinga o'giriladi.
                </p>
              )}

              <div className="mb-4">
                <label htmlFor="news-title" className="mb-1.5 block text-sm font-medium text-foreground-700">
                  Sarlavha {lang === "uz" && "*"}
                </label>
                <input
                  id="news-title"
                  value={(form[titleKey] as string) ?? ""}
                  onChange={(e) => set(titleKey, e.target.value as never)}
                  required={lang === "uz"}
                  className={`${INPUT} font-medium`}
                />
                {fieldErrors[`title_${lang}`] && <p className="mt-1 text-xs text-red-600">{fieldErrors[`title_${lang}`][0]}</p>}
              </div>

              <RichTextEditor
                key={lang}
                label="Matn"
                value={(form[contentKey] as string) ?? ""}
                onChange={(v) => set(contentKey, v as never)}
                allowFiles={lang === "uz"}
              />
              {fieldErrors[`content_${lang}`] && <p className="mt-1 text-xs text-red-600">{fieldErrors[`content_${lang}`][0]}</p>}
            </section>
          </div>

          <div className="grid grid-cols-1 content-start gap-4 md:grid-cols-2 xl:grid-cols-1">
            <Card title="Nashr">
              <div>
                <span className="mb-1.5 block text-sm font-medium text-foreground-700">Holat</span>
                <div className="grid grid-cols-2 gap-1 rounded-lg border border-background-300 bg-background-100 p-1">
                  {[
                    { value: 1, label: "E'lon qilingan", icon: "ri-global-line" },
                    { value: 0, label: "Qoralama", icon: "ri-draft-line" },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => set("status", opt.value)}
                      aria-pressed={(form.status ?? 1) === opt.value}
                      className={`flex h-9 cursor-pointer items-center justify-center gap-1.5 rounded-md text-sm font-medium ${
                        (form.status ?? 1) === opt.value ? "bg-background-50 text-primary-700 shadow-sm" : "text-foreground-500 hover:text-foreground-800"
                      }`}
                    >
                      <i className={opt.icon} aria-hidden="true" /> {opt.label}
                    </button>
                  ))}
                </div>
                {!published && <p className="mt-1.5 text-xs text-amber-700">Qoralama saytda ko'rinmaydi.</p>}
              </div>

              <div>
                <label htmlFor="news-category" className="mb-1.5 block text-sm font-medium text-foreground-700">Kategoriya *</label>
                <select
                  id="news-category"
                  value={form.category_id ?? ""}
                  onChange={(e) => set("category_id", Number(e.target.value))}
                  required
                  className={INPUT}
                >
                  <option value="">Tanlang</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.title_uz}</option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="news-date" className="mb-1.5 block text-sm font-medium text-foreground-700">Nashr sanasi</label>
                <input
                  id="news-date"
                  type="datetime-local"
                  value={toTashkentInput(form.date)}
                  onChange={(e) => set("date", e.target.value ? fromTashkentInput(e.target.value) : null)}
                  className={INPUT}
                />
                <details className="mt-1.5 text-xs text-foreground-500">
                  <summary className="cursor-pointer hover:text-foreground-800">Sana qanday ishlaydi?</summary>
                  <p className="mt-1 leading-relaxed">
                    Bo'sh qoldirilsa — hozirgi vaqt. O'tgan sana qo'yilsa yangilik shu sanada chiqqandek ko'rinadi; kelajak sanasi
                    qo'yilsa — shu vaqtgacha saytda ko'rinmaydi.
                  </p>
                </details>
                {fieldErrors.date && <p className="mt-1 text-xs text-red-600">{fieldErrors.date[0]}</p>}
              </div>
            </Card>

            <Card title="Rasmlar">
              <MediaPicker label="Asosiy rasm (muqova)" value={form.img} onChange={(path) => set("img", path)} />
              <GalleryPicker label="Qo'shimcha rasmlar (galereya)" value={form.gallery} onChange={(paths) => set("gallery", paths)} />
            </Card>
          </div>
        </div>

        <FormActionBar backTo="/admin/news" saving={saving} dirty={dirty} savedAt={savedAt} />
      </form>
    </div>
  );
}
