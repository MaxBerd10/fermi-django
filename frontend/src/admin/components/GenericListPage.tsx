import { Link } from "react-router-dom";
import type { BadgeTone, EntityConfig, ListColumn } from "../genericTypes";
import { formatDateTime } from "../format";
import { useAdminList } from "../hooks/useAdminList";
import DataTable, { type Column } from "./DataTable";
import ListToolbar from "./ListToolbar";
import PageHeader from "./PageHeader";
import Pagination from "./Pagination";

interface Item {
  id: number;
  [key: string]: unknown;
}

const TONES: Record<BadgeTone, string> = {
  green: "bg-green-50 text-green-700 border-green-200",
  gray: "bg-background-100 text-foreground-600 border-background-300",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
  red: "bg-red-50 text-red-700 border-red-200",
};

// Default meaning of a bare `status` column (see entityConfigs.ts STATUS_OPTIONS).
const DEFAULT_STATUS_BADGES: NonNullable<ListColumn["badges"]> = {
  "1": { label: "Faol", tone: "green" },
  "0": { label: "Nofaol", tone: "gray" },
};

function toColumn(col: ListColumn): Column<Item> {
  const badges = col.badges ?? (col.key === "status" ? DEFAULT_STATUS_BADGES : undefined);
  if (col.kind === "datetime") {
    return { key: col.key, label: col.label, render: (item) => <span className="whitespace-nowrap">{formatDateTime(item[col.key])}</span> };
  }
  if (badges) {
    return {
      key: col.key,
      label: col.label,
      render: (item) => {
        const badge = badges[String(item[col.key])];
        if (!badge) return String(item[col.key] ?? "");
        return (
          <span className={`inline-block whitespace-nowrap px-2 py-0.5 rounded-full border text-xs font-medium ${TONES[badge.tone]}`}>
            {badge.label}
          </span>
        );
      },
    };
  }
  return { key: col.key, label: col.label };
}

export default function GenericListPage({ config }: { config: EntityConfig }) {
  const list = useAdminList<Item>(config.resource);

  return (
    <div className="mx-auto max-w-6xl">
      <PageHeader
        title={config.title}
        actions={
          !config.noCreate && (
            <Link
              to={`/admin/${config.resource}/new`}
              className="flex h-10 cursor-pointer items-center gap-2 rounded-lg bg-primary-500 px-4 text-sm font-semibold text-background-50 hover:bg-primary-600"
            >
              <i className="ri-add-line" aria-hidden="true" /> {config.addLabel ?? "Yangi qo'shish"}
            </Link>
          )
        }
      />

      <ListToolbar value={list.searchInput} onChange={list.setSearchInput} onSubmit={list.submitSearch} total={list.error ? undefined : list.total} loading={list.loading} />

      {list.error && (
        <div role="alert" className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800 flex items-center justify-between gap-3">
          <span>{list.error}</span>
          <button type="button" onClick={list.reload} className="shrink-0 underline cursor-pointer">Qayta urinish</button>
        </div>
      )}

      <DataTable
        columns={config.listColumns.map(toColumn)}
        items={list.items}
        loading={list.loading}
        showEmpty={!list.error}
        editPathFor={(item) => `/admin/${config.resource}/${item.id}`}
        onDelete={(item) => list.remove(item, String(item[config.deleteConfirmField] ?? item.id), config.deleteWarning)}
        isUnread={config.inbox ? (item) => Number(item.status) === 1 : undefined}
        emptyText={config.inbox ? "Hali murojaat kelmagan." : undefined}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
