import type { ImentorSubjectStat } from "@/types/imentor";

/**
 * iMentor keeps every test question and clinical case in the language its author wrote it in, plus translations where
 * teachers (or iMentor's translator) added them. Its API takes `?language=` and then only returns what exists in that
 * language, so the site shows the visitor's language instead of a mix.
 */
export type ImentorLanguage = "uz" | "ru" | "en";

/** The site language as one of the three iMentor knows; anything else (e.g. "uz-Cyrl", "en-US") falls back sensibly. */
export function imentorLanguage(language?: string): ImentorLanguage {
  const code = (language || "uz").slice(0, 2).toLowerCase();
  return code === "ru" || code === "en" ? code : "uz";
}

/**
 * How many questions / cases a subject has in this language, or `undefined` when iMentor does not report languages
 * (an older answer): then the caller keeps the subject and its overall count.
 */
export function languageCount(subject: ImentorSubjectStat, language: ImentorLanguage): number | undefined {
  return subject.languages ? subject.languages[language] || 0 : undefined;
}

/** Only the subjects that have something in this language (all of them when languages are not reported). */
export function subjectsInLanguage(subjects: ImentorSubjectStat[], language: ImentorLanguage): ImentorSubjectStat[] {
  return subjects.filter((subject) => {
    const count = languageCount(subject, language);
    return count === undefined || count > 0;
  });
}
