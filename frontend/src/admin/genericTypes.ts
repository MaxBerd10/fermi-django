export type FieldSpec =
  | { kind: "lang-text"; base: string; label: string; requiredUz?: boolean }
  | { kind: "lang-textarea"; base: string; label: string; requiredUz?: boolean }
  | { kind: "lang-html"; base: string; label: string }
  | { kind: "text"; key: string; label: string; required?: boolean }
  | { kind: "textarea"; key: string; label: string; required?: boolean }
  | { kind: "html"; key: string; label: string }
  | { kind: "media"; key: string; label: string; required?: boolean }
  | { kind: "number"; key: string; label: string; required?: boolean }
  | { kind: "checkbox"; key: string; label: string }
  | { kind: "select"; key: string; label: string; required?: boolean; options: { value: number | string; label: string }[] }
  | { kind: "async-select"; key: string; label: string; required?: boolean; optionsResource: string; optionsLabelKey: string }
  | { kind: "geo-selects"; label: string; regionKey: string; districtKey: string; quarterKey?: string; required?: boolean }
  | { kind: "date"; key: string; label: string }
  /** Display-only value the form never sends back (e.g. when an inbound submission arrived). */
  | { kind: "readonly"; key: string; label: string; format?: "datetime" }
  /** Download link for an uploaded attachment; `nameKey` is the response key holding its file name. */
  | { kind: "file-link"; key: string; label: string; nameKey?: string };

export type BadgeTone = "green" | "gray" | "amber" | "red";

export interface ListColumn {
  key: string;
  label: string;
  /** "badge" maps the raw value through `badges`; "datetime" formats an ISO timestamp. */
  kind?: "badge" | "datetime";
  badges?: Record<string, { label: string; tone: BadgeTone }>;
}

export interface EntityConfig {
  resource: string;
  title: string;
  addLabel?: string;
  /** Hides "add new": for records that only ever arrive from a public form (contact/application submissions). */
  noCreate?: boolean;
  listColumns: ListColumn[];
  fields: FieldSpec[];
  deleteConfirmField: string;
  /** Extra sentence in the delete confirmation: what ELSE disappears with this record. */
  deleteWarning?: string;
}

/** A stable React key / field-error lookup key for any FieldSpec variant. */
export function fieldKey(field: FieldSpec): string {
  if ("key" in field) return field.key;
  if ("base" in field) return field.base;
  return field.regionKey;
}
