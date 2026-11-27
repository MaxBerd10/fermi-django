// Our own Django DB's id for the "Kafedralar" menu container -- not the old
// Yii2 site's id (which was 38 and matches nothing here; ids don't survive
// import). See the matching caveat on NAV_ROOT_THEMES in lib/menuSection.ts.
export const DEPARTMENT_MENU_ID = 1914;

export type DepartmentTheme =
  | "preventive"
  | "basic"
  | "clinical"
  | "social"
  | "tech"
  | "nursing";

