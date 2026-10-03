import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { adminResource } from "@/api/admin";
import { fieldKey, type EntityConfig, type FieldSpec } from "../genericTypes";
import GenericField from "./GenericField";
import { ApiError } from "@/types/api";
import { adminErrorMessage } from "../hooks/useAdminList";

type Values = Record<string, unknown>;

/** Validation messages for a field -- a lang-* field is posted as <base>_uz/_ru/_en, so its errors live under those keys. */
function errorsFor(field: FieldSpec, fieldErrors: Record<string, string[]>): string[] {
  if ("base" in field) {
    return (["uz", "ru", "en"] as const).flatMap((lang) => fieldErrors[`${field.base}_${lang}`] ?? []);
  }
  return fieldErrors[fieldKey(field)] ?? [];
}

export default function GenericFormPage({ config }: { config: EntityConfig }) {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const location = useLocation();
  const api = adminResource<Values & { id: number }>(config.resource);

  const [values, setValues] = useState<Values>({});
  const [loading, setLoading] = useState(!isNew);
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  // Arriving from "create" navigates here with state.saved so the confirmation survives the redirect.
  const [saved, setSaved] = useState(Boolean((location.state as { saved?: boolean } | null)?.saved));
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    setLoadError("");
    if (isNew) {
      setValues({});
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    api
      .get(Number(id))
      .then((data) => {
        if (!cancelled) setValues(data);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(adminErrorMessage(err, "Yozuvni yuklab bo'lmadi."));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, config.resource]);

  function onChange(key: string, value: unknown) {
    setValues((v) => ({ ...v, [key]: value }));
    setSaved(false);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSaved(false);
    setFieldErrors({});
    try {
      if (isNew) {
        const created = await api.create(values);
        navigate(`/admin/${config.resource}/${created.id}`, { replace: true, state: { saved: true } });
      } else {
        const updated = await api.update(Number(id), values);
        // The server may normalise what was typed (trimmed text, derived fields) -- show what was really stored.
        setValues(updated);
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

  if (loadError) {
    return (
      <div className="max-w-4xl">
        <div role="alert" className="mb-4 p-4 rounded-md bg-accent-50 border border-accent-200 text-sm text-accent-800">{loadError}</div>
        <Link to={`/admin/${config.resource}`} className="text-sm text-primary-600 underline">← Ro'yxatga qaytish</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl">
      <h1 className="font-heading text-2xl font-bold text-foreground-950 mb-6">
        {isNew ? `Yangi: ${config.title}` : `Tahrirlash: ${config.title}`}
      </h1>

      {error && <div role="alert" className="mb-4 p-3 rounded-md bg-accent-50 border border-accent-200 text-sm text-accent-800">{error}</div>}
      {saved && <div role="status" className="mb-4 p-3 rounded-md bg-green-50 border border-green-200 text-sm text-green-800">Saqlandi.</div>}

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="bg-background-50 border border-background-200 rounded-lg p-5 space-y-4">
          {config.fields.map((field) => {
            const messages = errorsFor(field, fieldErrors);
            return (
              <div key={fieldKey(field)}>
                <GenericField field={field} values={values} onChange={onChange} />
                {messages.length > 0 && <p className="mt-1 text-xs text-accent-600">{messages[0]}</p>}
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-3">
          <button type="submit" disabled={saving} className="h-11 px-6 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer disabled:opacity-60">
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
          <button type="button" onClick={() => navigate(`/admin/${config.resource}`)} className="h-11 px-6 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer">
            Orqaga
          </button>
        </div>
      </form>
    </div>
  );
}
