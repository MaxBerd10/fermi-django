import { useId, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import "@/styles/leader-content.css";
import type { Leader } from "@/types/content";
import LeaderRichContent from "@/components/shared/LeaderRichContent";
import { optimizedImageUrl } from "@/lib/imageProxy";
import {
  cleanPhoneForTel,
  displayLeaderText,
  hasLeaderHtmlContent,
} from "@/lib/leaderDisplay";

function ContactPill({
  icon,
  label,
  value,
  href,
}: {
  icon: string;
  label: string;
  value: string;
  href?: string;
}) {
  const inner = (
    <>
      <span className="leader-pill__label">{label}</span>
      <span className="leader-pill__value">{value}</span>
    </>
  );

  if (href) {
    return (
      <a href={href} className="leader-pill">
        <i className={icon} aria-hidden />
        {inner}
      </a>
    );
  }

  return (
    <div className="leader-pill">
      <i className={icon} aria-hidden />
      {inner}
    </div>
  );
}

export default function LeaderProfileCard({
  leader,
  open,
  onToggle,
  roleLabel,
  rector,
}: {
  leader: Leader;
  open: boolean;
  onToggle: () => void;
  roleLabel?: string;
  rector?: boolean;
}) {
  const { t } = useTranslation();
  const [photo, setPhoto] = useState(() => optimizedImageUrl(leader.photo, 320));
  const hasActivity = hasLeaderHtmlContent(leader.activity);
  const hasBio = hasLeaderHtmlContent(leader.biography);
  const detailsId = useId();
  const singlePanel = !(hasActivity && hasBio);

  return (
    <article className={`leader-prorector ${open ? "leader-prorector--open" : ""}`}>
      <div className="leader-prorector__header">
        <div className="leader-prorector__portrait">
          {photo ? (
            <img
              src={photo}
              alt={leader.name}
              className="leader-prorector__photo"
              loading="lazy"
              onError={() => setPhoto(photo === leader.photo ? "" : leader.photo || "")}
            />
          ) : (
            <div className="leader-prorector__photo-placeholder" aria-hidden>
              <i className="ri-user-3-line" />
            </div>
          )}
        </div>

        <div className="leader-prorector__summary">
          {roleLabel && <span className="leader-prorector__badge">{roleLabel}</span>}
          <h2 className="leader-prorector__name">{displayLeaderText(leader.name)}</h2>
          <p className="leader-prorector__position">{displayLeaderText(leader.position)}</p>

          <div className="leader-prorector__contacts">
            {leader.phone && (
              <ContactPill
                icon="ri-phone-line"
                label={t("leader.contact.phone")}
                value={leader.phone}
                href={`tel:${cleanPhoneForTel(leader.phone)}`}
              />
            )}
            {leader.email && (
              <ContactPill
                icon="ri-mail-line"
                label={t("leader.contact.email")}
                value={leader.email}
                href={`mailto:${leader.email}`}
              />
            )}
            {leader.receptionDays && (
              <ContactPill
                icon="ri-calendar-check-line"
                label={t("leader.contact.reception")}
                value={displayLeaderText(leader.receptionDays)}
              />
            )}
          </div>
          {rector && (
            <Link to="/virtual-qabulxona" className="leader-profile-reception">
              <i className="ri-customer-service-2-line" aria-hidden="true" /> {t("leader.virtualReception")}
            </Link>
          )}
        </div>

        <button
          type="button"
          className="leader-prorector__toggle"
          onClick={onToggle}
          aria-expanded={open}
          aria-controls={detailsId}
        >
          <span>{open ? t("leader.showLess") : t("leader.readMore")}</span>
          <i className={`ri-arrow-down-s-line ${open ? "rotate-180" : ""}`} aria-hidden />
        </button>
      </div>

      {rector && (
        <div className="leader-profile-highlights">
          <blockquote>{t("leadership.quote")}</blockquote>
          <ul>
            {[1, 2, 3, 4].map((index) => <li key={index}>{t(`leadership.highlight${index}`)}</li>)}
          </ul>
        </div>
      )}

      <div id={detailsId} hidden={!open}>
        {open && (
          <div className={`leader-prorector__panels ${singlePanel ? "leader-prorector__panels--single" : ""}`}>
            {hasActivity && (
              <section className="leader-panel leader-panel--duties leader-panel--compact">
                <header className="leader-panel__head">
                  <i className="ri-briefcase-4-line" aria-hidden />
                  <h3>{t("leader.activity")}</h3>
                </header>
                <div className="leader-panel__body">
                  <LeaderRichContent html={leader.activity} />
                </div>
              </section>
            )}
            {hasBio ? (
              <section className="leader-panel leader-panel--bio leader-panel--compact">
                <header className="leader-panel__head">
                  <i className="ri-book-open-line" aria-hidden />
                  <h3>{t("leader.biography")}</h3>
                </header>
                <div className="leader-panel__body">
                  <LeaderRichContent html={leader.biography} />
                </div>
              </section>
            ) : (
              <p className="text-sm text-slate-600">{t("leader.bioUnavailable")}</p>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
