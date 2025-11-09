import { useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  useApproveTimesheetMutation,
  useRejectTimesheetMutation,
  useSendTimesheetEmailMutation,
  useTimesheetQuery,
} from "../hooks/useTimesheets";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  sent: "Gesendet",
  approved: "Genehmigt",
};

export const TimesheetDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data, isLoading, error } = useTimesheetQuery(id);
  const approveMutation = useApproveTimesheetMutation(id ?? "");
  const rejectMutation = useRejectTimesheetMutation(id ?? "");
  const sendMutation = useSendTimesheetEmailMutation(id ?? "");

  const totalHours = useMemo(() => {
    if (!data) return 0;
    return data.entries.reduce((acc, entry) => {
      const start = new Date(`1970-01-01T${entry.start_time}:00`);
      const end = new Date(`1970-01-01T${entry.end_time}:00`);
      const diff =
        (end.getTime() - start.getTime()) / 1000 / 60 - entry.break_minutes;
      return acc + Math.max(diff, 0) / 60;
    }, 0);
  }, [data]);

  if (!id) {
    return (
      <Alert variant="destructive">
        Ungültige URL. Bitte kehren Sie zur Übersicht zurück.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Stundenzettel…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Alert variant="destructive">
          Stundenzettel konnte nicht geladen werden:{" "}
          {(
            error?.response?.data as { detail?: string } | undefined
          )?.detail ?? error?.message ?? "Unbekannter Fehler"}
        </Alert>
        <Button className="mt-4" variant="outline" onClick={() => navigate(-1)}>
          Zurück
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      <Button variant="outline" onClick={() => navigate(-1)}>
        Zurück zur Übersicht
      </Button>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-brand-gray">
              Stundenzettel {new Date(data.week_start).toLocaleDateString("de-DE")}{" "}
              – {new Date(data.week_end).toLocaleDateString("de-DE")}
            </h1>
            <p className="text-sm text-gray-600">
              Status: {statusLabels[data.status] ?? data.status} • Gesamtstunden:{" "}
              {totalHours.toFixed(2).replace(".", ",")}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending}
            >
              Per E-Mail senden
            </Button>
            <Button
              variant="outline"
              onClick={() => approveMutation.mutate()}
              disabled={approveMutation.isPending || data.status === "approved"}
            >
              Genehmigen
            </Button>
            <Button
              variant="outline"
              onClick={() => rejectMutation.mutate()}
              disabled={rejectMutation.isPending}
            >
              Ablehnen
            </Button>
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
              <tr>
                <th className="px-4 py-3">Datum</th>
                <th className="px-4 py-3">Start</th>
                <th className="px-4 py-3">Ende</th>
                <th className="px-4 py-3">Pause</th>
                <th className="px-4 py-3">Aufgaben</th>
                <th className="px-4 py-3">Projekt</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.entries.map((entry, index) => (
                <tr key={`${entry.date}-${index}`}>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(entry.date).toLocaleDateString("de-DE")}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{entry.start_time}</td>
                  <td className="px-4 py-3 text-gray-600">{entry.end_time}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {entry.break_minutes} Min
                  </td>
                  <td className="px-4 py-3 text-gray-600">{entry.tasks}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {entry.customer_project || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

