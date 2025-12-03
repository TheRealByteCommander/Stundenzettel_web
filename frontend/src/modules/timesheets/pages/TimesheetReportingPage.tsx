import { useMemo, useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { useTimesheetsQuery } from "../hooks/useTimesheets";
import { useMonthlyStatsQuery } from "../hooks/useTimesheetStats";
import { useAccountingTimesheetsQuery } from "../hooks/useAccountingTimesheets";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import { downloadTimesheetPDF } from "../../../services/api/timesheets";
import {
  exportTimesheetsToCSV,
  exportTimesheetsToJSON,
  exportTimesheetsToExcel,
  exportToJSON,
  exportToCSV,
  exportToExcel,
} from "../../../utils/export";
import type { AccountingMonthlyStat } from "../../../services/api/admin";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

const exportStatsToCSV = (stats: AccountingMonthlyStat[], month: string) => {
  const data = stats.map((stat) => ({
    Mitarbeiter: stat.user_name,
    Gesamtstunden: stat.total_hours.toFixed(2),
    "Stundenzettel-Stunden": stat.hours_on_timesheets.toFixed(2),
    Reisestunden: stat.travel_hours.toFixed(2),
    Reisekilometer: stat.travel_kilometers.toFixed(2),
    Reisekosten: stat.travel_expenses.toFixed(2),
    Stundenzettel: stat.timesheets_count || 0,
  }));
  
  exportToCSV(data, `timesheet-stats-${month}.csv`);
};

export const TimesheetReportingPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAdmin = user?.role === "admin" || user?.role === "accounting";
  const [month, setMonth] = useState(getCurrentMonth);
  const [selectedUser] = useState<string>("");

  const { data: allTimesheets, isLoading: timesheetsLoading } = useTimesheetsQuery();
  const { data: stats } = useAccountingMonthlyStatsQuery(month);
  useAccountingTimesheetsQuery({
    month,
    userId: selectedUser || undefined,
  });

  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  const filteredTimesheets = useMemo(() => {
    if (!allTimesheets) return [];
    return allTimesheets.filter((ts) => {
      const tsMonth = ts.week_start.substring(0, 7);
      return tsMonth === month;
    });
  }, [allTimesheets, month]);

  const handleDownloadPDF = async (id: string, userName: string, weekStart: string) => {
    setDownloadingIds((prev) => new Set(prev).add(id));
    try {
      const blob = await downloadTimesheetPDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Stundenzettel_${userName}_${weekStart}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Fehler beim Download:", error);
      alert("Fehler beim Download des PDFs.");
    } finally {
      setDownloadingIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleExportAll = (format: "csv" | "json" | "excel") => {
    if (filteredTimesheets.length === 0) {
      alert("Keine Daten zum Exportieren vorhanden.");
      return;
    }
    const filename = `timesheets-${month}`;
    if (format === "csv") {
      exportTimesheetsToCSV(filteredTimesheets, `${filename}.csv`);
    } else if (format === "json") {
      exportTimesheetsToJSON(filteredTimesheets, filename);
    } else if (format === "excel") {
      exportTimesheetsToExcel(filteredTimesheets, filename);
    }
  };

  const handleExportStats = (format: "csv" | "json" | "excel") => {
    if (!stats || stats.length === 0) {
      alert("Keine Statistiken zum Exportieren vorhanden.");
      return;
    }
    const filename = `timesheet-stats-${month}`;
    if (format === "csv") {
      exportStatsToCSV(stats, month);
    } else if (format === "json") {
      exportToJSON(stats, `${filename}.json`);
    } else if (format === "excel") {
      const data = stats.map((stat) => ({
        Mitarbeiter: stat.user_name,
        Gesamtstunden: stat.total_hours.toFixed(2),
        "Stundenzettel-Stunden": stat.hours_on_timesheets.toFixed(2),
        Reisestunden: stat.travel_hours.toFixed(2),
        Reisekilometer: stat.travel_kilometers.toFixed(2),
        Reisekosten: stat.travel_expenses.toFixed(2),
        Stundenzettel: stat.timesheets_count || 0,
      }));
      exportToExcel(data, filename, "Statistiken");
    }
  };

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Alert variant="destructive">
          Sie haben keine Berechtigung, auf diese Seite zuzugreifen.
        </Alert>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Timesheet-Reporting
          </h1>
          <p className="text-sm text-gray-600">
            Export-Funktionen und aggregierte Ansichten für Stundenzettel.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="report-month">Monat:</Label>
          <Input
            id="report-month"
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
          />
        </div>
      </div>

      <Card>
        <CardContent className="space-y-4 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="text-lg text-brand-gray">
              Export-Funktionen
            </CardTitle>
            <div className="flex flex-wrap gap-2">
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-gray-600">Stundenzettel:</Label>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => handleExportAll("csv")}>
                    CSV
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleExportAll("json")}>
                    JSON
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleExportAll("excel")}>
                    Excel
                  </Button>
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <Label className="text-xs text-gray-600">Statistiken:</Label>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" onClick={() => handleExportStats("csv")}>
                    CSV
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleExportStats("json")}>
                    JSON
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => handleExportStats("excel")}>
                    Excel
                  </Button>
                </div>
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Exportieren Sie alle Stundenzettel oder Statistiken für den
            ausgewählten Monat in verschiedenen Formaten (CSV, JSON, Excel).
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Stundenzettel für {month}
          </CardTitle>
          {timesheetsLoading ? (
            <p className="text-center text-gray-500">Lade Stundenzettel…</p>
          ) : filteredTimesheets.length > 0 ? (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Mitarbeiter</th>
                    <th className="px-4 py-3">Woche</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Einträge</th>
                    <th className="px-4 py-3">Aktionen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredTimesheets.map((timesheet) => (
                    <tr key={timesheet.id}>
                      <td className="px-4 py-3 text-gray-600">
                        {timesheet.user_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(timesheet.week_start).toLocaleDateString("de-DE")}{" "}
                        – {new Date(timesheet.week_end).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {timesheet.status}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {timesheet.entries.length}
                      </td>
                      <td className="px-4 py-3">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            handleDownloadPDF(
                              timesheet.id,
                              timesheet.user_name,
                              timesheet.week_start
                            )
                          }
                          disabled={downloadingIds.has(timesheet.id)}
                        >
                          {downloadingIds.has(timesheet.id)
                            ? "Lädt…"
                            : "PDF herunterladen"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center text-gray-500">
              Keine Stundenzettel für den ausgewählten Monat vorhanden.
            </p>
          )}
        </CardContent>
      </Card>

      {stats && stats.length > 0 && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Aggregierte Statistiken für {month}
            </CardTitle>
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Mitarbeiter</th>
                    <th className="px-4 py-3">Gesamtstunden</th>
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
                        {stat.total_hours > 0 ? "✓" : "–"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

