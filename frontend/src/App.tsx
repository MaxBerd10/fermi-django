import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { NavBar } from "./components/NavBar";
import { LanguageProvider } from "./i18n/LanguageContext";
import { DepartmentPage } from "./DepartmentPage";
import { FacultyDetailPage } from "./pages/FacultyDetailPage";
import { FacultyListPage } from "./pages/FacultyListPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { NewsDetailPage } from "./pages/NewsDetailPage";
import { NewsListPage } from "./pages/NewsListPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

export default function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <NavBar />
          <Routes>
            <Route path="/" element={<DepartmentPage slug="akusherlik-va-ginekologiya-kafedrasi" />} />
            <Route path="/yangiliklar" element={<NewsListPage />} />
            <Route path="/yangiliklar/:slug" element={<NewsDetailPage />} />
            <Route path="/fakultetlar" element={<FacultyListPage />} />
            <Route path="/fakultetlar/:slug" element={<FacultyDetailPage />} />
            <Route path="/kirish" element={<LoginPage />} />
            <Route path="/parolni-unutdim" element={<ForgotPasswordPage />} />
            <Route path="/parolni-tiklash/:uid/:token" element={<ResetPasswordPage />} />
            <Route path="/royxatdan-otish" element={<RegisterPage />} />
            <Route path="/email-tasdiqlash/:uid/:token" element={<VerifyEmailPage />} />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}
