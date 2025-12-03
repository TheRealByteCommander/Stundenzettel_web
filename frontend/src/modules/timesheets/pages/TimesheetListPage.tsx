import { Link } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  useDeleteTimesheetMutation,
  useTimesheetsQuery,
} from "../hooks/useTimesheets";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  sent: "Gesendet",
  approved: "Genehmigt",
};

const getIsoWeekNumber = (dateString: string) => {
  const date = new Date(dateString);
  const target = new Date(date.valueOf());
  const dayNumber = (date.getUTCDay() + 6) % 7;
  target.setUTCDate(target.getUTCDate() - dayNumber + 3);
  const firstThursday = new Date(Date.UTC(target.getUTCFullYear(), 0, 4));
  const diff =
    (target.valueOf() - firstThursday.valueOf()) / (7 * 24 * 60 * 60 * 1000);
  return `KW${String(1 + Math.floor(diff)).padStart(2, "0")}`;
};

export const TimesheetListPage = () => {
  const { data, isLoading, error } = useTimesheetsQuery();
  const deleteMutation = useDeleteTimesheetMutation();

  const handleDelete = (id: string) => {
    if (
      window.confirm(
        "Stundenzettel wirklich löschen? Dieser Vorgang kann nicht rückgängig gemacht werden."
      )
    ) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
            Stundenzettel
          </h1>
          <p className="text-xs sm:text-sm text-gray-600">
            Übersicht Ihrer Wochen-Stundenzettel. Funktionen werden während der
            Migration erweitert.
          </p>
        </div>
        <Button asChild className="w-full sm:w-auto">
          <Link to="/app/timesheets/new">Neuer Stundenzettel</Link>
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          Stundenzettel konnten nicht geladen werden:{" "}
          {(
            error.response?.data as { detail?: string } | undefined
          )?.detail ?? error.message}
        </Alert>
      )}

      {/* Mobile: Card-Layout, Desktop: Tabelle */}
      <div className="block sm:hidden space-y-3">
        {isLoading ? (
          <div className="text-center py-6 text-gray-500">Lade Stundenzettel…</div>
        ) : data && data.length > 0 ? (
          data.map((timesheet) => (
            <div
              key={timesheet.id}
              className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <div>
                  <p className="font-semibold text-brand-gray">
                    {getIsoWeekNumber(timesheet.week_start)}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {new Date(timesheet.week_start).toLocaleDateString("de-DE")}{" "}
                    – {new Date(timesheet.week_end).toLocaleDateString("de-DE")}
                  </p>
                </div>
                <span className="text-xs font-medium text-gray-600">
                  {statusLabels[timesheet.status] ?? timesheet.status}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" asChild className="flex-1 sm:flex-none">
                  <Link to={`/app/timesheets/${timesheet.id}`}>
                    Anzeigen
                  </Link>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(timesheet.id)}
                  disabled={deleteMutation.isPending}
                  className="flex-1 sm:flex-none"
                >
                  Löschen
                </Button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-6 text-gray-500">
            Noch keine Stundenzettel vorhanden.
          </div>
        )}
      </div>
      <div className="hidden sm:block overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
            <tr>
              <th className="px-4 py-3">Kalenderwoche</th>
              <th className="px-4 py-3">Zeitraum</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Aktionen</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                  Lade Stundenzettel…
                </td>
              </tr>
            ) : data && data.length > 0 ? (
              data.map((timesheet) => (
                <tr key={timesheet.id}>
                  <td className="px-4 py-3 font-medium text-brand-gray">
                    {getIsoWeekNumber(timesheet.week_start)}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(timesheet.week_start).toLocaleDateString("de-DE")}{" "}
                    –{" "}
                    {new Date(timesheet.week_end).toLocaleDateString("de-DE")}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {statusLabels[timesheet.status] ?? timesheet.status}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" asChild>
                        <Link to={`/app/timesheets/${timesheet.id}`}>
                          Anzeigen
                        </Link>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(timesheet.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Löschen
                      </Button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                  Noch keine Stundenzettel vorhanden.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

