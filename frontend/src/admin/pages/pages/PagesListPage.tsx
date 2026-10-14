import { Link } from "react-router-dom";
import type { AdminPage } from "@/admin/types";
import DataTable from "@/admin/components/DataTable";
import ListToolbar from "@/admin/components/ListToolbar";
import PageHeader from "@/admin/components/PageHeader";
import Pagination from "@/admin/components/Pagination";
import { useAdminList } from "@/admin/hooks/useAdminList";

export default function PagesListPage() {
  const list = useAdminList<AdminPage>("pages");

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Sahifalar"
        actions={
          <Link to="/admin/pages/new" className="flex h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600">
            <i className="ri-add-line" aria-hidden="true" /> Sahifa qo'shish
          </Link>
        }
      />

      <ListToolbar
        value={list.searchInput}
        onChange={list.setSearchInput}
        onSubmit={list.submitSearch}
        placeholder="Sarlavha, menyudagi nom yoki manzil bo'yicha qidirish..."
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
          // Pages imported from the old site have no title of their own (it lives on the menu item that links to
          // them): show that menu name, or the slug when no menu entry points here.
          {
            key: "title_uz",
            label: "Sarlavha",
            render: (item) =>
              item.title_uz || item.menu_title || <span className="text-foreground-400">{item.slug}</span>,
          },
          { key: "slug", label: "Manzil (slug)" },
          { key: "korish", label: "Ko'rishlar" },
          {
            key: "status",
            label: "Holat",
            render: (item) => (
              <span className={`inline-block whitespace-nowrap px-2 py-0.5 rounded-full border text-xs font-medium ${item.status === 1 ? "border-green-200 bg-green-50 text-green-700" : "border-background-300 bg-background-100 text-foreground-500"}`}>
                {item.status === 1 ? "Faol" : "Nofaol"}
              </span>
            ),
          },
        ]}
        items={list.items}
        loading={list.loading}
        showEmpty={!list.error}
        emptyText={list.searchInput ? "Bunday sahifa topilmadi." : undefined}
        editPathFor={(item) => `/admin/pages/${item.id}`}
        onDelete={(item) => list.remove(item, item.title_uz || item.slug, "Agar bu sahifa menyuda bo'lsa, menyudagi havola \"topilmadi\" xatosini beradi. Avval Menyu daraxtidan olib tashlang.")}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
