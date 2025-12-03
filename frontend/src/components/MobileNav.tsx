import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Button } from "./ui/button";
import { cn } from "../lib/utils";

interface MobileNavProps {
  user: {
    name: string;
    role: string;
  };
  onLogout: () => void;
  onPasswordChange: () => void;
}

export const MobileNav = ({ user, onLogout, onPasswordChange }: MobileNavProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const navItems = [
    { label: "Dashboard", path: "/app" },
    { label: "Stundenzettel", path: "/app/timesheets" },
    { label: "Reisekosten", path: "/app/expenses" },
    { label: "Urlaub", path: "/app/vacation" },
    { label: "Ankündigungen", path: "/app/announcements" },
  ];

  const settingsItems = [
    { label: "Benachrichtigungen", path: "/app/settings/notifications", roles: ["user", "admin", "accounting"] },
  ];

  const adminItems = [
    { label: "Prüfung", path: "/app/timesheets/admin/review", roles: ["admin", "accounting"] },
    { label: "Reporting", path: "/app/timesheets/reporting", roles: ["admin", "accounting"] },
    { label: "Buchhaltung", path: "/app/admin/accounting", roles: ["admin", "accounting"] },
    { label: "Benutzer", path: "/app/admin/users", roles: ["admin"] },
    { label: "Fahrzeuge", path: "/app/admin/vehicles", roles: ["admin"] },
    { label: "SMTP", path: "/app/admin/smtp", roles: ["admin"] },
    { label: "Kunden", path: "/app/admin/customers", roles: ["admin"] },
    { label: "Urlaubsguthaben", path: "/app/admin/vacation-balance", roles: ["admin"] },
    { label: "Audit-Logs", path: "/app/admin/audit-logs", roles: ["admin"] },
    { label: "Migration", path: "/app/admin/migration", roles: ["admin"] },
  ];

  const handleNavClick = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  return (
    <>
      {/* Hamburger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden p-2 rounded-md text-brand-gray hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-primary"
        aria-label="Menü öffnen"
        aria-expanded={isOpen}
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <nav
            className={cn(
              "fixed top-0 right-0 h-full w-80 max-w-[85vw] bg-white shadow-xl z-50 lg:hidden",
              "transform transition-transform duration-300 ease-in-out",
              isOpen ? "translate-x-0" : "translate-x-full"
            )}
            role="navigation"
            aria-label="Hauptnavigation"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div>
                  <p className="text-lg font-semibold text-brand-gray">Tick Guard</p>
                  <p className="text-xs text-gray-500">{user.name}</p>
                  <p className="text-xs uppercase tracking-wide text-gray-400">{user.role}</p>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 rounded-md text-gray-500 hover:bg-gray-100"
                  aria-label="Menü schließen"
                >
                  <X size={24} />
                </button>
              </div>

              {/* Navigation Items */}
              <div className="flex-1 overflow-y-auto py-4">
                <div className="px-2 space-y-1">
                  {navItems.map((item) => (
                    <button
                      key={item.path}
                      onClick={() => handleNavClick(item.path)}
                      className="w-full text-left px-4 py-3 rounded-md text-brand-gray hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-primary transition-colors"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>

                {/* Admin Section */}
                {(user.role === "admin" || user.role === "accounting") && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                      Verwaltung
                    </p>
                    <div className="px-2 space-y-1">
                      {adminItems
                        .filter((item) => !item.roles || item.roles.includes(user.role))
                        .map((item) => (
                          <button
                            key={item.path}
                            onClick={() => handleNavClick(item.path)}
                            className="w-full text-left px-4 py-3 rounded-md text-brand-gray hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-brand-primary transition-colors"
                          >
                            {item.label}
                          </button>
                        ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="border-t border-gray-200 p-4 space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    onPasswordChange();
                    setIsOpen(false);
                  }}
                >
                  Passwort ändern
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    onLogout();
                    setIsOpen(false);
                  }}
                >
                  Abmelden
                </Button>
              </div>
            </div>
          </nav>
        </>
      )}
    </>
  );
};

