import { StrictMode } from 'react'
import './i18n'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/base.css'
import './styles/hero-radar.css'
import './styles/hero-v2.css'
import './styles/home-atmosphere.css'
import './styles/responsive-polish.css'
import './styles/ai-cards.css'
import App from './App.tsx'
import ErrorBoundary from './components/shared/ErrorBoundary.tsx'
import { reloadForStaleBuild } from './lib/staleBuild'

window.addEventListener("vite:preloadError", (event) => {
  event.preventDefault();
  reloadForStaleBuild();
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
