import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminResource } from "@/api/admin";
import type { AdminPost, AdminPostcategory } from "@/admin/types";
import DataTable from "@/admin/components/DataTable";
import ListToolbar from "@/admin/components/ListToolbar";
import PageHeader from "@/admin/components/PageHeader";
import Pagination from "@/admin/components/Pagination";
import { useAdminList } from "@/admin/hooks/useAdminList";
import { formatDateTime } from "@/admin/format";

const STATUS_FILTERS = [
  { value: "", label: "Hammasi" },
  { value: "1", label: "E'lon qilingan" },
  { value: "0", label: "Qoralama" },
];

export default function NewsListPage() {
  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState<AdminPostcategory[]>([]);
  const filters: Record<string, string> = {};
  if (status) filters.status = status;
  if (category) filters.category = category;
  const list = useAdminList<AdminPost>("news", 20, filters);

  useEffect(() => {
    adminResource<AdminPostcategory>("postcategories")
      .list({ pageSize: 100 })
      .then((r) => setCategories(r.items))
      .catch(() => setCategories([]));
  }, []);

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Yangiliklar"
        actions={
          <Link to="/admin/news/new" className="flex h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600">
            <i className="ri-add-line" aria-hidden="true" /> Yangilik qo'shish
          </Link>
        }
      />

      <ListToolbar
        value={list.searchInput}
        onChange={list.setSearchInput}
        onSubmit={list.submitSearch}
        placeholder="Sarlavha bo'yicha qidirish..."
        total={list.error ? undefined : list.total}
        loading={list.loading}
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div role="group" aria-label="Holat bo'yicha" className="inline-flex rounded-lg border border-background-300 bg-background-100 p-1">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setStatus(f.value)}
              aria-pressed={status === f.value}
              className={`h-9 cursor-pointer whitespace-nowrap rounded-md px-3 text-sm font-medium ${
                status === f.value ? "bg-background-50 text-primary-700 shadow-sm" : "text-foreground-500 hover:text-foreground-800"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        {categories.length > 0 && (
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            aria-label="Kategoriya bo'yicha"
            className="h-11 rounded-lg border border-background-300 bg-background-50 px-3 text-sm focus:border-primary-500 focus:outline-none"
          >
            <option value="">Barcha kategoriyalar</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.title_uz}</option>
            ))}
          </select>
        )}
      </div>

      {list.error && (
        <div role="alert" className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800 flex items-center justify-between gap-3">
          <span>{list.error}</span>
          <button type="button" onClick={list.reload} className="shrink-0 underline cursor-pointer">Qayta urinish</button>
        </div>
      )}

      <DataTable
        columns={[
          { key: "title_uz", label: "Sarlavha" },
          { key: "date", label: "Sana", render: (item) => <span className="whitespace-nowrap">{formatDateTime(item.date)}</span> },
          { key: "seen", label: "Ko'rishlar" },
          {
            key: "status",
            label: "Holat",
            render: (item) => (
              <span className={`inline-block whitespace-nowrap px-2 py-0.5 rounded-full border text-xs font-medium ${item.status === 1 ? "border-green-200 bg-green-50 text-green-700" : "border-amber-200 bg-amber-50 text-amber-800"}`}>
                {item.status === 1 ? "E'lon qilingan" : "Qoralama"}
              </span>
            ),
          },
        ]}
        items={list.items}
        loading={list.loading}
        showEmpty={!list.error}
        emptyText={list.searchInput || status || category ? "Bunday yangilik topilmadi." : "Hali yangilik qo'shilmagan."}
        editPathFor={(item) => `/admin/news/${item.id}`}
        onDelete={(item) => list.remove(item, item.title_uz, "Yangilik saytdan butunlay o'chadi. Vaqtincha yashirmoqchi bo'lsangiz, o'chirmang: yangilikni oching va \"Holat\" ni \"Qoralama\" qiling.")}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
