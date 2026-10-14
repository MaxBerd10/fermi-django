import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface Props {
  title: string;
  /** Small "← Yangiliklar" link above the title (forms point back to their list). */
  back?: { to: string; label: string };
  subtitle?: ReactNode;
  /** Buttons on the right (e.g. "Yangi qo'shish"). */
  actions?: ReactNode;
}

export default function PageHeader({ title, back, subtitle, actions }: Props) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-x-4 gap-y-3">
      <div className="min-w-0">
        {back && (
          <Link to={back.to} className="mb-1 inline-flex items-center gap-1 text-xs font-medium text-foreground-500 hover:text-primary-600">
            <i className="ri-arrow-left-s-line" aria-hidden="true" /> {back.label}
          </Link>
        )}
        <h1 className="font-heading text-xl font-bold text-foreground-950 sm:text-2xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-foreground-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
