import { useLanguage } from "../i18n/LanguageContext";
import type { Lang } from "../types";

const LANGS: { code: Lang; label: string }[] = [
  { code: "uz", label: "UZ" },
  { code: "ru", label: "RU" },
  { code: "en", label: "EN" },
];

export function LanguageSwitcher() {
  const { lang, setLang } = useLanguage();
  return (
    <div className="flex gap-1">
      {LANGS.map((l) => (
        <button
          key={l.code}
          onClick={() => setLang(l.code)}
          className={`rounded-full px-2.5 py-1 text-xs font-bold transition-colors ${
            lang === l.code ? "bg-primary-900 text-white" : "bg-primary-50 text-primary-700 hover:bg-primary-100"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
