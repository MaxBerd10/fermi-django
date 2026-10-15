import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listUsers, deleteUser, type AdminUserItem } from "@/api/adminUsers";
import DataTable from "@/admin/components/DataTable";
import { useConfirm } from "@/admin/components/ConfirmDialog";
import ListToolbar from "@/admin/components/ListToolbar";
import PageHeader from "@/admin/components/PageHeader";
import Pagination from "@/admin/components/Pagination";
import { useAdminAuth } from "@/admin/AdminAuthContext";
import { ApiError } from "@/types/api";

const STATUS_LABELS: Record<number, string> = { 10: "Faol", 9: "Nofaol", 0: "O'chirilgan" };

export default function UserListPage() {
  const { user: currentUser } = useAdminAuth();
  const confirm = useConfirm();
  const [items, setItems] = useState<AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const pageSize = 20;

  async function load() {
    setLoading(true);
    try {
      const { items, meta } = await listUsers({ page, pageSize, search: search || undefined });
      setItems(items);
      setTotal(meta?.total ?? 0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load();
  }

  async function onDelete(item: AdminUserItem) {
    const ok = await confirm({
      title: `«${item.username}» hisobi o'chirilsinmi?`,
      message: "Bu odam admin panelga kira olmaydi. Qaytarib bo'lmaydi.",
      confirmLabel: "Ha, o'chirish",
      danger: true,
    });
    if (!ok) return;
    setError("");
    try {
      await deleteUser(item.id);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "O'chirishda xatolik yuz berdi.");
    }
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title="Foydalanuvchilar"
        actions={
          <Link to="/admin/users/new" className="flex h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600">
            <i className="ri-add-line" aria-hidden="true" /> Yangi foydalanuvchi
          </Link>
        }
      />

      {error && <div role="alert" className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">{error}</div>}

      <ListToolbar value={search} onChange={setSearch} onSubmit={onSearchSubmit} placeholder="Login yoki email bo'yicha qidirish..." total={total} loading={loading} />

      <DataTable
        columns={[
          { key: "id", label: "ID" },
          { key: "username", label: "Login" },
          { key: "email", label: "Email" },
          {
            key: "role",
            label: "Rol",
            render: (item) => (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${item.role === "admin" ? "bg-primary-100 text-primary-700" : "bg-background-200 text-foreground-600"}`}>
                {item.role === "admin" ? "Administrator" : "Foydalanuvchi"}
              </span>
            ),
          },
          { key: "status", label: "Holat", render: (item) => STATUS_LABELS[item.status] ?? item.status },
          { key: "createdAt", label: "Ro'yxatdan o'tgan" },
          {
            key: "self",
            label: "",
            render: (item) => (currentUser?.id === item.id ? <span className="text-xs text-primary-600 font-medium">(siz)</span> : ""),
          },
        ]}
        items={items}
        loading={loading}
        editPathFor={(item) => `/admin/users/${item.id}`}
        onDelete={onDelete}
      />
      <Pagination page={page} pageSize={pageSize} total={total} onChange={setPage} />
    </div>
  );
}
