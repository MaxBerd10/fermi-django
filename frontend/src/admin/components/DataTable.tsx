import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

export interface Column<T> {
  key: string;
  label: string;
  render?: (item: T) => ReactNode;
}

interface DataTableProps<T extends { id: number }> {
  columns: Column<T>[];
  items: T[];
  loading: boolean;
  /** False while a load error is on screen, so a failed request doesn't read as "no records". */
  showEmpty?: boolean;
  editPathFor: (item: T) => string;
  onDelete: (item: T) => void;
  /** Rows nobody has looked at yet (new messages) are drawn bold with a dot. */
  isUnread?: (item: T) => boolean;
  emptyText?: string;
}

function cell<T>(col: Column<T>, item: T): ReactNode {
  return col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? "");
}

function Skeleton() {
  return (
    <div className="space-y-px overflow-hidden rounded-xl border border-background-200 bg-background-50" aria-busy="true" aria-label="Yuklanmoqda">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-background-200 px-4 py-4 last:border-0">
          <div className="h-4 flex-1 animate-pulse rounded bg-background-200" />
          <div className="hidden h-4 w-28 animate-pulse rounded bg-background-200 md:block" />
          <div className="hidden h-4 w-20 animate-pulse rounded bg-background-200 md:block" />
        </div>
      ))}
    </div>
  );
}

/** A list of records: a table on wide screens, one card per record on a phone. The whole row opens the record;
 *  the pencil and bin buttons stay for the eye. The technical ID column is not shown -- editors never need it. */
export default function DataTable<T extends { id: number }>({
  columns,
  items,
  loading,
  showEmpty = true,
  editPathFor,
  onDelete,
  isUnread,
  emptyText = "Hech qanday yozuv topilmadi.",
}: DataTableProps<T>) {
  const navigate = useNavigate();
  const shown = columns.filter((col) => col.key !== "id");

  if (loading && items.length === 0) return <Skeleton />;

  if (items.length === 0) {
    return showEmpty ? (
      <div className="rounded-xl border border-dashed border-background-300 bg-background-50 py-16 text-center">
        <i className="ri-inbox-line text-3xl text-foreground-300" aria-hidden="true" />
        <p className="mt-2 text-sm text-foreground-500">{emptyText}</p>
      </div>
    ) : null;
  }

  const [primary, ...rest] = shown;

  function onRowClick(e: React.MouseEvent, item: T) {
    // A click on a link/button inside the row does its own thing; anywhere else opens the record.
    if ((e.target as HTMLElement).closest("a,button,input,select,textarea")) return;
    navigate(editPathFor(item));
  }

  return (
    <div className={loading ? "opacity-60 transition-opacity" : "transition-opacity"}>
      <div className="hidden overflow-x-auto rounded-xl border border-background-200 bg-background-50 md:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-background-200 bg-background-100">
              {shown.map((col) => (
                <th key={col.key} className="whitespace-nowrap px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-foreground-500">
                  {col.label}
                </th>
              ))}
              <th className="w-24 px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const unread = isUnread?.(item) ?? false;
              return (
                <tr
                  key={item.id}
                  onClick={(e) => onRowClick(e, item)}
                  className="cursor-pointer border-b border-background-200 last:border-0 hover:bg-primary-50/60"
                >
                  {shown.map((col, i) => (
                    <td key={col.key} className={`px-4 py-3.5 align-top text-foreground-800 ${unread && i === 0 ? "font-semibold" : ""}`}>
                      {unread && i === 0 && <span className="mr-2 inline-block h-2 w-2 rounded-full bg-secondary-600 align-middle" aria-label="Yangi" />}
                      {cell(col, item)}
                    </td>
                  ))}
                  <td className="whitespace-nowrap px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <Link
                        to={editPathFor(item)}
                        className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-md text-foreground-500 hover:bg-background-200 hover:text-primary-600"
                        title="Tahrirlash"
                      >
                        <i className="ri-pencil-line" />
                      </Link>
                      <button
                        type="button"
                        onClick={() => onDelete(item)}
                        className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-md text-foreground-500 hover:bg-red-50 hover:text-red-600"
                        title="O'chirish"
                      >
                        <i className="ri-delete-bin-line" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <ul className="space-y-2 md:hidden">
        {items.map((item) => {
          const unread = isUnread?.(item) ?? false;
          return (
            <li key={item.id} className="rounded-xl border border-background-200 bg-background-50">
              <div className="flex items-start gap-2 p-4 pb-3">
                <Link to={editPathFor(item)} className={`min-w-0 flex-1 text-sm text-foreground-900 ${unread ? "font-semibold" : "font-medium"}`}>
                  {unread && <span className="mr-2 inline-block h-2 w-2 rounded-full bg-secondary-600 align-middle" aria-label="Yangi" />}
                  {primary ? cell(primary, item) : `#${item.id}`}
                </Link>
                <button
                  type="button"
                  onClick={() => onDelete(item)}
                  className="-mr-1 -mt-1 flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-md text-foreground-400 hover:bg-red-50 hover:text-red-600"
                  title="O'chirish"
                  aria-label="O'chirish"
                >
                  <i className="ri-delete-bin-line" />
                </button>
              </div>
              {rest.length > 0 && (
                <dl className="grid grid-cols-2 gap-x-3 gap-y-2 border-t border-background-200 px-4 py-3 text-xs">
                  {rest.map((col) => {
                    const value = cell(col, item);
                    if (value === "" || value === null) return null;
                    return (
                      <div key={col.key} className="min-w-0">
                        <dt className="text-foreground-500">{col.label}</dt>
                        <dd className="mt-0.5 break-words text-foreground-800">{value}</dd>
                      </div>
                    );
                  })}
                </dl>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
