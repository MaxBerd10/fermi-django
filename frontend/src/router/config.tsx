import { lazy } from "react";
import type { RouteObject } from "react-router-dom";
import Layout from "../components/feature/Layout";

const NotFound = lazy(() => import("../pages/NotFound"));
const Home = lazy(() => import("../pages/home/page"));
const Yangiliklar = lazy(() => import("../pages/yangiliklar/page"));
const Aloqa = lazy(() => import("../pages/aloqa/page"));
const Qabul = lazy(() => import("../pages/qabul/page"));
const AdmissionResults = lazy(() => import("../pages/qabul-natijalari/page"));
const Institut = lazy(() => import("../pages/institut/page"));
const VirtualQabulxona = lazy(() => import("../pages/virtual-qabulxona/page"));
const BlogPage = lazy(() => import("../pages/blog/page"));
const LeaderPage = lazy(() => import("../pages/leader/page"));
const FacultyPage = lazy(() => import("../pages/faculty/page"));
const DepartmentPage = lazy(() => import("../pages/departments/page"));
const DocumentsPage = lazy(() => import("../pages/documents/page"));
const NewsCategoryPage = lazy(() => import("../pages/news/page"));
const DetailPage = lazy(() => import("../pages/detail/page"));
const AboutPage = lazy(() => import("../pages/about/page"));
const RedesignPreviewPage = lazy(() => import("../pages/redesign-preview/page"));
const GaleryaPage = lazy(() => import("../pages/galereya/page"));
const FullGalleryPage = lazy(() => import("../pages/full-gallery/page"));
const VideoPage = lazy(() => import("../pages/video/page"));
const SchedulePage = lazy(() => import("../pages/schedule/page"));
const SearchPage = lazy(() => import("../pages/search/page"));
const SitemapPage = lazy(() => import("../pages/sitemap/page"));
const TestPage = lazy(() => import("../pages/test/page"));
const KeyslarPage = lazy(() => import("../pages/keyslar/page"));
const LoginPage = lazy(() => import("../pages/auth/login/page"));
const SignupPage = lazy(() => import("../pages/auth/signup/page"));
const PasswordResetPage = lazy(() => import("../pages/auth/password-reset/page"));
const VerifyEmailPage = lazy(() => import("../pages/auth/verify-email/page"));

// The whole admin panel (including the TipTap rich text editor) is a large chunk
// that regular site visitors never touch — keep it fully lazy.
// Keep admin auth, form metadata and editor code out of every public visit.
const AdminRoutes = lazy(() => import("../admin/AdminRoutes"));

const routes: RouteObject[] = [
  // Standalone design-concept preview — deliberately outside <Layout/> so
  // it doesn't inherit the current Navbar/Footer while the client evaluates
  // the new visual direction. Not linked from anywhere in real navigation.
  { path: "/yangi-dizayn", element: <RedesignPreviewPage /> },
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },

      { path: "/yangiliklar", element: <Yangiliklar /> },
      { path: "/aloqa", element: <Aloqa /> },
      { path: "/aloqa/:sub", element: <Aloqa /> },
      { path: "/qabul", element: <Qabul /> },
      { path: "/qabul-natijalari", element: <AdmissionResults /> },
      { path: "/qabul/:type", element: <Qabul /> },
      { path: "/institut", element: <Institut /> },
      { path: "/institut/:sub", element: <Institut /> },
      { path: "/virtual-qabulxona", element: <VirtualQabulxona /> },

      // Legacy urlManager-matching routes (kept for SEO — see approved plan)
      { path: "/blog/:menuId/:slug", element: <BlogPage /> },
      { path: "/leader/:menuId/:slug", element: <LeaderPage /> },
      { path: "/faculty/:menuId/:slug", element: <FacultyPage /> },
      { path: "/departments/:menuId/:slug", element: <DepartmentPage /> },
      { path: "/documents/:menuId/:slug", element: <DocumentsPage /> },
      { path: "/news/:menuId/:slug", element: <NewsCategoryPage /> },
      { path: "/detail/:slug", element: <DetailPage /> },
      { path: "/about/:slug", element: <AboutPage /> },
      { path: "/virtual-reception/:menuId", element: <VirtualQabulxona /> },
      { path: "/galereya", element: <GaleryaPage /> },
      { path: "/full-gallery/:id", element: <FullGalleryPage /> },
      { path: "/video", element: <VideoPage /> },
      { path: "/schedule", element: <SchedulePage /> },
      { path: "/search", element: <SearchPage /> },
      { path: "/sitemap", element: <SitemapPage /> },
      { path: "/test", element: <TestPage /> },
      { path: "/keyslar", element: <KeyslarPage /> },

      // Auth
      { path: "/kirish", element: <LoginPage /> },
      { path: "/royxatdan-otish", element: <SignupPage /> },
      { path: "/parolni-tiklash", element: <PasswordResetPage /> },
      { path: "/parolni-tiklash/:token", element: <PasswordResetPage /> },
      { path: "/email-tasdiqlash/:token", element: <VerifyEmailPage /> },

      { path: "*", element: <NotFound /> },
    ],
  },
  { path: "/admin/*", element: <AdminRoutes /> },
];

export default routes;
