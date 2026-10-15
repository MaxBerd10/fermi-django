import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createMenuNode, getMenuTree } from "@/api/adminMenu";
import type { AdminMenuNode } from "@/admin/menuTypes";
import { adminErrorMessage } from "../hooks/useAdminList";
import { useToast } from "./Toast";

interface Place {
  id: number;
  path: string;
}

interface ParentOption {
  id: number;
  label: string;
}

const MAX_DEPTH = 2; // sections and their sub-sections: deeper entries are too many to pick from a list

function walk(nodes: AdminMenuNode[], slug: string, trail: string[], places: Place[], parents: ParentOption[]) {
  for (const node of nodes) {
    const path = [...trail, node.titleUz];
    if ((node.urlValue ?? "").split(/[?#]/)[0].replace(/\/$/, "").endsWith(`/${slug}`)) places.push({ id: node.id, path: path.join(" › ") });
    if (trail.length < MAX_DEPTH) parents.push({ id: node.id, label: path.join(" › ") });
    walk(node.children, slug, path, places, parents);
  }
}

interface Props {
  slug: string;
  title: string;
  titleRu?: string | null;
  titleEn?: string | null;
  /** The page was created a moment ago: say loudly that it is not on the site yet. */
  justCreated?: boolean;
}

/** "Where does this page appear on the site?" A page is reachable only through the menu (or by its direct address):
 *  this shows where it is linked now, and lets the editor add it to a menu section with one click. */
export default function PagePlacement({ slug, title, titleRu, titleEn, justCreated }: Props) {
  const toast = useToast();
  const [places, setPlaces] = useState<Place[] | null>(null);
  const [parents, setParents] = useState<ParentOption[]>([]);
  const [error, setError] = useState("");
  const [parentId, setParentId] = useState("");
  const [label, setLabel] = useState(title);
  const [adding, setAdding] = useState(false);

  const load = useCallback(() => {
    getMenuTree()
      .then((tree) => {
        const found: Place[] = [];
        const options: ParentOption[] = [];
        walk(tree, slug, [], found, options);
        setPlaces(found);
        setParents(options);
        setError("");
      })
      .catch((err) => setError(adminErrorMessage(err, "Menyuni yuklab bo'lmadi.")));
  }, [slug]);

  useEffect(load, [load]);
  useEffect(() => setLabel(title), [title]);

  async function onAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!parentId || !label.trim()) return;
    setAdding(true);
    try {
      await createMenuNode({
        parentId: Number(parentId),
        title_uz: label.trim(),
        title_ru: titleRu?.trim() || label.trim(),
        title_en: titleEn?.trim() || label.trim(),
        url_type: "other",
        url_value: `/blog/${parentId}/${slug}`,
        status: 1,
        active: 1,
        disabled: 0,
      });
      toast.success("Menyuga qo'shildi. Saytda ko'rinadi.");
      load();
    } catch (err) {
      toast.error(adminErrorMessage(err, "Menyuga qo'shib bo'lmadi."));
    } finally {
      setAdding(false);
    }
  }

  const address = `/blog/0/${slug}`;
  const inMenu = places !== null && places.length > 0;

  return (
    <section
      className={`mb-4 rounded-xl border p-4 sm:p-5 ${
        places !== null && !inMenu ? "border-amber-300 bg-amber-50" : "border-background-200 bg-background-50"
      }`}
    >
      <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-foreground-500">
        <i className="ri-map-pin-line" aria-hidden="true" /> Saytda qayerda ko'rinadi?
      </h2>

      {error && <p className="text-sm text-red-700">{error}</p>}
      {places === null && !error && <p className="text-sm text-foreground-500">Tekshirilmoqda...</p>}

      {inMenu && (
        <div className="space-y-2 text-sm">
          {places.map((place) => (
            <p key={place.id} className="flex items-start gap-2 text-foreground-800">
              <i className="ri-checkbox-circle-line mt-0.5 text-green-600" aria-hidden="true" />
              <span>Menyuda: <b>{place.path}</b></span>
            </p>
          ))}
          <p className="text-foreground-500">
            O'rnini o'zgartirish yoki olib tashlash uchun <Link to="/admin/menu-tree" className="font-medium text-primary-600 underline">Menyu daraxti</Link>ga o'ting.
          </p>
        </div>
      )}

      {places !== null && !inMenu && (
        <div className="space-y-3 text-sm text-amber-900">
          <p className="flex items-start gap-2">
            <i className="ri-error-warning-line mt-0.5 text-lg text-amber-600" aria-hidden="true" />
            <span>
              {justCreated ? <b>Sahifa saqlandi, lekin hali saytda hech qayerda ko'rinmaydi. </b> : <b>Bu sahifa menyuda yo'q. </b>}
              Menyuga qo'shilmaguncha uni faqat to'g'ridan-to'g'ri manzil orqali ochish mumkin.
            </span>
          </p>
          <form onSubmit={onAdd} className="grid gap-3 rounded-lg bg-background-50 p-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-foreground-600">Qaysi bo'limga qo'shamiz?</span>
              <select
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
                required
                className="h-11 w-full rounded-lg border border-background-300 bg-background-50 px-3 text-sm text-foreground-900 focus:border-primary-500 focus:outline-none"
              >
                <option value="">Tanlang...</option>
                {parents.map((p) => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-foreground-600">Menyudagi nomi</span>
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                required
                className="h-11 w-full rounded-lg border border-background-300 bg-background-50 px-3 text-sm text-foreground-900 focus:border-primary-500 focus:outline-none"
              />
            </label>
            <button
              type="submit"
              disabled={adding || !parentId}
              className="h-11 cursor-pointer rounded-lg bg-primary-500 px-5 text-sm font-semibold text-background-50 hover:bg-primary-600 disabled:opacity-60"
            >
              {adding ? "Qo'shilmoqda..." : "Menyuga qo'shish"}
            </button>
          </form>
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-background-200/70 pt-3 text-xs text-foreground-500">
        <span>To'g'ridan-to'g'ri manzil:</span>
        <code className="rounded bg-background-200 px-1.5 py-0.5 text-foreground-700">fermi.uz{address}</code>
        <a href={address} target="_blank" rel="noreferrer" className="font-medium text-primary-600 hover:underline">
          Saytda ochish
        </a>
      </div>
    </section>
  );
}
