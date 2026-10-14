import { useEffect, useState } from "react";
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

/** For 1-row config tables (Counter/Setting/Logo) — no list, no create, no delete. */
export default function SingletonFormPage({ config }: { config: EntityConfig }) {
  const api = adminResource<Values & { id: number }>(config.resource);
  const [values, setValues] = useState<Values>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const toast = useToast();
  const [initial, setInitial] = useState("{}");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .list({ pageSize: 1 })
      .then((r) => {
        if (!cancelled && r.items[0]) {
          setValues(r.items[0]);
          setInitial(JSON.stringify(r.items[0]));
        }
      })
      .catch((err) => {
        if (!cancelled) setError(adminErrorMessage(err, "Ma'lumotlarni yuklab bo'lmadi."));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.resource]);

  const dirty = JSON.stringify(values) !== initial;
  useUnsavedGuard(dirty);

  function onChange(key: string, value: unknown) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setFieldErrors({});
    try {
      const updated = await api.update(values.id as number, values);
      setValues(updated);
      setInitial(JSON.stringify(updated));
      setSavedAt(nowLabel());
      toast.success("Saqlandi.");
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

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={config.title} />

      {error && <div role="alert" className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">{error}</div>}

      <form onSubmit={onSubmit}>
        <EntityFormFields config={config} values={values} onChange={onChange} fieldErrors={fieldErrors} />
        <FormActionBar backTo="/admin" saving={saving} dirty={dirty} savedAt={savedAt} />
      </form>
    </div>
  );
}
