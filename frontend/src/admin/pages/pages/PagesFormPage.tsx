import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { adminResource } from "@/api/admin";
import type { AdminPage } from "@/admin/types";
import RichTextEditor from "@/admin/components/RichTextEditor";
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

export default function PagesFormPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();

  const [form, setForm] = useState<Partial<AdminPage>>(EMPTY);
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    if (!isNew) {
      pagesApi
        .get(Number(id))
        .then((data) => setForm(data))
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
    setSaving(true);
    setError("");
    setSaved(false);
    setFieldErrors({});
    try {
      if (isNew) {
        const created = await pagesApi.create(form);
        navigate(`/admin/pages/${created.id}`, { replace: true });
      } else {
        // Show what was really stored: the server re-renders the content (and tables/PDFs stay as chips).
        setForm(await pagesApi.update(Number(id), form));
        setSaved(true);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError(err.message);
        setFieldErrors(err.fields ?? {});
      } else {
        setError(adminErrorMessage(err, "Saqlashda xatolik yuz berdi."));
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
        {isNew ? "Yangi sahifa" : "Sahifani tahrirlash"}
      </h1>

      {error && <div role="alert" className="mb-4 p-3 rounded-md bg-accent-50 border border-accent-200 text-sm text-accent-800">{error}</div>}
      {saved && <div role="status" className="mb-4 p-3 rounded-md bg-green-50 border border-green-200 text-sm text-green-800">Saqlandi.</div>}

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="bg-background-50 border border-background-200 rounded-lg p-5 space-y-4">
          {!isNew && (
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1.5">Slug (manzil)</label>
              <input value={form.slug ?? ""} disabled className="w-full sm:w-96 h-11 px-4 rounded-md border border-background-300 bg-background-100 text-sm text-foreground-500" />
            </div>
          )}
          <p className="text-xs text-foreground-500">
            Jadval, PDF-hujjat, galereya va boshqa maxsus bloklar matnda kulrang <b>«tahrirlanmaydi»</b> katakchalar
            ko'rinishida turadi: ularni sudrab joyini o'zgartirish yoki tanlab o'chirish mumkin, aks holda saqlashda o'zgarmaydi.
            Eski saytdan ko'chirilgan sahifalarning sarlavhasi menyudan olinadi, shuning uchun bu yerda bo'sh bo'lishi mumkin.
          </p>
        </div>

        {(["uz", "ru", "en"] as const).map((lang) => (
          <div key={lang} className="bg-background-50 border border-background-200 rounded-lg p-5 space-y-4">
            <h2 className="font-semibold text-foreground-800 uppercase text-xs tracking-wide">{lang}</h2>
            <div>
              <label className="block text-sm font-medium text-foreground-700 mb-1.5">
                Sarlavha {lang === "uz" && (isNew || Boolean(form.title_uz)) && "*"}
              </label>
              <input
                value={(form[`title_${lang}` as keyof AdminPage] as string) ?? ""}
                onChange={(e) => set(`title_${lang}` as keyof AdminPage, e.target.value as never)}
                required={lang === "uz" && (isNew || Boolean(form.title_uz))}
                className="w-full h-11 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              />
              {fieldErrors[`title_${lang}`] && <p className="mt-1 text-xs text-accent-600">{fieldErrors[`title_${lang}`][0]}</p>}
            </div>
            <RichTextEditor
              label="Matn"
              value={(form[`content_${lang}` as keyof AdminPage] as string) ?? ""}
              onChange={(v) => set(`content_${lang}` as keyof AdminPage, v as never)}
            />
          </div>
        ))}

        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="h-11 px-6 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer disabled:opacity-60">
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          <button type="button" onClick={() => navigate("/admin/pages")} className="h-11 px-6 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer">
            Bekor qilish
          </button>
        </div>
      </form>
    </div>
  );
}
