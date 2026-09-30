import { apiClient } from "./client";
import type { ApiMeta } from "../types/api";

export interface AdminListResult<T> {
  items: T[];
  meta?: ApiMeta;
}

export interface AdminListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  [key: string]: string | number | undefined;
}

/** Generic CRUD bound to one /v1/admin/<resource> endpoint (see api/controllers/BaseAdminController.php). */
export function adminResource<T extends { id: number }>(resource: string) {
  return {
    list: async (params?: AdminListParams): Promise<AdminListResult<T>> => {
      const { data, meta } = await apiClient.get<T[]>(`admin/${resource}`, params, true);
      return { items: data, meta };
    },
    get: async (id: number): Promise<T> => {
      const { data } = await apiClient.get<T>(`admin/${resource}/${id}`, undefined, true);
      return data;
    },
    create: async (payload: Partial<T>): Promise<T> => {
      const { data } = await apiClient.post<T>(`admin/${resource}`, payload, true);
      return data;
    },
    update: async (id: number, payload: Partial<T>): Promise<T> => {
      const { data } = await apiClient.put<T>(`admin/${resource}/${id}`, payload, true);
      return data;
    },
    remove: async (id: number): Promise<void> => {
      await apiClient.del(`admin/${resource}/${id}`, true);
    },
  };
}

export interface UploadResult {
  path: string;
  url: string;
}

export async function uploadMedia(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.postForm<UploadResult>("admin/media/upload", formData, true);
  return data;
}

/** Browser-loadable URL for a media field's value: absolute URLs pass through,
 * bare storage paths ("uploads/admin/a.jpg", what an upload returns) resolve
 * under the same-origin /media/ that Vite and production-server.mjs proxy to Django. */
export function mediaUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  if (/^(https?:)?\/\//.test(value) || value.startsWith("data:") || value.startsWith("blob:")) return value;
  return "/media/" + value.replace(/^\/+/, "").replace(/^media\//, "");
}

export type TranslationLang = "uz" | "ru" | "en";

/** Machine-translates a set of named strings (plain text or editor HTML) — see apps/admin_api/translate_views.py. */
export async function translateTexts<K extends string>(
  texts: Record<K, string>,
  targets: TranslationLang[] = ["ru", "en"],
  source: TranslationLang = "uz",
): Promise<Partial<Record<TranslationLang, Record<K, string>>>> {
  // A list rather than a {ru, en} map, so the shape survives resolveLocale
  // even if this ever stops being treated as a raw admin/* response.
  const { data } = await apiClient.post<{ translations: { lang: TranslationLang; texts: Record<K, string> }[] }>(
    "admin/translate",
    { source, targets, texts },
    true,
  );
  return Object.fromEntries(data.translations.map((t) => [t.lang, t.texts]));
}
