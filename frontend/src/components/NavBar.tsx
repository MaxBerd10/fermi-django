import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function NavBar() {
  const { user, loading, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between border-b border-slate-200 px-6 py-3">
      <Link to="/" className="font-semibold text-slate-900">
        FerMI
      </Link>
      <div className="flex items-center gap-3 text-sm">
        {loading ? null : user ? (
          <>
            <span className="text-slate-600">Salom, {user.username}</span>
            <button onClick={logout} className="rounded-lg bg-slate-100 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-200">
              Chiqish
            </button>
          </>
        ) : (
          <>
            <Link to="/kirish" className="rounded-lg px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100">
              Kirish
            </Link>
            <Link to="/royxatdan-otish" className="rounded-lg bg-slate-900 px-3 py-1.5 font-medium text-white">
              Ro'yxatdan o'tish
            </Link>
          </>
        )}
      </div>
    </nav>
  );
}
