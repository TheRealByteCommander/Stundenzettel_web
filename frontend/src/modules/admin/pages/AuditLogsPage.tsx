import { useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { useAuditLogsQuery } from "../hooks/useAuditLogs";
import { useAdminUsersQuery } from "../hooks/useAdminUsers";
import type { AuditLog } from "../../../services/api/audit";

const ACTION_OPTIONS = [
  { value: "", label: "Alle Aktionen" },
  { value: "upload", label: "Upload" },
  { value: "download", label: "Download" },
  { value: "view", label: "Anzeigen" },
  { value: "delete", label: "Löschen" },
  { value: "modify", label: "Ändern" },
];

const RESOURCE_TYPE_OPTIONS = [
  { value: "", label: "Alle Ressourcen" },
  { value: "receipt", label: "Beleg" },
  { value: "report", label: "Report" },
  { value: "document", label: "Dokument" },
  { value: "timesheet", label: "Stundenzettel" },
];

export const AuditLogsPage = () => {
  const [filters, setFilters] = useState<{
    limit: number;
    user_id?: string;
    action?: string;
    resource_type?: string;
  }>({
    limit: 500,
  });

  const { data, isLoading, error } = useAuditLogsQuery(filters);
  const { data: users } = useAdminUsersQuery();

  const handleFilterChange = (key: string, value: string | number) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }));
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString("de-DE", {
        dateStyle: "short",
        timeStyle: "medium",
      });
    } catch {
      return timestamp;
    }
  };

  const getUserName = (userId: string) => {
    return users?.find((u) => u.id === userId)?.name ?? userId;
  };

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
          Audit-Logs
        </h1>
        <p className="text-xs sm:text-sm text-gray-600">
          Übersicht aller protokollierten Datenzugriffe (DSGVO-Compliance).
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          Fehler beim Laden der Audit-Logs:{" "}
          {(error as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail ?? (error as { message?: string }).message}
        </Alert>
      )}

      <Card>
        <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Filter
          </CardTitle>
          <div className="grid gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="filter-user" className="text-sm">Mitarbeiter:</Label>
              <select
                id="filter-user"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px] sm:min-h-[40px]"
                value={filters.user_id || ""}
                onChange={(e) => handleFilterChange("user_id", e.target.value)}
              >
                <option value="">Alle Mitarbeiter</option>
                {users?.map((user) => (
                  <option key={user.id} value={user.id}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="filter-action" className="text-sm">Aktion:</Label>
              <select
                id="filter-action"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px] sm:min-h-[40px]"
                value={filters.action || ""}
                onChange={(e) => handleFilterChange("action", e.target.value)}
              >
                {ACTION_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="filter-resource" className="text-sm">Ressourcentyp:</Label>
              <select
                id="filter-resource"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px] sm:min-h-[40px]"
                value={filters.resource_type || ""}
                onChange={(e) => handleFilterChange("resource_type", e.target.value)}
              >
                {RESOURCE_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="filter-limit" className="text-sm">Anzahl:</Label>
              <Input
                id="filter-limit"
                type="number"
                min="1"
                max="10000"
                value={filters.limit}
                onChange={(e) => handleFilterChange("limit", Number(e.target.value))}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <CardTitle className="text-base sm:text-lg text-brand-gray">
              Audit-Logs ({data?.count ?? 0} Einträge)
            </CardTitle>
          </div>

          {isLoading ? (
            <p className="text-center text-gray-500 py-6">Lade Audit-Logs…</p>
          ) : data && data.logs.length > 0 ? (
            <>
              {/* Mobile: Card-Layout */}
              <div className="block sm:hidden space-y-2">
                {data.logs.map((log: AuditLog, index: number) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-200 bg-white p-3 text-xs"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold text-brand-gray">
                          {getUserName(log.user_id)}
                        </p>
                        <p className="text-gray-600">{formatTimestamp(log.timestamp)}</p>
                      </div>
                      <span className="rounded-full px-2 py-1 bg-gray-100 text-gray-700 text-xs">
                        {log.action}
                      </span>
                    </div>
                    <div className="text-gray-600 space-y-1">
                      <p>
                        <strong>Ressource:</strong> {log.resource_type} ({log.resource_id})
                      </p>
                      {log.details && Object.keys(log.details).length > 0 && (
                        <p>
                          <strong>Details:</strong> {JSON.stringify(log.details)}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop: Tabelle */}
              <div className="hidden sm:block overflow-x-auto rounded-lg border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                    <tr>
                      <th className="px-4 py-3">Zeitstempel</th>
                      <th className="px-4 py-3">Mitarbeiter</th>
                      <th className="px-4 py-3">Aktion</th>
                      <th className="px-4 py-3">Ressourcentyp</th>
                      <th className="px-4 py-3">Ressourcen-ID</th>
                      <th className="px-4 py-3">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {data.logs.map((log: AuditLog, index: number) => (
                      <tr key={index}>
                        <td className="px-4 py-3 text-gray-600 text-xs">
                          {formatTimestamp(log.timestamp)}
                        </td>
                        <td className="px-4 py-3 font-medium text-brand-gray">
                          {getUserName(log.user_id)}
                        </td>
                        <td className="px-4 py-3">
                          <span className="rounded-full px-2 py-1 bg-gray-100 text-gray-700 text-xs">
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{log.resource_type}</td>
                        <td className="px-4 py-3 text-gray-600 text-xs font-mono">
                          {log.resource_id.substring(0, 8)}...
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-xs">
                          {log.details && Object.keys(log.details).length > 0
                            ? JSON.stringify(log.details).substring(0, 50) + "..."
                            : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p className="text-center text-gray-500 py-6">
              Keine Audit-Logs gefunden.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

