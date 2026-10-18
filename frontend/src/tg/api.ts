import { initData } from "./bridge";

export interface Category {
  id: number;
  title: string;
}
export interface Me {
  registered: boolean;
  status: "pending" | "active" | "blocked" | null;
  full_name: string;
  department: string;
  is_approver: boolean;
  telegram_name: string;
  invited: boolean;
  categories: Category[];
  limits: { photos: number; files: number; per_day: number; sent_today: number; title: number; text: number };
}
export interface Submission {
  id: number;
  title: string;
  state: "pending" | "published" | "removed";
  url: string | null;
  photos: number;
  files: number;
  thumb: string | null;
  created_at: string;
}

export class AppError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** The server answers errors as {field: [messages]} or {detail: ...}: say the first one in plain words. */
function messageOf(body: unknown, fallback: string): string {
  if (body && typeof body === "object") {
    for (const value of Object.values(body as Record<string, unknown>)) {
      const first = Array.isArray(value) ? value[0] : value;
      if (typeof first === "string" && first) return first;
    }
  }
  return fallback;
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1/telegram/app/${path}`, {
      ...init,
      headers: { Authorization: `tma ${initData}`, ...(init.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}) },
    });
  } catch {
    throw new AppError("Internet aloqasi yo'q. Tekshirib, qayta urinib ko'ring.", 0);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) throw new AppError("Ilovani yopib, Telegramdan qayta oching.", 401);
    // a server that is down or busy answers in English from some proxy: say it in our words instead
    if (response.status === 429) throw new AppError("Juda ko'p so'rov yuborildi. Bir daqiqa kuting va qayta urining.", 429);
    if (response.status >= 500) throw new AppError("Server vaqtincha javob bermayapti. Birozdan keyin qayta urining.", response.status);
    throw new AppError(messageOf(body, "Xatolik yuz berdi. Qayta urinib ko'ring."), response.status);
  }
  return body as T;
}

export const getMe = () => call<Me>("me");
export const register = (full_name: string, department: string) => call<Me>("register", { method: "POST", body: JSON.stringify({ full_name, department }) });
export const getSubmissions = () => call<Submission[]>("submissions");
export const uploadPhoto = (file: Blob) => {
  const form = new FormData();
  form.append("file", file, "photo.jpg");
  return call<{ path: string; url: string }>("upload", { method: "POST", body: form });
};
/** A PDF / Word / Excel / PowerPoint file: kept under its own name (the server checks that it really is one). */
export const uploadDocument = (file: File) => {
  const form = new FormData();
  form.append("file", file, file.name);
  return call<{ path: string; url: string; title: string }>("upload", { method: "POST", body: form });
};
export const submitNews = (payload: { title: string; body: string; photos: string[]; files: { path: string; title: string }[]; category_id: number | null }) =>
  call<{ ok: boolean }>("submit", { method: "POST", body: JSON.stringify(payload) });
