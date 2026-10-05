import { useEffect, useState } from "react";
import { adminResource } from "@/api/admin";
import type { AdminMenuNode } from "../menuTypes";
import type { MenuNodeInput } from "@/api/adminMenu";

interface PageOption {
  id: number;
  slug: string;
  title_uz?: string;
}

interface Props {
  node: AdminMenuNode;
  /** The menu item this one sits under (null for a top-level section): the site groups a page's sidebar by it. */
  parentId: number | null;
  onSave: (input: MenuNodeInput) => Promise<void>;
  onClose: () => void;
}

export default function MenuNodeEditor({ node, parentId, onSave, onClose }: Props) {
  const [form, setForm] = useState<MenuNodeInput>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [pages, setPages] = useState<PageOption[]>([]);
  const [mode, setMode] = useState<"page" | "other">("other");

  useEffect(() => {
    adminResource<PageOption>("pages")
      .list({ pageSize: 200 })
      .then(({ items }) => setPages(items))
      .catch(() => setPages([]));
  }, []);

  useEffect(() => {
    setMode((node.urlValue ?? "").startsWith("/blog/") ? "page" : "other");
    setForm({
      title_uz: node.titleUz ?? "",
      title_ru: node.titleRu ?? "",
      title_en: node.titleEn ?? "",
      url_type: "other",
      url_value: node.urlValue ?? "",
    });
    setError("");
  }, [node]);

  function set<K extends keyof MenuNodeInput>(key: K, value: MenuNodeInput[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await onSave(form);
    } catch {
      setError("Saqlashda xatolik yuz berdi.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="bg-background-50 border border-background-200 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-foreground-900">Tahrirlash — #{node.id}</h2>
        <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-md text-foreground-400 hover:bg-background-200 cursor-pointer">
          <i className="ri-close-line" />
        </button>
      </div>

      {error && <div className="mb-3 p-2.5 rounded-md bg-accent-50 border border-accent-200 text-xs text-accent-800">{error}</div>}

      <form onSubmit={onSubmit} className="space-y-3">
        {(["uz", "ru", "en"] as const).map((lang) => (
          <div key={lang}>
            <label className="block text-xs font-semibold text-foreground-500 uppercase mb-1">Nomi ({lang})</label>
            <input
              value={(form[`title_${lang}`] as string) ?? ""}
              onChange={(e) => set(`title_${lang}`, e.target.value)}
              className="w-full h-10 px-3 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
            />
          </div>
        ))}

        <div>
          <span className="block text-xs font-semibold text-foreground-500 uppercase mb-1.5">Bu band qayerga olib borsin?</span>
          <div className="flex rounded-md border border-background-300 overflow-hidden mb-2">
            <button type="button" onClick={() => setMode("page")} className={`flex-1 text-xs px-2.5 py-2 cursor-pointer ${mode === "page" ? "bg-primary-500 text-background-50" : "text-foreground-600 hover:bg-background-100"}`}>
              Saytdagi sahifaga
            </button>
            <button type="button" onClick={() => setMode("other")} className={`flex-1 text-xs px-2.5 py-2 cursor-pointer ${mode === "other" ? "bg-primary-500 text-background-50" : "text-foreground-600 hover:bg-background-100"}`}>
              Boshqa manzilga
            </button>
          </div>

          {mode === "page" ? (
            <>
              <select
                value={pages.find((p) => (form.url_value ?? "").endsWith(`/${p.slug}`))?.slug ?? ""}
                onChange={(e) => e.target.value && set("url_value", `/blog/${parentId ?? node.id}/${e.target.value}`)}
                className="w-full h-10 px-3 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              >
                <option value="">Sahifani tanlang…</option>
                {pages.map((p) => (
                  <option key={p.id} value={p.slug}>{p.title_uz || p.slug}</option>
                ))}
              </select>
              <p className="mt-1.5 text-xs text-foreground-500">Ro'yxatda sahifa yo'q bo'lsa, avval «Sahifalar» bo'limida uni yarating.</p>
            </>
          ) : (
            <>
              <input
                value={form.url_value ?? ""}
                onChange={(e) => set("url_value", e.target.value)}
                placeholder="/yangiliklar  yoki  https://..."
                className="w-full h-10 px-3 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
              />
              <p className="mt-1.5 text-xs text-foreground-500">
                Saytning boshqa bo'limi uchun / bilan boshlang (masalan /yangiliklar, /aloqa), tashqi sayt uchun to'liq manzil (https://…). Faqat sarlavha bo'lib, hech qayerga olib bormasa «#» qoldiring.
              </p>
            </>
          )}
        </div>

        <button type="submit" disabled={saving} className="w-full h-10 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold cursor-pointer disabled:opacity-60">
          {saving ? "Saqlanmoqda..." : "Saqlash"}
        </button>
      </form>
    </div>
  );
}
