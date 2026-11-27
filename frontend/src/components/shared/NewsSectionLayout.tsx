import type { ReactNode } from "react";
import { InnerPageContent } from "./InnerPageLayout";
import { Reveal } from "@/components/Animation";
import NewsSectionNav from "@/components/shared/NewsSectionNav";
import MenuSectionNav from "@/components/shared/MenuSectionNav";

export default function NewsSectionLayout({
  children,
  intro,
  currentSlug,
  showAllNews = true,
  theme,
  menuSectionId,
}: {
  children: ReactNode;
  intro?: string;
  currentSlug?: string;
  showAllNews?: boolean;
  theme?: string;
  menuSectionId?: number;
}) {
  return (
    <InnerPageContent
      className={`news-section${theme ? ` news-section--${theme}` : ""}`}
      sidebar={menuSectionId ? (
        <MenuSectionNav menuId={menuSectionId} currentSlug={currentSlug} />
      ) : (
        <NewsSectionNav currentSlug={currentSlug} showAllNews={showAllNews} />
      )}
    >
      {intro && (
        <Reveal>
          <p className="news-section__intro">{intro}</p>
        </Reveal>
      )}
      {children}
    </InnerPageContent>
  );
}
