import { useEffect, useRef, useState } from "react";
import { fieldKey, type EntityConfig, type FieldSpec } from "../genericTypes";
import GenericField from "./GenericField";
import LangTabs, { type Lang } from "./LangTabs";

type Values = Record<string, unknown>;

const LANG_LIST = ["uz", "ru", "en"] as const;

/** A lang-* field is posted as <base>_uz/_ru/_en, so its validation errors live under those keys. */
export function errorsFor(field: FieldSpec, fieldErrors: Record<string, string[]>): string[] {
  if ("base" in field) return LANG_LIST.flatMap((l) => fieldErrors[`${field.base}_${l}`] ?? []);
  return fieldErrors[fieldKey(field)] ?? [];
}

function hasText(value: unknown): boolean {
  return String(value ?? "").replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").trim() !== "";
}

interface Props {
  config: EntityConfig;
  values: Values;
  onChange: (key: string, value: unknown) => void;
  fieldErrors: Record<string, string[]>;
}

/** All fields of a generic form. When any field is per-language it adds the UZ / RU / EN tabs on top, so the
 *  editor fills one language at a time instead of scrolling past three copies of every field. */
export default function EntityFormFields({ config, values, onChange, fieldErrors }: Props) {
  const [lang, setLang] = useState<Lang>("uz");
  const wrapRef = useRef<HTMLDivElement>(null);
  const langFields = config.fields.filter((f): f is Extract<FieldSpec, { base: string }> => "base" in f);
  const hasLang = langFields.length > 0;

  const filled = Object.fromEntries(LANG_LIST.map((l) => [l, langFields.some((f) => hasText(values[`${f.base}_${l}`]))])) as Record<Lang, boolean>;
  const invalid = Object.fromEntries(LANG_LIST.map((l) => [l, langFields.some((f) => fieldErrors[`${f.base}_${l}`])])) as Record<Lang, boolean>;

  // A server-side error in another language: open that tab so the message is in view.
  useEffect(() => {
    const bad = LANG_LIST.find((l) => invalid[l]);
    if (bad && !invalid[lang]) setLang(bad);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fieldErrors]);

  // The browser cannot point at a required input inside a hidden tab: open the tab, then ask it to point again.
  function onInvalidCapture(e: React.FormEvent) {
    const panel = (e.target as HTMLElement).closest<HTMLElement>("[data-lang]");
    const target = panel?.dataset.lang as Lang | undefined;
    if (target && target !== lang) {
      setLang(target);
      requestAnimationFrame(() => wrapRef.current?.closest("form")?.reportValidity());
    }
  }

  return (
    <div ref={wrapRef} onInvalidCapture={onInvalidCapture} className="space-y-5 rounded-xl border border-background-200 bg-background-50 p-4 sm:p-5">
      {hasLang && <LangTabs value={lang} onChange={setLang} filled={filled} invalid={invalid} />}
      {config.fields.map((field) => {
        const messages = errorsFor(field, fieldErrors);
        return (
          <div key={fieldKey(field)}>
            <GenericField field={field} values={values} onChange={onChange} lang={hasLang ? lang : undefined} />
            {messages.length > 0 && <p className="mt-1 text-xs text-red-600">{messages[0]}</p>}
          </div>
        );
      })}
    </div>
  );
}
