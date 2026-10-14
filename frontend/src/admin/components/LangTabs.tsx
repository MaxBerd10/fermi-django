export type Lang = "uz" | "ru" | "en";

export const LANGS: { key: Lang; label: string; full: string }[] = [
  { key: "uz", label: "UZ", full: "O'zbekcha" },
  { key: "ru", label: "RU", full: "Ruscha" },
  { key: "en", label: "EN", full: "Inglizcha" },
];

interface Props {
  value: Lang;
  onChange: (lang: Lang) => void;
  /** Which languages already have text: a filled one shows a green dot, an empty one a grey ring. */
  filled?: Partial<Record<Lang, boolean>>;
  /** Languages with a validation error get a red dot. */
  invalid?: Partial<Record<Lang, boolean>>;
  className?: string;
}

/** The UZ / RU / EN switch above a form: one language at a time instead of three long blocks stacked. */
export default function LangTabs({ value, onChange, filled, invalid, className = "" }: Props) {
  return (
    <div role="tablist" aria-label="Til" className={`inline-flex rounded-lg border border-background-300 bg-background-100 p-1 ${className}`}>
      {LANGS.map((lang) => {
        const active = lang.key === value;
        return (
          <button
            key={lang.key}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(lang.key)}
            title={lang.full}
            className={`flex h-9 cursor-pointer items-center gap-2 rounded-md px-4 text-sm font-semibold transition-colors ${
              active ? "bg-background-50 text-primary-700 shadow-sm" : "text-foreground-500 hover:text-foreground-800"
            }`}
          >
            {lang.label}
            <span
              aria-hidden="true"
              className={`h-2 w-2 rounded-full ${
                invalid?.[lang.key] ? "bg-red-500" : filled?.[lang.key] ? "bg-green-500" : "border border-background-500 bg-transparent"
              }`}
            />
            <span className="sr-only">{invalid?.[lang.key] ? "(xatolik bor)" : filled?.[lang.key] ? "(to'ldirilgan)" : "(bo'sh)"}</span>
          </button>
        );
      })}
    </div>
  );
}
