import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { NavBar } from "./components/NavBar";
import { DepartmentPage } from "./DepartmentPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavBar />
        <Routes>
          <Route path="/" element={<DepartmentPage slug="akusherlik-va-ginekologiya-kafedrasi" />} />
          <Route path="/kirish" element={<LoginPage />} />
          <Route path="/royxatdan-otish" element={<RegisterPage />} />
          <Route path="/email-tasdiqlash/:uid/:token" element={<VerifyEmailPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
