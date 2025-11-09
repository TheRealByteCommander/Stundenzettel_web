import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import {
  useAccountingApproveMutation,
  useAccountingRejectMutation,
  useAccountingTimesheetsQuery,
} from "../hooks/useAccountingTimesheets";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export const TimesheetAdminPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAccounting = user?.role === "admin" || user?.role === "accounting";
  const [month, setMonth] = useState(getCurrentMonth);

  const params = useMemo(
    () => ({
      month: month || undefined,
    }),
    [month]
  );

  const { data, isLoading, error } = useAccountingTimesheetsQuery(params);
  const approveMutation = useAccountingApproveMutation();
  const rejectMutation = useAccountingRejectMutation();

  if (!isAccounting) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Alert variant="destructive">
          Sie benötigen Rollenrechte (Buchhaltung oder Admin), um auf diesen
          Bereich zuzugreifen.
        </Alert>
      </div>
    );
  }

  const handleApprove = (id: string) => {
    approveMutation.mutate({ id, params });
  };

  const handleReject = (id: string) => {
    rejectMutation.mutate({ id, params });
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Stundenzettel – Buchhaltung
          </h1>
          <p className="text-sm text-gray-600">
            Übersicht aller Stundenzettel mit Upload-Status. Genehmigen oder
            weisen Sie Zeiten manuell zu.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="filter-month" className="text-sm text-gray-600">
            Monat
          </label>
          <Input
            id="filter-month"
            type="month"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
          />
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          Stundenzettel konnten nicht geladen werden:{" "}
          {(
            error.response?.data as { detail?: string } | undefined
          )?.detail ?? error.message}
        </Alert>
      )}

      <Card>
        <CardContent className="overflow-x-auto py-4">
          <CardTitle className="mb-4 text-base text-brand-gray">
            Eingänge
          </CardTitle>
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-100 text-left text-xs uppercase tracking-wide text-gray-600">
              <tr>
                <th className="px-4 py-3">Mitarbeiter</th>
                <th className="px-4 py-3">Woche</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Unterschrift</th>
                <th className="px-4 py-3">Hinweise</th>
                <th className="px-4 py-3">Aktionen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-center text-gray-500"
                  >
                    Lade Stundenzettel…
                  </td>
                </tr>
              ) : data && data.length > 0 ? (
                data.map((timesheet) => (
                  <tr key={timesheet.id}>
                    <td className="px-4 py-3 text-gray-700">
                      {timesheet.user_name}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {timesheet.week_start} – {timesheet.week_end}
                    </td>
                    <td className="px-4 py-3 font-medium text-brand-gray">
                      {timesheet.status}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {timesheet.signed_pdf_verified
                        ? "Automatisch verifiziert"
                        : timesheet.signed_pdf_path
                        ? "Nicht verifiziert"
                        : "Fehlt"}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {timesheet.signed_pdf_verification_notes ?? "–"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link to={`/app/timesheets/${timesheet.id}`}>
                            Details
                          </Link>
                        </Button>
                        {(timesheet.status === "sent" ||
                          timesheet.status === "draft") && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleApprove(timesheet.id)}
                            disabled={approveMutation.isPending}
                          >
                            Genehmigen
                          </Button>
                        )}
                        {timesheet.status === "approved" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleReject(timesheet.id)}
                            disabled={rejectMutation.isPending}
                          >
                            Zurückweisen
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-center text-gray-500"
                  >
                    Keine Stundenzettel für den ausgewählten Zeitraum gefunden.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

