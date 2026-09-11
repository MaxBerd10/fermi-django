import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function NavBar() {
  const { user, loading, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between border-b border-primary-100 bg-white px-6 py-3">
      <div className="flex items-center gap-6">
        <Link to="/" className="font-display text-lg font-extrabold tracking-tight text-primary-900">
          Fer<span className="bg-gradient-to-b from-transparent from-75% to-secondary-400 to-75% text-primary-900">MI</span>
        </Link>
        <Link to="/yangiliklar" className="text-sm font-semibold text-foreground-700 hover:text-primary-700">
          Yangiliklar
        </Link>
      </div>
      <div className="flex items-center gap-3 text-sm">
        {loading ? null : user ? (
          <>
            <span className="text-foreground-600">Salom, {user.username}</span>
            <button
              onClick={logout}
              className="rounded-full bg-primary-50 px-4 py-2 font-semibold text-primary-800 hover:bg-primary-100"
            >
              Chiqish
            </button>
          </>
        ) : (
          <>
            <Link to="/kirish" className="rounded-full px-4 py-2 font-semibold text-primary-700 hover:bg-primary-50">
              Kirish
            </Link>
            <Link to="/royxatdan-otish" className="uni-btn">
              Ro'yxatdan o'tish
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
