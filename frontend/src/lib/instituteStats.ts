import type { Counter } from "@/types/content";

/**
 * Institute-wide headline numbers (student count, professor count, etc.) —
 * the old backend's getHomeData() served these from a Yii2 "counter" row an
 * admin edited; Django has no equivalent model (and the admin CRUD panel
 * that would manage one is out of scope for this integration pass — see
 * frontend's git history). Hardcoded here rather than inventing a fake
 * endpoint that would just return the same static JSON. Override any of
 * these per-deployment via VITE_STAT_* without a code change.
 */
export const INSTITUTE_COUNTER: Counter = {
  professor_teachers: Number(import.meta.env.VITE_STAT_PROFESSORS) || 275,
  students: Number(import.meta.env.VITE_STAT_STUDENTS) || 6238,
  graduaters: Number(import.meta.env.VITE_STAT_GRADUATES) || 0,
  book_fund: Number(import.meta.env.VITE_STAT_BOOK_FUND) || 0,
};
