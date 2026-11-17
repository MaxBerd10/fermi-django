import type { ImentorI18n, ImentorSubjectStat } from "@/types/imentor";

/**
 * iMentor sends the study programme, the year of study, the semester and the intake year of every subject as
 * separate fields (programme_code, course, semester, study_year, pure_title, ...), and the names of subjects and
 * departments in each language, so the pickers can go Yo'nalish -> Kurs -> Fan without reading anything out of free
 * text. A subject whose programme iMentor does not know lands in "other" / "no year" instead of being hidden.
 */

export interface ProgramInfo {
  /** stable key used in the address (?f=) */
  key: string;
  /** shown on the card, per language */
  name: { uz: string; ru: string; en: string };
  icon: string;
}

export const PROGRAMS: ProgramInfo[] = [
  { key: "davolash", name: { uz: "Davolash ishi", ru: "Лечебное дело", en: "General medicine" }, icon: "ri-stethoscope-line" },
  { key: "pediatriya", name: { uz: "Pediatriya ishi", ru: "Педиатрия", en: "Pediatrics" }, icon: "ri-heart-pulse-line" },
  { key: "profilaktika", name: { uz: "Tibbiy profilaktika ishi", ru: "Медико-профилактическое дело", en: "Medical prevention" }, icon: "ri-shield-cross-line" },
  { key: "stomatologiya", name: { uz: "Stomatologiya", ru: "Стоматология", en: "Dentistry" }, icon: "ri-hospital-line" },
  { key: "farmatsiya", name: { uz: "Farmatsiya", ru: "Фармация", en: "Pharmacy" }, icon: "ri-capsule-line" },
  { key: "hamshiralik", name: { uz: "Oliy hamshiralik ishi", ru: "Высшее сестринское дело", en: "Nursing" }, icon: "ri-user-heart-line" },
  { key: "fundamental", name: { uz: "Fundamental tibbiyot", ru: "Фундаментальная медицина", en: "Fundamental medicine" }, icon: "ri-microscope-line" },
  { key: "biologik", name: { uz: "Tibbiy biologik ish", ru: "Медико-биологическое дело", en: "Medical biology" }, icon: "ri-flask-line" },
  { key: "biotibbiyot", name: { uz: "Biotibbiyot muhandisligi", ru: "Биомедицинская инженерия", en: "Biomedical engineering" }, icon: "ri-cpu-line" },
  { key: "other", name: { uz: "Boshqa fanlar", ru: "Другие предметы", en: "Other subjects" }, icon: "ri-book-open-line" },
];

const PROGRAM_BY_KEY = new Map(PROGRAMS.map((program) => [program.key, program]));
export function programInfo(key: string): ProgramInfo {
  return PROGRAM_BY_KEY.get(key) ?? PROGRAM_BY_KEY.get("other")!;
}

/** iMentor's programme_code -> the key used in the address (?f=) and in PROGRAMS above */
const PROGRAM_KEY_BY_CODE: Record<string, string> = {
  davolash: "davolash",
  pediatriya: "pediatriya",
  "tibbiy-profilaktika": "profilaktika",
  stomatologiya: "stomatologiya",
  farmatsiya: "farmatsiya",
  "oliy-hamshiralik": "hamshiralik",
  "fundamental-tibbiyot": "fundamental",
  "tibbiy-biologik": "biologik",
  "biotibbiyot-muhandisligi": "biotibbiyot",
};

export interface ParsedSubject {
  program: string;
  /** year of study 1..6, or null when iMentor does not say */
  course: number | null;
  semester: number | null;
  /** the subject without programme / year / semester decorations, in the visitor's language */
  title: string;
  /** "2023-2024" */
  intake: string | null;
  /** "Milliy" / "Xorijiy" / ... in the visitor's language */
  track: string | null;
  /** the department's name in the visitor's language */
  department: string;
  /** the programme's name as iMentor writes it, in the visitor's language (null when none is sent) */
  programName: string | null;
}

const MAX_COURSE = 6;
type Lang = "uz" | "ru" | "en";

/** the text in the visitor's language; the answer already comes in that language, so the plain field is the fallback */
const pick = (texts: ImentorI18n | undefined, lang: Lang): string => (texts?.[lang] || "").trim();

export function subjectInfo(subject: ImentorSubjectStat, lang: Lang): ParsedSubject {
  const course = typeof subject.course === "number" && subject.course >= 1 && subject.course <= MAX_COURSE ? subject.course : null;
  return {
    program: PROGRAM_KEY_BY_CODE[subject.programme_code || ""] ?? "other",
    course,
    semester: typeof subject.semester === "number" ? subject.semester : null,
    title: pick(subject.pure_title_i18n, lang) || (subject.pure_title || "").trim() || pick(subject.subject_name_i18n, lang) || subject.subject_name,
    intake: subject.study_year?.trim() || null,
    track: pick(subject.track_i18n, lang) || null,
    department: pick(subject.department_name_i18n, lang) || subject.department_name || "",
    programName: pick(subject.programme_name_i18n, lang) || null,
  };
}

/** The subject's full name (title, programme, year, semester) in the visitor's language. */
export function subjectFullName(subject: ImentorSubjectStat, lang: Lang): string {
  return pick(subject.subject_name_i18n, lang) || subject.subject_name;
}

/** Every spelling of the subject's and department's name (all languages), so a search finds it however it is typed. */
export function subjectSearchTexts(subject: ImentorSubjectStat): string[] {
  const texts = [subject.subject_name, subject.department_name || "", subject.pure_title || ""];
  for (const group of [subject.subject_name_i18n, subject.department_name_i18n, subject.pure_title_i18n]) {
    if (group) texts.push(...Object.values(group).filter((text): text is string => Boolean(text)));
  }
  return texts;
}

export interface CatalogEntry<T> {
  item: T;
  parsed: ParsedSubject;
}

export function buildCatalog(subjects: ImentorSubjectStat[], lang: Lang): CatalogEntry<ImentorSubjectStat>[] {
  return subjects.map((item) => ({ item, parsed: subjectInfo(item, lang) }));
}

export const COURSES = [1, 2, 3, 4, 5, 6] as const;
