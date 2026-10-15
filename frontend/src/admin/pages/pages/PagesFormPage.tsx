import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { adminResource } from "@/api/admin";
import type { AdminPage } from "@/admin/types";
import FormActionBar from "@/admin/components/FormActionBar";
import LangTabs, { type Lang } from "@/admin/components/LangTabs";
import PageHeader from "@/admin/components/PageHeader";
import PagePlacement from "@/admin/components/PagePlacement";
import RichTextEditor from "@/admin/components/RichTextEditor";
import { useToast } from "@/admin/components/Toast";
import { nowLabel, useUnsavedGuard } from "@/admin/components/useUnsavedGuard";
import { ApiError } from "@/types/api";
import { adminErrorMessage } from "@/admin/hooks/useAdminList";

const pagesApi = adminResource<AdminPage>("pages");

const EMPTY: Partial<AdminPage> = {
  title_uz: "",
  title_ru: "",
  title_en: "",
  content_uz: "",
  content_ru: "",
  content_en: "",
};

function hasText(html: string | null | undefined) {
  return (html ?? "").replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim() !== "";
}

export default function PagesFormPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const location = useLocation();
  const justCreated = Boolean((location.state as { created?: boolean } | null)?.created);
  const toast = useToast();

  const [form, setForm] = useState<Partial<AdminPage>>(EMPTY);
  const [initial, setInitial] = useState(() => JSON.stringify(EMPTY));
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [lang, setLang] = useState<Lang>("uz");
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const dirty = JSON.stringify(form) !== initial;
  useUnsavedGuard(dirty);

  useEffect(() => {
    if (!isNew) {
      pagesApi
        .get(Number(id))
        .then((data) => {
          setForm(data);
          setInitial(JSON.stringify(data));
        })
        .catch((err) => setError(adminErrorMessage(err, "Sahifani yuklab bo'lmadi.")))
        .finally(() => setLoading(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  function set<K extends keyof AdminPage>(key: K, value: AdminPage[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const hadTitle = Boolean((JSON.parse(initial) as Partial<AdminPage>).title_uz);
    if ((isNew || hadTitle) && !form.title_uz?.trim()) {
      setLang("uz");
      toast.error("O'zbekcha sarlavhani kiriting.");
      window.setTimeout(() => document.getElementById("page-title")?.focus(), 50);
      return;
    }
    setSaving(true);
    setError("");
    setFieldErrors({});
    try {
      if (isNew) {
        const created = await pagesApi.create(form);
        toast.success("Sahifa qo'shildi.");
        setInitial(JSON.stringify(created));
        navigate(`/admin/pages/${created.id}`, { replace: true, state: { created: true } });
      } else {
        // Show what was really stored: the server re-renders the content (and tables/PDFs stay as chips).
        const updated = await pagesApi.update(Number(id), form);
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

  const filled = { uz: !!form.title_uz?.trim() || hasText(form.content_uz), ru: !!form.title_ru?.trim() || hasText(form.content_ru), en: !!form.title_en?.trim() || hasText(form.content_en) };
  const invalid = {
    uz: !!(fieldErrors.title_uz || fieldErrors.content_uz),
    ru: !!(fieldErrors.title_ru || fieldErrors.content_ru),
    en: !!(fieldErrors.title_en || fieldErrors.content_en),
  };
  const titleKey = `title_${lang}` as keyof AdminPage;
  const contentKey = `content_${lang}` as keyof AdminPage;

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        back={{ to: "/admin/pages", label: "Sahifalar" }}
        title={isNew ? "Yangi sahifa" : form.title_uz || form.menu_title || "Sahifani tahrirlash"}
        subtitle={
          isNew ? "Saqlagandan keyin sahifani saytning menyusiga qo'shish taklif qilinadi: menyuga qo'shilmaguncha u saytda ko'rinmaydi." : undefined
        }
      />

      {error && (
        <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          <i className="ri-error-warning-line mt-0.5 text-base" aria-hidden="true" />
          {error}
        </div>
      )}

      {!isNew && form.slug && (
        <PagePlacement slug={form.slug} title={form.title_uz || form.menu_title || ""} titleRu={form.title_ru} titleEn={form.title_en} justCreated={justCreated} />
      )}

      <form onSubmit={onSubmit}>
        <section className="rounded-xl border border-background-200 bg-background-50 p-4 sm:p-5">
          <div className="mb-4">
            <LangTabs value={lang} onChange={setLang} filled={filled} invalid={invalid} />
          </div>

          <details className="mb-4 rounded-lg bg-background-100 px-3 py-2 text-xs text-foreground-600">
            <summary className="cursor-pointer font-medium text-foreground-700">Jadval, PDF va boshqa maxsus bloklar haqida</summary>
            <p className="mt-2 leading-relaxed">
              Jadval, PDF-hujjat, galereya va boshqa maxsus bloklar matnda kulrang <b>«tahrirlanmaydi»</b> katakchalar
              ko'rinishida turadi: ularni sudrab joyini o'zgartirish yoki tanlab o'chirish mumkin, aks holda saqlashda o'zgarmaydi.
              Eski saytdan ko'chirilgan sahifalarning sarlavhasi menyudan olinadi, shuning uchun bu yerda bo'sh bo'lishi mumkin.
            </p>
          </details>

          <div className="mb-4">
            <label htmlFor="page-title" className="mb-1.5 block text-sm font-medium text-foreground-700">
              Sarlavha {lang === "uz" && (isNew || Boolean(form.title_uz)) && "*"}
            </label>
            <input
              id="page-title"
              value={(form[titleKey] as string) ?? ""}
              onChange={(e) => set(titleKey, e.target.value as never)}
              className="w-full h-11 px-4 rounded-lg border border-background-300 bg-background-50 text-sm font-medium focus:outline-none focus:border-primary-500"
            />
            {!form.title_uz && form.menu_title && lang === "uz" && (
              <p className="mt-1 text-xs text-foreground-500">Bu sahifaning nomi menyudan olinadi: «{form.menu_title}». Shu yerda yozsangiz, o'sha nom ishlatiladi.</p>
            )}
            {fieldErrors[`title_${lang}`] && <p className="mt-1 text-xs text-red-600">{fieldErrors[`title_${lang}`][0]}</p>}
          </div>

          <RichTextEditor
            key={lang}
            label="Matn"
            value={(form[contentKey] as string) ?? ""}
            onChange={(v) => set(contentKey, v as never)}
            allowFiles={lang === "uz"}
            rawHtml={Boolean(form.raw_editing)}
          />
          {fieldErrors[`content_${lang}`] && <p className="mt-1 text-xs text-red-600">{fieldErrors[`content_${lang}`][0]}</p>}
        </section>

        <FormActionBar backTo="/admin/pages" saving={saving} dirty={dirty} savedAt={savedAt} />
      </form>
    </div>
  );
}
