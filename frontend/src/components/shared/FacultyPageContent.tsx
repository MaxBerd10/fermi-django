import { useState } from "react";
import "@/styles/faculty-content.css";
import { useTranslation } from "react-i18next";
import type { FacultyDetail } from "@/types/content";
import LeaderProfileCard from "@/components/shared/LeaderProfileCard";
import { getFacultyRoleKey } from "@/lib/facultyDisplay";
import FacultyOverview from "./FacultyOverview";
import { getFacultyPageConfig } from "@/lib/facultySection";

export default function FacultyPageContent({ faculty, slug }: { faculty: FacultyDetail; slug: string }) {
  const { t } = useTranslation();
  const [openLeaderId, setOpenLeaderId] = useState<number | null>(null);

  const hasContent = faculty.blocks.length > 0 || Boolean(getFacultyPageConfig(slug).missionKey);

  return (
    <div className="academic-page">
      {faculty.leaders.length > 0 && (
        <section className="faculty-page__leaders" aria-labelledby="faculty-leaders-heading">
          <h2 id="faculty-leaders-heading" className="academic-page__title">
            {t("faculty.leadersTitle")}
          </h2>
          <div className="leader-prorector-list">
            {faculty.leaders.map((leader, index) => (
              <LeaderProfileCard
                key={`${leader.id}:${leader.photo ?? ""}`}
                leader={leader}
                roleLabel={t(getFacultyRoleKey(leader, faculty.title, index))}
                open={openLeaderId === leader.id}
                onToggle={() => setOpenLeaderId(openLeaderId === leader.id ? null : leader.id)}
              />
            ))}
          </div>
        </section>
      )}

      {hasContent && <FacultyOverview slug={slug} blocks={faculty.blocks} />}
    </div>
  );
}
