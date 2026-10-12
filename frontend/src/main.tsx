import { StrictMode } from 'react'
import './i18n'
import { createRoot } from 'react-dom/client'
import './index.css'
import './styles/global.css'
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
