import { lazy, Suspense } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import MedicalAtmosphere from "./MedicalAtmosphere";
import { MenuProvider } from "../../context/MenuContext";

// The chat widget pulls in the AI client and the ~5 KB knowledge base, none of
// which the first paint needs — most visits never open it. Load it after the
// page is interactive; the only visible effect is the floating button appearing
// a beat later.
const AiChatWidget = lazy(() => import("./AiChatWidget"));

export default function Layout() {
  return (
    <MenuProvider>
      <div className="relative min-h-screen text-foreground-900 flex flex-col bg-transparent">
        <MedicalAtmosphere />
        {/* This div is itself a flex item of the row above -- the same
            min-w-0 override as <main> below, one level up, since a flex
            item's content-based min-width otherwise propagates to its own
            flex-item parent too, not just stopping at the first one fixed. */}
        <div className="relative z-10 flex flex-col flex-1 min-h-screen min-w-0">
          <Navbar />
          {/* min-w-0 overrides a flex item's default min-width:auto -- without
              it, wide content anywhere on the page (e.g. a table block wider
              than its own overflow-x-auto wrapper intends) could grow this
              whole column instead of being clipped/scrolled within its own
              container, leaking a horizontal scrollbar onto the entire page. */}
          <main className="flex-1 min-w-0">
            <Outlet />
          </main>
          <Footer />
        </div>
        <Suspense fallback={null}>
          <AiChatWidget />
        </Suspense>
      </div>
    </MenuProvider>
  );
}
