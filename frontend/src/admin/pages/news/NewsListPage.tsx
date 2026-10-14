import { Link } from "react-router-dom";
import type { AdminPost } from "@/admin/types";
import DataTable from "@/admin/components/DataTable";
import ListToolbar from "@/admin/components/ListToolbar";
import PageHeader from "@/admin/components/PageHeader";
import Pagination from "@/admin/components/Pagination";
import { useAdminList } from "@/admin/hooks/useAdminList";
import { formatDateTime } from "@/admin/format";

export default function NewsListPage() {
  const list = useAdminList<AdminPost>("news");

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
        emptyText={list.searchInput ? "Bunday yangilik topilmadi." : "Hali yangilik qo'shilmagan."}
        editPathFor={(item) => `/admin/news/${item.id}`}
        onDelete={(item) => list.remove(item, item.title_uz, "Yangilik saytdan butunlay o'chadi. Vaqtincha yashirmoqchi bo'lsangiz, o'chirmang: yangilikni oching va \"Holat\" ni \"Qoralama\" qiling.")}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
