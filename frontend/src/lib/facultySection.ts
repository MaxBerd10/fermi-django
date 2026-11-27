export type FacultyTheme = "clinical" | "preventive" | "international" | "pediatric";

export interface FacultyStat {
  icon: string;
  /** A raw display value that is the same in every language (no stat of the four faculties uses one any more). */
  value?: string;
  /** The text key of the value: a number (students, directions) or a word (a degree level, a focus area). Every value is a Sayt matnlari key
   * ("Fakultet sahifasi"), so the numbers are edited in the admin, not in the code. */
  valueKey?: string;
  labelKey: string;
}

export interface FacultyPageConfig {
  theme: FacultyTheme;
  introKey: string;
  missionKey?: string;
  stats: FacultyStat[];
}

// Our own Django DB's id for the "Fakultetlar" menu container -- not the
// old Yii2 site's id (37). See lib/menuSection.ts's NAV_ROOT_THEMES comment.
export const FACULTY_MENU_ID = 1909;

export const FACULTY_PAGE_CONFIG: Record<string, FacultyPageConfig> = {
  "davolash-ishi": {
    theme: "clinical",
    introKey: "faculty.intro.davolash",
    missionKey: "faculty.mission.davolash",
    stats: [
      { icon: "ri-graduation-cap-line", valueKey: "faculty.stats.davolash.students", labelKey: "faculty.stats.students" },
      { icon: "ri-stethoscope-line", valueKey: "faculty.stats.davolash.directions", labelKey: "faculty.stats.directions" },
      { icon: "ri-book-open-line", valueKey: "faculty.stats.value.bakalavriat", labelKey: "faculty.stats.level" },
    ],
  },
  "tibbiy-profilaktika-va-jamoat-salomatligi-fakulteti": {
    theme: "preventive",
    introKey: "faculty.intro.preventive",
    missionKey: "faculty.mission.preventive",
    stats: [
      { icon: "ri-graduation-cap-line", valueKey: "faculty.stats.preventive.students", labelKey: "faculty.stats.students" },
      { icon: "ri-route-line", valueKey: "faculty.stats.preventive.directions", labelKey: "faculty.stats.directions" },
    ],
  },
  "xalqaro-fakultet": {
    theme: "international",
    introKey: "faculty.intro.international",
    missionKey: "faculty.mission.international",
    stats: [
      { icon: "ri-graduation-cap-line", valueKey: "faculty.stats.international.students", labelKey: "faculty.stats.students" },
      { icon: "ri-global-line", valueKey: "faculty.stats.international.languages", labelKey: "faculty.stats.languages" },
      { icon: "ri-earth-line", valueKey: "faculty.stats.value.xalqaro", labelKey: "faculty.stats.focus" },
    ],
  },
  "pediatriya-fakulteti": {
    theme: "pediatric",
    introKey: "faculty.intro.pediatric",
    missionKey: "faculty.mission.pediatric",
    stats: [
      { icon: "ri-graduation-cap-line", valueKey: "faculty.stats.pediatric.students", labelKey: "faculty.stats.students" },
      { icon: "ri-route-line", valueKey: "faculty.stats.pediatric.directions", labelKey: "faculty.stats.directions" },
      { icon: "ri-emotion-happy-line", valueKey: "faculty.stats.value.pediatriya", labelKey: "faculty.stats.focus" },
    ],
  },
};

export function getFacultyPageConfig(slug: string): FacultyPageConfig {
  return (
    FACULTY_PAGE_CONFIG[slug] ?? {
      theme: "clinical",
      introKey: "section.intro.fakultetlar",
      stats: [],
    }
  );
}
