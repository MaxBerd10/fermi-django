import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { adminResource } from "@/api/admin";
import type { EntityConfig } from "../genericTypes";
import EntityFormFields from "./EntityFormFields";
import FormActionBar from "./FormActionBar";
import PageHeader from "./PageHeader";
import { useToast } from "./Toast";
import { nowLabel, useUnsavedGuard } from "./useUnsavedGuard";
import { ApiError } from "@/types/api";
import { adminErrorMessage } from "../hooks/useAdminList";

type Values = Record<string, unknown>;

export default function GenericFormPage({ config }: { config: EntityConfig }) {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const location = useLocation();
  const api = adminResource<Values & { id: number }>(config.resource);

  const toast = useToast();
  const [values, setValues] = useState<Values>({});
  const [initial, setInitial] = useState("{}");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const dirty = JSON.stringify(values) !== initial;
  useUnsavedGuard(dirty);
  const [loading, setLoading] = useState(!isNew);
  const [loadError, setLoadError] = useState("");
  const [saving, setSaving] = useState(false);
  // Arriving from "create" navigates here with state.saved: the record was just created.
  const justCreated = Boolean((location.state as { saved?: boolean } | null)?.saved);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    setLoadError("");
    if (isNew) {
      setValues({});
      setInitial("{}");
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    api
      .get(Number(id))
      .then((data) => {
        if (!cancelled) {
          setValues(data);
          setInitial(JSON.stringify(data));
        }
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
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setFieldErrors({});
    // A file/picture/select cannot use the browser's own "required" check -- say what is missing before the round trip.
    const missing: Record<string, string[]> = {};
    for (const field of config.fields) {
      if (!("required" in field) || !field.required) continue;
      if (field.kind !== "media" && field.kind !== "async-select" && field.kind !== "select") continue;
      const value = values[field.key];
      if (value === undefined || value === null || value === "" || value === 0) {
        missing[field.key] = [field.kind === "media" ? "Fayl yoki rasm tanlang." : "Ro'yxatdan birini tanlang."];
      }
    }
    if (Object.keys(missing).length > 0) {
      setFieldErrors(missing);
      setError("Majburiy maydonlar to'ldirilmagan. Qizil yozuvli joylarni tekshiring.");
      toast.error("Majburiy maydonlar to'ldirilmagan.");
      setSaving(false);
      return;
    }
    try {
      if (isNew) {
        const created = await api.create(values);
        toast.success("Yaratildi.");
        setInitial(JSON.stringify(created));
        navigate(`/admin/${config.resource}/${created.id}`, { replace: true, state: { saved: true } });
      } else {
        const updated = await api.update(Number(id), values);
        // The server may normalise what was typed (trimmed text, derived fields) -- show what was really stored.
        setValues(updated);
        setInitial(JSON.stringify(updated));
        setSavedAt(nowLabel());
        toast.success("Saqlandi.");
      }
    } catch (err) {
      let message: string;
      if (err instanceof ApiError && err.status === 400) {
        message = err.message;
        setFieldErrors(err.fields ?? {});
      } else {
        message = adminErrorMessage(err, "Saqlashda xatolik yuz berdi.");
      }
      setError(message);
      toast.error(message);
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
        <div role="alert" className="mb-4 p-4 rounded-md bg-red-50 border border-red-200 text-sm text-red-800">{loadError}</div>
        <Link to={`/admin/${config.resource}`} className="text-sm text-primary-600 underline">← Ro'yxatga qaytish</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        back={{ to: `/admin/${config.resource}`, label: config.title }}
        title={isNew ? (config.addLabel ?? "Yangi yozuv") : "Tahrirlash"}
      />

      {error && <div role="alert" className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">{error}</div>}

      <form onSubmit={onSubmit}>
        <EntityFormFields config={config} values={values} onChange={onChange} fieldErrors={fieldErrors} />
        <FormActionBar backTo={`/admin/${config.resource}`} saving={saving} dirty={dirty} savedAt={savedAt ?? (justCreated ? nowLabel() : null)} />
      </form>
    </div>
  );
}
