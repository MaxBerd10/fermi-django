import { Link } from "react-router-dom";
import type { AdminPost } from "@/admin/types";
import DataTable from "@/admin/components/DataTable";
import Pagination from "@/admin/components/Pagination";
import { useAdminList } from "@/admin/hooks/useAdminList";
import { formatDateTime } from "@/admin/format";

export default function NewsListPage() {
  const list = useAdminList<AdminPost>("news");

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-2xl font-bold text-foreground-950">Yangiliklar</h1>
        <Link to="/admin/news/new" className="h-10 px-4 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold flex items-center gap-2 cursor-pointer">
          <i className="ri-add-line" /> Yangi qo'shish
        </Link>
      </div>

      <form onSubmit={list.submitSearch} className="mb-4 flex gap-2">
        <input
          value={list.searchInput}
          onChange={(e) => list.setSearchInput(e.target.value)}
          placeholder="Sarlavha bo'yicha qidirish..."
          className="w-full max-w-sm h-10 px-4 rounded-md border border-background-300 bg-background-50 text-sm focus:outline-none focus:border-primary-500"
        />
        <button type="submit" className="h-10 px-4 rounded-md border border-background-300 text-sm font-medium hover:bg-background-100 cursor-pointer">
          Qidirish
        </button>
      </form>

      {list.error && (
        <div role="alert" className="mb-4 p-3 rounded-md bg-accent-50 border border-accent-200 text-sm text-accent-800 flex items-center justify-between gap-3">
          <span>{list.error}</span>
          <button type="button" onClick={list.reload} className="shrink-0 underline cursor-pointer">Qayta urinish</button>
        </div>
      )}

      <DataTable
        columns={[
          { key: "id", label: "ID" },
          { key: "title_uz", label: "Sarlavha" },
          { key: "date", label: "Sana", render: (item) => formatDateTime(item.date) },
          { key: "seen", label: "Ko'rishlar" },
          {
            key: "status",
            label: "Holat",
            render: (item) => (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${item.status === 1 ? "bg-green-100 text-green-700" : "bg-background-200 text-foreground-500"}`}>
                {item.status === 1 ? "Faol" : "Nofaol"}
              </span>
            ),
          },
        ]}
        items={list.items}
        loading={list.loading}
        showEmpty={!list.error}
        editPathFor={(item) => `/admin/news/${item.id}`}
        onDelete={(item) => list.remove(item, item.title_uz)}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
