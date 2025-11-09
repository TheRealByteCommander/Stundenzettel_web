import { Outlet, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "../../components/ui/button";
import { useCurrentUserQuery } from "../../modules/auth/hooks/useCurrentUser";
import { useAuthStore } from "../../store/auth-store";

export const ProtectedLayout = () => {
  const navigate = useNavigate();
  const { clearSession } = useAuthStore((state) => ({
    clearSession: state.clearSession,
  }));
  const { data: user, isLoading, isError } = useCurrentUserQuery();

  useEffect(() => {
    if (isError || (!isLoading && !user)) {
      clearSession();
      navigate("/login", { replace: true });
    }
  }, [clearSession, isError, isLoading, navigate, user]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Benutzerdaten…
      </div>
    );
  }

  if (isError || !user) {
    return null;
  }

  const handleLogout = () => {
    clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-lg font-semibold text-brand-gray">Tick Guard</p>
            <p className="text-xs text-gray-500">
              Authentifizierter Bereich (Neuaufbau)
            </p>
          </div>
          <nav className="flex items-center gap-4 text-sm text-gray-600">
            <button
              className="text-brand-gray hover:text-brand-primary"
              onClick={() => navigate("/app")}
            >
              Dashboard
            </button>
            <button
              className="text-brand-gray hover:text-brand-primary"
              onClick={() => navigate("/app/timesheets")}
            >
              Stundenzettel
            </button>
            {(user.role === "admin" || user.role === "accounting") && (
              <button
                className="text-brand-gray hover:text-brand-primary"
                onClick={() => navigate("/app/timesheets/admin/review")}
              >
                Prüfung
              </button>
            )}
          </nav>
          <div className="flex items-center gap-4">
            <div className="text-right text-sm text-gray-600">
              <p className="font-medium text-brand-gray">{user.name}</p>
              <p className="text-xs uppercase tracking-wide text-gray-400">
                {user.role}
              </p>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              Abmelden
            </Button>
          </div>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
};

