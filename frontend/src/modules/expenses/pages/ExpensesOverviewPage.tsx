import { Link, useNavigate } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { useTravelExpensesQuery } from "../hooks/useTravelExpenses";
import {
  useExpenseReportMonthsQuery,
  useInitializeExpenseReportMutation,
} from "../hooks/useTravelExpenseReports";
import { useState } from "react";

export const ExpensesOverviewPage = () => {
  const { data, isLoading, error } = useTravelExpensesQuery();
  const { data: months, isLoading: monthsLoading, error: monthsError } =
    useExpenseReportMonthsQuery();
  const initializeMutation = useInitializeExpenseReportMutation();
  const navigate = useNavigate();
  const [initializeMessage, setInitializeMessage] = useState<string | null>(
    null
  );
  const [initializeError, setInitializeError] = useState<string | null>(null);

  const handleInitialize = (month: string) => {
    setInitializeMessage(null);
    setInitializeError(null);
    initializeMutation.mutate(month, {
      onSuccess: (report) => {
        setInitializeMessage(
          `Bericht für ${report.month} wurde vorbereitet.`
        );
        navigate(`/app/expenses/reports/${report.id}`);
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setInitializeError(
          detail ?? "Bericht konnte nicht initialisiert werden."
        );
      },
    });
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Reisekosten & Belege
          </h1>
          <p className="text-sm text-gray-600">
            Iteration 4 Vorbereitung: Übersicht über eingereichte Reisekosten,
            Einstieg in Upload- und Prüfprozesse.
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link to="/app/timesheets">
            Stundenzettel öffnen
          </Link>
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          Reisekosten konnten nicht geladen werden:{" "}
          {(error.response?.data as { detail?: string } | undefined)?.detail ??
            error.message}
        </Alert>
      )}
      {monthsError && (
        <Alert variant="destructive">
          Verfügbare Monate konnten nicht geladen werden:{" "}
          {(monthsError.response?.data as { detail?: string } | undefined)
            ?.detail ?? monthsError.message}
        </Alert>
      )}
      {initializeMessage && <Alert variant="success">{initializeMessage}</Alert>}
      {initializeError && <Alert variant="destructive">{initializeError}</Alert>}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardContent className="space-y-3 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Ablaufkonzept
            </CardTitle>
            <p className="text-sm text-gray-600">
              Iteration 4 verknüpft genehmigte Stundenzettel mit
              Reisekostenberichten. Der geplante Flow:
            </p>
            <ol className="list-decimal space-y-1 pl-4 text-sm text-gray-600">
              <li>
                Wochenabschluss: genehmigter Stundenzettel erzeugt Draft
                Reisekostenbericht.
              </li>
              <li>
                Mitarbeitende laden Belege pro Reisetag hoch (PDF/JPG) – optional
                mit Fremdwährungsnachweis.
              </li>
              <li>
                Chat/Kommentarfunktion für Nachfragen durch Buchhaltung.
              </li>
              <li>
                Statuswechsel: <em>draft → submitted → in_review → approved</em>.
              </li>
            </ol>
            <p className="text-sm text-gray-600">
              Diese Karte dient als Referenz beim schrittweisen Ausbau der
              Module. Technische Grundlage: neue API-Clients +
              React-Query-Hooks.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Nächste UI-Schritte
            </CardTitle>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>
                Filterleiste mit Monat/Status und Badge für offene Aufgaben.
              </li>
              <li>
                Tabelle der Reisekosten (Kilometer, Betrag, Status) mit
                Aktionen: „Belege prüfen“, „Chat öffnen“.
              </li>
              <li>
                Drawer/Modal für neuen Beleg-Upload (FormData → `/travel-expenses`).
              </li>
              <li>
                Split-View für Detailseite (`/app/expenses/reports/:id`) inkl.
                Chat-Panel und Dokumentenvorschau.
              </li>
            </ul>
            <p className="text-sm text-gray-600">
              Die jetzt angelegten Query-Hooks decken die CRUD- und
              Freigabe-Endpunkte bereits ab.
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Monatsberichte initialisieren
          </CardTitle>
          <p className="text-sm text-gray-600">
            Wählen Sie einen Monat aus, um eine neue Reisekostenabrechnung zu
            erstellen. Der Bericht übernimmt automatisch alle freigegebenen
            Stundenzettel dieses Monats.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            {monthsLoading
              ? Array.from({ length: 3 }).map((_, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-center text-sm text-gray-500"
                  >
                    Lade Monate…
                  </div>
                ))
              : months?.map((month) => (
                  <div
                    key={month.value}
                    className="rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-700"
                  >
                    <p className="font-medium text-brand-gray">{month.label}</p>
                    <p className="mt-1 text-xs text-gray-500">
                      {month.value}
                    </p>
                    <Button
                      className="mt-3 w-full"
                      variant="outline"
                      onClick={() => handleInitialize(month.value)}
                      disabled={initializeMutation.isPending}
                    >
                      {initializeMutation.isPending
                        ? "Init…"
                        : "Bericht erstellen"}
                    </Button>
                  </div>
                ))}
          </div>
          <p className="text-xs text-gray-500">
            Bereits erstellte Berichte werden beim erneuten Initialisieren nicht
            dupliziert – das Backend liefert den vorhandenen Datensatz zurück.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="py-6">
          <CardTitle className="text-lg text-brand-gray">
            Eingereichte Reisekosten
          </CardTitle>
          <div className="mt-4 overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Datum</th>
                  <th className="px-4 py-3">Beschreibung</th>
                  <th className="px-4 py-3">Kilometer</th>
                  <th className="px-4 py-3">Kosten</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {isLoading ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Lade Reisekosten…
                    </td>
                  </tr>
                ) : data && data.length > 0 ? (
                  data.map((expense) => (
                    <tr key={expense.id}>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(expense.date).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {expense.description}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {expense.kilometers?.toLocaleString("de-DE", {
                          maximumFractionDigits: 1,
                        }) ?? 0}{" "}
                        km
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {expense.expenses?.toLocaleString("de-DE", {
                          style: "currency",
                          currency: "EUR",
                          minimumFractionDigits: 2,
                        }) ?? "0,00 €"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {expense.status ?? "draft"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Noch keine Reisekosten erfasst.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

