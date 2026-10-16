import { useOutletContext } from "react-router-dom";

export interface DashboardNews {
  id: number;
  title: string;
  published_at: string;
  hidden: number;
  views: number;
}

/** GET /api/v1/admin/dashboard (apps/admin_api/dashboard_views.py). */
export interface DashboardData {
  /** Messages nobody has opened yet, per inbox resource ("contacts", "acceptances", ...). */
  unread: Record<string, number>;
  drafts: number;
  /** Drafts that staff sent through the Telegram bot and nobody has published yet. */
  telegram_drafts: number;
  news: DashboardNews[];
}

export interface AdminOutletContext {
  summary: DashboardData | null;
  refreshSummary: () => void;
}

/** What AdminLayout loaded for the sidebar badges; null until the first answer (or if it failed). */
export function useAdminSummary(): AdminOutletContext {
  return useOutletContext<AdminOutletContext>();
}
