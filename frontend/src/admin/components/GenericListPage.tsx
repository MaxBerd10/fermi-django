import { Link } from "react-router-dom";
import type { BadgeTone, EntityConfig, ListColumn } from "../genericTypes";
import { formatDateTime } from "../format";
import { useAdminList } from "../hooks/useAdminList";
import DataTable, { type Column } from "./DataTable";
import Pagination from "./Pagination";

interface Item {
  id: number;
  [key: string]: unknown;
}

const TONES: Record<BadgeTone, string> = {
  green: "bg-green-50 text-green-700 border-green-200",
  gray: "bg-background-100 text-foreground-600 border-background-300",
  amber: "bg-amber-50 text-amber-800 border-amber-200",
  red: "bg-accent-50 text-accent-700 border-accent-200",
};

// Default meaning of a bare `status` column (see entityConfigs.ts STATUS_OPTIONS).
const DEFAULT_STATUS_BADGES: NonNullable<ListColumn["badges"]> = {
  "1": { label: "Faol", tone: "green" },
  "0": { label: "Nofaol", tone: "gray" },
};

function toColumn(col: ListColumn): Column<Item> {
  const badges = col.badges ?? (col.key === "status" ? DEFAULT_STATUS_BADGES : undefined);
  if (col.kind === "datetime") {
    return { key: col.key, label: col.label, render: (item) => formatDateTime(item[col.key]) };
  }
  if (badges) {
    return {
      key: col.key,
      label: col.label,
      render: (item) => {
        const badge = badges[String(item[col.key])];
        if (!badge) return String(item[col.key] ?? "");
        return (
          <span className={`inline-block px-2 py-0.5 rounded-full border text-xs font-medium ${TONES[badge.tone]}`}>
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
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-2xl font-bold text-foreground-950">{config.title}</h1>
        {!config.noCreate && (
          <Link
            to={`/admin/${config.resource}/new`}
            className="h-10 px-4 rounded-md bg-primary-500 hover:bg-primary-600 text-background-50 text-sm font-semibold flex items-center gap-2 cursor-pointer"
          >
            <i className="ri-add-line" /> {config.addLabel ?? "Yangi qo'shish"}
          </Link>
        )}
      </div>

      <form onSubmit={list.submitSearch} className="mb-4 flex gap-2">
        <input
          value={list.searchInput}
          onChange={(e) => list.setSearchInput(e.target.value)}
          placeholder="Qidirish..."
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
        columns={config.listColumns.map(toColumn)}
        items={list.items}
        loading={list.loading}
        showEmpty={!list.error}
        editPathFor={(item) => `/admin/${config.resource}/${item.id}`}
        onDelete={(item) => list.remove(item, String(item[config.deleteConfirmField] ?? item.id), config.deleteWarning)}
      />
      <Pagination page={list.page} pageSize={list.pageSize} total={list.total} onChange={list.setPage} />
    </div>
  );
}
