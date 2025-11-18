import { Outlet, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/ui/button";
import { useCurrentUserQuery } from "../../modules/auth/hooks/useCurrentUser";
import { authStore } from "../../store/auth-store";
import { ChangePasswordDialog } from "../../modules/auth/components/ChangePasswordDialog";

export const ProtectedLayout = () => {
  const navigate = useNavigate();
  const hasRedirectedRef = useRef(false);
  const { data: user, isLoading, isError } = useCurrentUserQuery();
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  useEffect(() => {
    if (hasRedirectedRef.current) {
      return;
    }

    if (isError || (!isLoading && !user)) {
      hasRedirectedRef.current = true;
      authStore.getState().clearSession();
      navigate("/login", { replace: true });
    }
  }, [isError, isLoading, navigate, user]);

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
    authStore.getState().clearSession();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="border-b border-gray-200 bg-white" role="banner">
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
            <button
              className="text-brand-gray hover:text-brand-primary"
              onClick={() => navigate("/app/expenses")}
            >
              Reisekosten
            </button>
            <button
              className="text-brand-gray hover:text-brand-primary"
              onClick={() => navigate("/app/vacation")}
            >
              Urlaub
            </button>
            <button
              className="text-brand-gray hover:text-brand-primary"
              onClick={() => navigate("/app/announcements")}
            >
              Ankündigungen
            </button>
            {(user.role === "admin" || user.role === "accounting") && (
              <>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/timesheets/admin/review")}
                  aria-label="Zur Prüfung navigieren"
                >
                  Prüfung
                </button>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/timesheets/reporting")}
                  aria-label="Zum Reporting navigieren"
                >
                  Reporting
                </button>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/admin/accounting")}
                  aria-label="Zur Buchhaltung navigieren"
                >
                  Buchhaltung
                </button>
              </>
            )}
            {user.role === "admin" && (
              <>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/admin/users")}
                  aria-label="Zur Benutzerverwaltung navigieren"
                >
                  Benutzer
                </button>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/admin/vehicles")}
                  aria-label="Zur Fahrzeugverwaltung navigieren"
                >
                  Fahrzeuge
                </button>
                <button
                  className="text-brand-gray hover:text-brand-primary"
                  onClick={() => navigate("/app/admin/smtp")}
                  aria-label="Zur SMTP-Konfiguration navigieren"
                >
                  SMTP
                </button>
              </>
            )}
          </nav>
          <div className="flex items-center gap-4">
            <div className="text-right text-sm text-gray-600">
              <p className="font-medium text-brand-gray">{user.name}</p>
              <p className="text-xs uppercase tracking-wide text-gray-400">
                {user.role}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowPasswordDialog(true)}
              aria-label="Passwort ändern"
            >
              Passwort ändern
            </Button>
            <Button 
              variant="outline" 
              onClick={handleLogout}
              aria-label="Abmelden"
            >
              Abmelden
            </Button>
          </div>
        </div>
      </header>
      <main role="main">
        <Outlet />
      </main>
      {showPasswordDialog && (
        <ChangePasswordDialog onClose={() => setShowPasswordDialog(false)} />
      )}
    </div>
  );
};

