import { lazy } from "react";
import { useRoutes } from "react-router-dom";
import { AdminAuthProvider } from "./AdminAuthContext";
import AdminGuard from "./AdminGuard";
import { ALL_ENTITY_CONFIGS, SINGLETON_CONFIGS } from "./entityConfigs";

const AdminLayout = lazy(() => import("./AdminLayout"));
const AdminLoginPage = lazy(() => import("./pages/AdminLoginPage"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const AdminStatistics = lazy(() => import("./pages/AdminStatistics"));
const NewsListPage = lazy(() => import("./pages/news/NewsListPage"));
const NewsFormPage = lazy(() => import("./pages/news/NewsFormPage"));
const PagesListPage = lazy(() => import("./pages/pages/PagesListPage"));
const PagesFormPage = lazy(() => import("./pages/pages/PagesFormPage"));
const GenericListPage = lazy(() => import("./components/GenericListPage"));
const GenericFormPage = lazy(() => import("./components/GenericFormPage"));
const SingletonFormPage = lazy(() => import("./components/SingletonFormPage"));
const MenuTreePage = lazy(() => import("./pages/menu/MenuTreePage"));
const UserListPage = lazy(() => import("./pages/users/UserListPage"));
const UserFormPage = lazy(() => import("./pages/users/UserFormPage"));

export default function AdminRoutes() {
  return useRoutes([
    { path: "login", element: <AdminAuthProvider><AdminLoginPage /></AdminAuthProvider> },
    {
      element: <AdminAuthProvider><AdminGuard /></AdminAuthProvider>,
      children: [{
        element: <AdminLayout />,
        children: [
          { index: true, element: <AdminDashboard /> },
          { path: "statistics", element: <AdminStatistics /> },
          { path: "news", element: <NewsListPage /> }, { path: "news/new", element: <NewsFormPage /> }, { path: "news/:id", element: <NewsFormPage /> },
          { path: "pages", element: <PagesListPage /> }, { path: "pages/new", element: <PagesFormPage /> }, { path: "pages/:id", element: <PagesFormPage /> },
          ...ALL_ENTITY_CONFIGS.flatMap((config) => [{ path: config.resource, element: <GenericListPage config={config} /> }, { path: `${config.resource}/new`, element: <GenericFormPage config={config} /> }, { path: `${config.resource}/:id`, element: <GenericFormPage config={config} /> }]),
          ...SINGLETON_CONFIGS.map((config) => ({ path: config.resource, element: <SingletonFormPage config={config} /> })),
          { path: "menu-tree", element: <MenuTreePage /> },
          { path: "users", element: <UserListPage /> }, { path: "users/new", element: <UserFormPage /> }, { path: "users/:id", element: <UserFormPage /> },
        ],
      }],
    },
  ]);
}
