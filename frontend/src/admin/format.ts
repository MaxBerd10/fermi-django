/** "24.09.2026, 12:00" in the institute's own timezone, whatever the admin's browser is set to. */
export function formatDateTime(value: unknown): string {
  if (!value) return "";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("ru-RU", { timeZone: "Asia/Tashkent", dateStyle: "short", timeStyle: "short" });
}

// Uzbekistan has no daylight saving: Asia/Tashkent is a fixed UTC+5.
const TASHKENT_OFFSET = "+05:00";

/** ISO timestamp -> the "YYYY-MM-DDTHH:mm" a <input type=datetime-local> wants, in Tashkent time. */
export function toTashkentInput(value: unknown): string {
  if (!value) return "";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "";
  const parts = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Tashkent",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).format(date);
  return parts.replace(" ", "T");
}

/** The inverse: a datetime-local value (Tashkent wall-clock time) -> ISO with the explicit offset. */
export function fromTashkentInput(local: string): string {
  return `${local}:00${TASHKENT_OFFSET}`;
}
