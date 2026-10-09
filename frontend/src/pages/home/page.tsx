import { lazy } from "react";
import Hero from "@/pages/home/components/Hero";
import NewsAnnouncements from "@/pages/home/components/NewsAnnouncements";
import DeferredSection from "@/components/shared/DeferredSection";

// Everything below the first screens loads when the visitor scrolls toward it (see DeferredSection).
// The placeholder heights are the sections' measured heights on a phone and on a wide screen.
const About = lazy(() => import("@/pages/home/components/About"));
const FacultiesNews = lazy(() => import("@/pages/home/components/FacultiesNews"));
const WhyUs = lazy(() => import("@/pages/home/components/WhyUs"));
const PathFinder = lazy(() => import("@/pages/home/components/PathFinder"));
const StudentVoices = lazy(() => import("@/pages/home/components/StudentVoices"));
const Leadership = lazy(() => import("@/pages/home/components/Leadership"));
const Gallery = lazy(() => import("@/pages/home/components/Gallery"));
const EventsJournal = lazy(() => import("@/pages/home/components/EventsJournal"));
const Partners = lazy(() => import("@/pages/home/components/Partners"));
const OurProjects = lazy(() => import("@/pages/home/components/OurProjects"));
const ContactMap = lazy(() => import("@/pages/home/components/ContactMap"));

export default function Home() {
  return (
    <div className="text-foreground-950 bg-transparent">
      <main>
        <Hero />
        <NewsAnnouncements />
        <DeferredSection placeholderClassName="min-h-[917px] lg:min-h-[637px]">
          <About />
        </DeferredSection>
        <DeferredSection id="faculties-news" placeholderClassName="min-h-[1724px] lg:min-h-[743px]">
          <FacultiesNews />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[802px] lg:min-h-[300px]">
          <WhyUs />
        </DeferredSection>
        <DeferredSection id="pathfinder" placeholderClassName="min-h-[1702px] lg:min-h-[842px]">
          <PathFinder />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[441px] lg:min-h-[301px]">
          <StudentVoices />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[1053px] lg:min-h-[709px]">
          <Leadership />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[568px] lg:min-h-[320px]">
          <Gallery />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[1404px] lg:min-h-[927px]">
          <EventsJournal />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[360px] lg:min-h-[220px]">
          <Partners />
        </DeferredSection>
        <DeferredSection placeholderClassName="min-h-[784px] lg:min-h-[369px]">
          <OurProjects />
        </DeferredSection>
        <DeferredSection id="aloqa" placeholderClassName="min-h-[1112px] lg:min-h-[570px]">
          <ContactMap />
        </DeferredSection>
      </main>
    </div>
  );
}
