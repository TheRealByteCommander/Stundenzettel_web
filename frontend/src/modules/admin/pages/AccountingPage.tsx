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
import {
  useAccountingMonthlyStatsQuery,
  useDownloadAccountingReportMutation,
} from "../hooks/useAdminSettings";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export const AccountingPage = () => {
  const [month, setMonth] = useState(getCurrentMonth());
  const { data: stats, isLoading, error } = useAccountingMonthlyStatsQuery(month);
  const downloadMutation = useDownloadAccountingReportMutation();

  const handleDownloadPDF = async () => {
    try {
      const blob = await downloadMutation.mutateAsync(month);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Buchhaltungsbericht_${month}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Fehler beim Download:", err);
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Buchhaltungs-Übersicht
          </h1>
          <p className="text-sm text-gray-600">
            Monatliche Statistiken für die Buchhaltung.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="accounting-month">Monat:</Label>
          <Input
            id="accounting-month"
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
          />
          <Button
            variant="outline"
            onClick={handleDownloadPDF}
            disabled={downloadMutation.isPending}
          >
            {downloadMutation.isPending ? "Lade…" : "PDF exportieren"}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          Statistiken konnten nicht geladen werden:{" "}
          {error instanceof Error
            ? error.message
            : typeof error === "object" && error !== null && "message" in error
              ? String(error.message)
              : "Unbekannter Fehler"}
        </Alert>
      )}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Monatsstatistik {month}
          </CardTitle>
          {isLoading ? (
            <p className="text-center text-gray-500">Lade Statistiken…</p>
          ) : stats && stats.length > 0 ? (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Mitarbeiter</th>
                    <th className="px-4 py-3">Gesamtstunden</th>
                    <th className="px-4 py-3">Stundenzettel-Stunden</th>
                    <th className="px-4 py-3">Reisestunden</th>
                    <th className="px-4 py-3">Reisekilometer</th>
                    <th className="px-4 py-3">Reisekosten</th>
                    <th className="px-4 py-3">Stundenzettel</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {stats.map((stat) => (
                    <tr key={stat.user_id}>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.user_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.total_hours.toFixed(2).replace(".", ",")} h
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.hours_on_timesheets.toFixed(2).replace(".", ",")} h
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.travel_hours.toFixed(2).replace(".", ",")} h
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.travel_kilometers.toFixed(2).replace(".", ",")} km
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.travel_expenses.toFixed(2).replace(".", ",")} €
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.timesheets_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center text-gray-500">
              Für den ausgewählten Monat liegen noch keine Daten vor.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

