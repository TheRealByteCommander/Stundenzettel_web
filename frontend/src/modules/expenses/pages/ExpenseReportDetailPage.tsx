import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import {
  useSubmitExpenseReportMutation,
  useTravelExpenseReportQuery,
} from "../hooks/useTravelExpenseReports";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  in_review: "In Prüfung",
  approved: "Freigegeben",
  rejected: "Zurückgewiesen",
  submitted: "Übermittelt",
};

export const ExpenseReportDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useTravelExpenseReportQuery(id);
  const submitMutation = useSubmitExpenseReportMutation();
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!id) {
    return (
      <Alert variant="destructive">
        Ungültige URL – keine Reisekostenabrechnung ausgewählt.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Reisekostenabrechnung…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Alert variant="destructive">
          Reisekostenabrechnung konnte nicht geladen werden:{" "}
          {(error?.response?.data as { detail?: string } | undefined)?.detail ??
            error?.message ??
            "Unbekannter Fehler"}
        </Alert>
        <Button className="mt-4" variant="outline" onClick={() => navigate(-1)}>
          Zurück
        </Button>
      </div>
    );
  }

  const handleSubmit = () => {
    setSubmitMessage(null);
    setSubmitError(null);
    submitMutation.mutate(data.id, {
      onSuccess: async (response) => {
        setSubmitMessage(response.message);
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setSubmitError(
          detail ?? "Einreichen der Reisekostenabrechnung fehlgeschlagen."
        );
      },
    });
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Reisekostenabrechnung {data.month}
          </h1>
          <p className="text-sm text-gray-600">
            Status: {statusLabels[data.status] ?? data.status} • Einträge:{" "}
            {data.entries.length}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate(-1)}>
          Zur Übersicht
        </Button>
      </div>

      {submitMessage && <Alert variant="success">{submitMessage}</Alert>}
      {submitError && <Alert variant="destructive">{submitError}</Alert>}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Reiseeinträge
          </CardTitle>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Datum</th>
                  <th className="px-4 py-3">Ort</th>
                  <th className="px-4 py-3">Projekt</th>
                  <th className="px-4 py-3">Fahrzeit</th>
                  <th className="px-4 py-3">Arbeitsstunden</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.entries.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Noch keine Reiseeinträge vorhanden. Bericht wurde
                      vermutlich frisch initialisiert.
                    </td>
                  </tr>
                ) : (
                  data.entries.map((entry) => (
                    <tr key={entry.date}>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(entry.date).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.location || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.customer_project || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {(entry.travel_time_minutes / 60).toLocaleString(
                          "de-DE",
                          { minimumFractionDigits: 1, maximumFractionDigits: 1 }
                        )}{" "}
                        h
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.working_hours.toLocaleString("de-DE", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        })}{" "}
                        h
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500">
            Einträge werden automatisch aus freigegebenen Stundenzetteln
            generiert. Ergänzungen (z. B. zusätzliche Reisetage) folgen in einem
            späteren Schritt.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Belege & Dokumente (Preview)
          </CardTitle>
          <p className="text-sm text-gray-600">
            Die Backend-API unterstützt bereits das Hochladen verschlüsselter
            PDFs und optionaler Fremdwährungsnachweise. Die UI-Anbindung erfolgt
            in den nächsten Schritten. Aktueller Status:
          </p>
          {data.receipts.length === 0 ? (
            <Alert>
              Noch keine Belege vorhanden. Nutzen Sie in Kürze den Upload-Dialog,
              um Dokumente anzuhängen.
            </Alert>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Dateiname</th>
                    <th className="px-4 py-3">Größe</th>
                    <th className="px-4 py-3">Fremdwährung</th>
                    <th className="px-4 py-3">Nachweis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.receipts.map((receipt) => (
                    <tr key={receipt.id}>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.filename}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {(receipt.file_size / 1024).toLocaleString("de-DE", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        })}{" "}
                        KB
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.currency ?? "EUR"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.exchange_proof_filename
                          ? "Nachweis vorhanden"
                          : receipt.needs_exchange_proof
                          ? "Nachweis erforderlich"
                          : "–"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Bericht einreichen
          </CardTitle>
          <p className="text-sm text-gray-600">
            Vor dem Einreichen müssen alle zugehörigen Stundenzettel freigegeben
            und unterschrieben sein. Das Backend validiert dies automatisch.
          </p>
          <Button
            onClick={handleSubmit}
            disabled={
              submitMutation.isPending ||
              data.status !== "draft" ||
              data.entries.length === 0
            }
          >
            {submitMutation.isPending ? "Reicht ein…" : "Bericht einreichen"}
          </Button>
          {data.status !== "draft" && (
            <p className="text-xs text-gray-500">
              Der Bericht befindet sich bereits im Status „
              {statusLabels[data.status] ?? data.status}“.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

