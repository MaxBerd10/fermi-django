/**
 * iMentor groups tests and cases by department (kafedra) and subject only. A faculty / study programme and a
 * year of study are not separate fields there: the teachers type them into the subject name
 * ("Davolash ishi 2023-2024 (Milliy) 5-semestr Patologik fiziologiya", "Yuqumli kasalliklar 9-s DI",
 * "TPI Falsafa 3 sm"). This reads them back out, so the pickers can go Yo'nalish -> Kurs -> Fan.
 *
 * It is a best-effort reading of free text: a name it cannot place lands in "other" / "no year" instead of
 * being hidden. When iMentor starts returning real faculty / course fields, replace `parseSubjectName` with
 * them -- nothing else in the pickers needs to change.
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
  { key: "xalqaro", name: { uz: "Xalqaro fakultet", ru: "Международный факультет", en: "International faculty" }, icon: "ri-global-line" },
  { key: "biotibbiyot", name: { uz: "Biotibbiyot muhandisligi", ru: "Биомедицинская инженерия", en: "Biomedical engineering" }, icon: "ri-cpu-line" },
  { key: "other", name: { uz: "Boshqa fanlar", ru: "Другие предметы", en: "Other subjects" }, icon: "ri-book-open-line" },
];

const PROGRAM_BY_KEY = new Map(PROGRAMS.map((program) => [program.key, program]));
export function programInfo(key: string): ProgramInfo {
  return PROGRAM_BY_KEY.get(key) ?? PROGRAM_BY_KEY.get("other")!;
}

/** The programme named in full at the start of the subject ("Davolash ishi 2023-2024 ..."). */
const LEADING_PROGRAM: Array<[RegExp, string]> = [
  [/^davolash ishi\b/i, "davolash"],
  [/^pediatriya ishi\b/i, "pediatriya"],
  [/^tibbiy profilaktika ishi\b/i, "profilaktika"],
  [/^stomatologiya\s+(?:\d{4}|\d{1,2}\s*-?\s*s\b)/i, "stomatologiya"],
  [/^farmatsiya\s+\d{4}/i, "farmatsiya"],
  [/^oliy hamshiralik ishi\b/i, "hamshiralik"],
  [/^fundamental tibbiyot\b/i, "fundamental"],
  [/^tibbiy biologik ish/i, "biologik"],
];

/** Short programme codes teachers append or prepend ("... 9-s DI", "TPI Falsafa 3 sm"); case matters, they are upper-case. */
const PROGRAM_CODES: Array<[RegExp, string]> = [
  [/(?:\b|(?<=[a-z]))TPI\b/, "profilaktika"],
  [/(?:\b|(?<=[a-z]))OHI\b/, "hamshiralik"],
  [/\b(?:FT|TBI)\b/, "fundamental"],
  [/\b(?:PED|Ped|PI)\b/, "pediatriya"],
  [/\b(?:STOM|Stom)\b/, "stomatologiya"],
  [/\b(?:FARM)\b/, "farmatsiya"],
  [/\b(?:BM)\b/, "biotibbiyot"],
  [/\b(?:DI)\b/, "davolash"],
];

export interface ParsedSubject {
  program: string;
  /** year of study 1..6, or null when the name does not say */
  course: number | null;
  semester: number | null;
  /** the subject without programme / year / semester decorations */
  title: string;
  /** "2023-2024" */
  intake: string | null;
  /** "Milliy" / "Xorijiy" / ... */
  track: string | null;
}

const MAX_COURSE = 6;

function courseFromSemester(semester: number): number | null {
  const course = Math.ceil(semester / 2);
  return course >= 1 && course <= MAX_COURSE ? course : null;
}

export function parseSubjectName(rawName: string): ParsedSubject {
  const name = rawName.replace(/\s+/g, " ").trim();

  let program = "other";
  for (const [pattern, key] of LEADING_PROGRAM) {
    if (pattern.test(name)) {
      program = key;
      break;
    }
  }
  if (program === "other") {
    for (const [pattern, key] of PROGRAM_CODES) {
      if (pattern.test(name)) {
        program = key;
        break;
      }
    }
  }
  if (program === "other" && /\bdavolash\b/i.test(name)) program = "davolash";
  if (program === "other" && /\bfundamental tibbiyot\b/i.test(name)) program = "fundamental";
  if (program === "other" && /\(xalqaro\)/i.test(name)) program = "xalqaro";

  // "4-kurs" / "1k" says the year of study directly; otherwise it follows from the semester
  let course: number | null = null;
  const explicitCourse = /(?<!\d)([1-6])\s*-?\s*kurs\b/i.exec(name);
  if (explicitCourse) course = Number(explicitCourse[1]);

  // "5-semestr", "9-s", "3 sm", "2sm", "11 sm", "5s"; not part of a year ("2023-2024") or a group number
  const semesterMatch = /(?<![\d-])(\d{1,2})(?:\s*-\s*\d{1,2}(?=\s*-?\s*semestr))?\s*-?\s*(?:semestr|sem|sm|s)(?![a-zA-Z])/i.exec(name);
  const semester = semesterMatch ? Number(semesterMatch[1]) : null;
  if (course === null && semester !== null) course = courseFromSemester(semester);
  if (course === null) {
    const oneK = /(?<!\d)([1-6])\s*k\b/i.exec(name);
    if (oneK) course = Number(oneK[1]);
  }

  const intake = /\b(20\d{2})\s*[-\s]\s*(20\d{2})\b/.exec(name);
  const singleYear = intake ? null : /^(?:davolash ishi|pediatriya ishi|tibbiy profilaktika ishi)\s+(20\d{2})\b/i.exec(name);
  const trackMatch = /\((milliy|xorijiy|yevro|gibrid)[^)]*\)|\b(milliy|xorijiy)\b/i.exec(name);

  let title = name
    .replace(/\((?:milliy|xorijiy|yevro|gibrid|xalqaro)[^)]*\)/gi, " ")
    .replace(/\b(?:milliy|xorijiy|gibrid)\b/gi, " ")
    .replace(/\b(?:\d{3}-\d{3,4})\b/g, " ")
    .replace(/\b20\d{2}\s*[-\s]\s*20\d{2}\b/g, " ")
    .replace(/(?<!\d)\d{1,2}(?:\s*-\s*\d{1,2}(?=\s*-?\s*semestr))?\s*-?\s*(?:semestr|sem|sm|s)(?![a-zA-Z])\.?/gi, " ")
    .replace(/(?<!\d)[1-6]\s*-?\s*kurs\b/gi, " ")
    .replace(/(?<!\d)\d\s*k\b/gi, " ")
    .replace(/([a-z])(?:TPI|OHI)\b/g, "$1");
  title = title.replace(/^(?:davolash ishi|pediatriya ishi|tibbiy profilaktika ishi|oliy hamshiralik ishi|fundamental tibbiyot|tibbiy biologik ishi?)\b/i, " ");
  title = title.replace(/^\s*20\d{2}\b/, " ");
  title = title.replace(/^(?:stomatologiya|farmatsiya)\s+(?=[^\s])/i, (m) => (program === "stomatologiya" || program === "farmatsiya" ? " " : m));
  // programme codes at either end ("BM Dinshunoslik", "... 9-s DI", "... 5-s FT+TBI", "... (DI)")
  title = title
    .replace(/\((?:PED|PI|STOM|FARM|BM|DI|TPI|FT|OHI|TBI)\)/g, " ")
    .replace(/^(?:\s*(?:PED|Ped-?|STOM|FARM|BM|DI|TPI|FT|OHI|PI)\b[\s-]*)+/, " ")
    .replace(/(?:[\s,.]*\b(?:TPI|OHI|FT|TBI|PED|PI|STOM|Stom|DI|BM)\b(?:\s*\+\s*(?:TPI|OHI|FT|TBI|PED|PI|STOM|DI|BM))*)+\s*$/g, " ")
    .replace(/\(\s*\)/g, " ")
    .replace(/\s+[,.;-]+\s*$/g, " ")
    .replace(/^[\s,.;:-]+|[\s,.;:-]+$/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!title) title = name;
  title = title.charAt(0).toUpperCase() + title.slice(1);

  return {
    program,
    course,
    semester,
    title,
    intake: intake ? `${intake[1]}-${intake[2]}` : singleYear ? singleYear[1] : null,
    track: trackMatch ? (trackMatch[1] || trackMatch[2]).replace(/^./, (c) => c.toUpperCase()) : null,
  };
}

export interface CatalogEntry<T> {
  item: T;
  parsed: ParsedSubject;
}

export function buildCatalog<T extends { subject_name: string }>(subjects: T[]): CatalogEntry<T>[] {
  return subjects.map((item) => ({ item, parsed: parseSubjectName(item.subject_name) }));
}

export const COURSES = [1, 2, 3, 4, 5, 6] as const;
