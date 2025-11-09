import { useMemo, useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import {
  useMonthlyRankQuery,
  useMonthlyStatsQuery,
} from "../../timesheets/hooks/useTimesheetStats";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export const DashboardPage = () => {
  const { data: user } = useCurrentUserQuery();
  const [month, setMonth] = useState(getCurrentMonth);

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useMonthlyStatsQuery(month);
  const { data: rankData } = useMonthlyRankQuery(month);

  const topStats = useMemo(() => stats?.stats ?? [], [stats]);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-brand-gray">
          Willkommen zurück{user ? `, ${user.name}` : ""}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Dies ist die neue Tick-Guard-Oberfläche. Funktionen werden
          schrittweise migriert.
        </p>
      </div>

      <Card>
        <CardContent className="space-y-2 py-6">
          <CardTitle className="text-base text-brand-gray">
            Angemeldete Sitzung
          </CardTitle>
          <div className="text-sm text-gray-600">
            <p>E-Mail: {user?.email ?? "–"}</p>
            <p>Rolle: {user?.role ?? "–"}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-base text-brand-gray">
              Monatsstatistik Stundenzettel
            </CardTitle>
            <div className="flex items-center gap-2">
              <label htmlFor="stats-month" className="text-sm text-gray-600">
                Monat auswählen
              </label>
              <Input
                id="stats-month"
                type="month"
                value={month}
                onChange={(event) => setMonth(event.target.value)}
              />
            </div>
          </div>

          {statsError && (
            <Alert variant="destructive">
              Statistik konnte nicht geladen werden:{" "}
              {(
                statsError.response?.data as { detail?: string } | undefined
              )?.detail ?? statsError.message}
            </Alert>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm">
              <p className="text-brand-gray">
                Eigene Platzierung (Arbeitsstunden):
              </p>
              <p className="mt-1 text-2xl font-semibold text-brand-primary">
                {rankData?.rank ? `Platz ${rankData.rank}` : "Noch keine Daten"}
              </p>
              <p className="text-xs text-gray-500">
                Gesamt: {rankData?.total_users ?? "–"} Mitarbeitende
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm">
              <p className="text-brand-gray">Datenbasis:</p>
              <p className="mt-1 text-2xl font-semibold text-brand-primary">
                {topStats.length}
              </p>
              <p className="text-xs text-gray-500">
                Nutzende mit erfassten Stundenzetteln im ausgewählten Monat
              </p>
            </div>
          </div>

          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-100 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Platz</th>
                  <th className="px-4 py-3">Mitarbeiter</th>
                  <th className="px-4 py-3">Stunden</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {statsLoading ? (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Lade Statistik…
                    </td>
                  </tr>
                ) : topStats.length > 0 ? (
                  topStats.map((stat, index) => (
                    <tr key={stat.user_id}>
                      <td className="px-4 py-3 text-gray-600">
                        {index + 1}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.user_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {stat.total_hours.toFixed(2).replace(".", ",")} h
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Für den ausgewählten Monat liegen noch keine Daten vor.
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

