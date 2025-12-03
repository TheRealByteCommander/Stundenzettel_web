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
import { exportToCSV, exportToJSON, exportToExcel } from "../../../utils/export";
import { SimpleBarChart } from "../../../components/charts/SimpleBarChart";

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
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleDownloadPDF}
              disabled={downloadMutation.isPending}
              size="sm"
            >
              {downloadMutation.isPending ? "Lade…" : "PDF"}
            </Button>
            {stats && stats.length > 0 && (
              <>
                <Button
                  variant="outline"
                  onClick={() => {
                    const data = stats.map((stat) => ({
                      Mitarbeiter: stat.user_name,
                      Gesamtstunden: stat.total_hours.toFixed(2),
                      "Stundenzettel-Stunden": stat.hours_on_timesheets.toFixed(2),
                      Reisestunden: stat.travel_hours.toFixed(2),
                      Reisekilometer: stat.travel_kilometers.toFixed(2),
                      Reisekosten: stat.travel_expenses.toFixed(2),
                      Stundenzettel: stat.timesheets_count || 0,
                    }));
                    exportToCSV(data, `accounting-stats-${month}.csv`);
                  }}
                  size="sm"
                >
                  CSV
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    exportToJSON(stats, `accounting-stats-${month}.json`);
                  }}
                  size="sm"
                >
                  JSON
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    const data = stats.map((stat) => ({
                      Mitarbeiter: stat.user_name,
                      Gesamtstunden: stat.total_hours.toFixed(2),
                      "Stundenzettel-Stunden": stat.hours_on_timesheets.toFixed(2),
                      Reisestunden: stat.travel_hours.toFixed(2),
                      Reisekilometer: stat.travel_kilometers.toFixed(2),
                      Reisekosten: stat.travel_expenses.toFixed(2),
                      Stundenzettel: stat.timesheets_count || 0,
                    }));
                    exportToExcel(data, `accounting-stats-${month}`, "Buchhaltung");
                  }}
                  size="sm"
                >
                  Excel
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          Statistiken konnten nicht geladen werden:{" "}
          {error instanceof Error
            ? error.message
            : typeof error === "object" && error !== null && "message" in error
              ? String((error as { message: unknown }).message)
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

      {stats && stats.length > 0 && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Visualisierungen
            </CardTitle>
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <SimpleBarChart
                  data={stats.map((stat) => ({
                    label: stat.user_name,
                    value: stat.total_hours,
                    color: "#e90118",
                  }))}
                  title="Gesamtstunden pro Mitarbeiter"
                  height={250}
                />
              </div>
              <div>
                <SimpleBarChart
                  data={stats.map((stat) => ({
                    label: stat.user_name,
                    value: stat.travel_expenses,
                    color: "#3b82f6",
                  }))}
                  title="Reisekosten pro Mitarbeiter (€)"
                  height={250}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

