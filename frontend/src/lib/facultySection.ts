export type FacultyTheme = "clinical" | "preventive" | "international" | "pediatric";

export interface FacultyStat {
  icon: string;
  /** A raw display value (a number, a count) that's the same in every language. */
  value?: string;
  /** For a stat whose value is itself a word (a degree level, a focus area),
   * not a number -- translated the same way as labelKey, instead of showing
   * the same Uzbek word regardless of the selected language. */
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
      { icon: "ri-graduation-cap-line", value: "1 324", labelKey: "faculty.stats.students" },
      { icon: "ri-stethoscope-line", value: "1", labelKey: "faculty.stats.directions" },
      { icon: "ri-book-open-line", valueKey: "faculty.stats.value.bakalavriat", labelKey: "faculty.stats.level" },
    ],
  },
  "tibbiy-profilaktika-va-jamoat-salomatligi-fakulteti": {
    theme: "preventive",
    introKey: "faculty.intro.preventive",
    missionKey: "faculty.mission.preventive",
    stats: [
      { icon: "ri-graduation-cap-line", value: "707", labelKey: "faculty.stats.students" },
      { icon: "ri-route-line", value: "5", labelKey: "faculty.stats.directions" },
      { icon: "ri-heart-pulse-line", valueKey: "faculty.stats.value.js", labelKey: "faculty.stats.focus" },
    ],
  },
  "xalqaro-fakultet": {
    theme: "international",
    introKey: "faculty.intro.international",
    missionKey: "faculty.mission.international",
    stats: [
      { icon: "ri-graduation-cap-line", value: "1 504", labelKey: "faculty.stats.students" },
      { icon: "ri-global-line", value: "2", labelKey: "faculty.stats.languages" },
      { icon: "ri-earth-line", valueKey: "faculty.stats.value.xalqaro", labelKey: "faculty.stats.focus" },
    ],
  },
  "pediatriya-fakulteti": {
    theme: "pediatric",
    introKey: "faculty.intro.pediatric",
    missionKey: "faculty.mission.pediatric",
    stats: [
      { icon: "ri-graduation-cap-line", value: "693", labelKey: "faculty.stats.students" },
      { icon: "ri-route-line", value: "3", labelKey: "faculty.stats.directions" },
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
