import { Outlet, useNavigate } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/ui/button";
import { MobileNav } from "../../components/MobileNav";
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
      <header className="border-b border-gray-200 bg-white sticky top-0 z-30" role="banner">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 sm:px-6 py-3 sm:py-4">
          {/* Logo & Title - Mobile: kleiner, Desktop: vollständig */}
          <div className="flex-1 min-w-0">
            <p className="text-base sm:text-lg font-semibold text-brand-gray truncate">Tick Guard</p>
            <p className="hidden sm:block text-xs text-gray-500">
              Authentifizierter Bereich (Neuaufbau)
            </p>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-2 xl:gap-4 text-sm text-gray-600">
            <button
              className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
              onClick={() => navigate("/app")}
            >
              Dashboard
            </button>
            <button
              className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
              onClick={() => navigate("/app/timesheets")}
            >
              Stundenzettel
            </button>
            <button
              className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
              onClick={() => navigate("/app/expenses")}
            >
              Reisekosten
            </button>
            <button
              className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
              onClick={() => navigate("/app/vacation")}
            >
              Urlaub
            </button>
            <button
              className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
              onClick={() => navigate("/app/announcements")}
            >
              Ankündigungen
            </button>
            {(user.role === "admin" || user.role === "accounting") && (
              <>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/timesheets/admin/review")}
                  aria-label="Zur Prüfung navigieren"
                >
                  Prüfung
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/timesheets/reporting")}
                  aria-label="Zum Reporting navigieren"
                >
                  Reporting
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
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
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/users")}
                  aria-label="Zur Benutzerverwaltung navigieren"
                >
                  Benutzer
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/vehicles")}
                  aria-label="Zur Fahrzeugverwaltung navigieren"
                >
                  Fahrzeuge
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/smtp")}
                  aria-label="Zur SMTP-Konfiguration navigieren"
                >
                  SMTP
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/customers")}
                  aria-label="Zur Kundenverwaltung navigieren"
                >
                  Kunden
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/vacation-balance")}
                  aria-label="Zur Urlaubsguthaben-Verwaltung navigieren"
                >
                  Urlaubsguthaben
                </button>
                <button
                  className="px-2 py-1.5 rounded-md text-brand-gray hover:text-brand-primary hover:bg-gray-100 transition-colors"
                  onClick={() => navigate("/app/admin/audit-logs")}
                  aria-label="Zu Audit-Logs navigieren"
                >
                  Audit-Logs
                </button>
              </>
            )}
          </nav>

          {/* Desktop User Info & Actions */}
          <div className="hidden lg:flex items-center gap-3 xl:gap-4 flex-shrink-0">
            <div className="hidden xl:block text-right text-sm text-gray-600">
              <p className="font-medium text-brand-gray">{user.name}</p>
              <p className="text-xs uppercase tracking-wide text-gray-400">
                {user.role}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPasswordDialog(true)}
              aria-label="Passwort ändern"
              className="hidden xl:inline-flex"
            >
              Passwort ändern
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleLogout}
              aria-label="Abmelden"
            >
              Abmelden
            </Button>
          </div>

          {/* Mobile Navigation */}
          <div className="lg:hidden flex-shrink-0">
            <MobileNav
              user={user}
              onLogout={handleLogout}
              onPasswordChange={() => setShowPasswordDialog(true)}
            />
          </div>
        </div>
      </header>
      <main role="main" className="pb-safe">
        <Outlet />
      </main>
      {showPasswordDialog && (
        <ChangePasswordDialog onClose={() => setShowPasswordDialog(false)} />
      )}
    </div>
  );
};

