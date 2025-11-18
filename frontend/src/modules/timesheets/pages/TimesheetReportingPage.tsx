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
import type { WeeklyTimesheet } from "../../../services/api/types";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

const exportToCSV = (data: WeeklyTimesheet[], filename: string) => {
  const headers = [
    "ID",
    "Mitarbeiter",
    "Woche Start",
    "Woche Ende",
    "Status",
    "Einträge",
    "Erstellt am",
  ];
  
  const rows = data.map((ts) => [
    ts.id,
    ts.user_name,
    ts.week_start,
    ts.week_end,
    ts.status,
    ts.entries.length.toString(),
    ts.created_at || "",
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const exportStatsToCSV = (stats: any[], month: string) => {
  const headers = ["Mitarbeiter", "Gesamtstunden", "Stundenzettel"];
  const rows = stats.map((stat) => [
    stat.user_name,
    stat.total_hours.toFixed(2),
    stat.timesheets_count || 0,
  ]);

  const csvContent = [
    headers.join(","),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
  ].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `timesheet-stats-${month}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const TimesheetReportingPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAdmin = user?.role === "admin" || user?.role === "accounting";
  const [month, setMonth] = useState(getCurrentMonth);
  const [selectedUser, setSelectedUser] = useState<string>("");

  const { data: allTimesheets, isLoading: timesheetsLoading } = useTimesheetsQuery();
  const { data: stats } = useMonthlyStatsQuery(month);
  const { data: accountingTimesheets } = useAccountingTimesheetsQuery({
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

  const handleExportAll = () => {
    if (filteredTimesheets.length === 0) {
      alert("Keine Daten zum Exportieren vorhanden.");
      return;
    }
    exportToCSV(filteredTimesheets, `timesheets-${month}.csv`);
  };

  const handleExportStats = () => {
    if (!stats || stats.stats.length === 0) {
      alert("Keine Statistiken zum Exportieren vorhanden.");
      return;
    }
    exportStatsToCSV(stats.stats, month);
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
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg text-brand-gray">
              Export-Funktionen
            </CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleExportAll}>
                Alle als CSV exportieren
              </Button>
              <Button variant="outline" onClick={handleExportStats}>
                Statistiken als CSV exportieren
              </Button>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Exportieren Sie alle Stundenzettel oder Statistiken für den
            ausgewählten Monat als CSV-Datei.
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

      {stats && stats.stats.length > 0 && (
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
                  {stats.stats.map((stat) => (
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

