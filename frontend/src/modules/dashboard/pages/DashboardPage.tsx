import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import {
  useMonthlyRankQuery,
  useMonthlyStatsQuery,
} from "../../timesheets/hooks/useTimesheetStats";
import { useAnnouncementsQuery } from "../../announcements/hooks/useAnnouncements";
import { PushNotificationButton } from "../../push/components/PushNotificationButton";

const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery();
  const [month, setMonth] = useState(getCurrentMonth);

  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useMonthlyStatsQuery(month);
  const { data: rankData } = useMonthlyRankQuery(month);
  const { data: announcements } = useAnnouncementsQuery(true);

  const topStats = useMemo(() => stats?.stats ?? [], [stats]);
  const activeAnnouncements = useMemo(
    () => announcements?.filter((a) => a.active) ?? [],
    [announcements]
  );

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
          Willkommen zurück{user ? `, ${user.name}` : ""}!
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-gray-600">
          Dies ist die neue Tick-Guard-Oberfläche. Funktionen werden
          schrittweise migriert.
        </p>
      </div>

      {activeAnnouncements.length > 0 && (
        <Card>
          <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <CardTitle className="text-sm sm:text-base text-brand-gray">
                Aktuelle Ankündigungen
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate("/app/announcements")}
                className="w-full sm:w-auto"
              >
                Alle anzeigen
              </Button>
            </div>
            <div className="space-y-3">
              {activeAnnouncements.slice(0, 3).map((announcement) => (
                <div
                  key={announcement.id}
                  className="rounded-lg border border-gray-200 bg-gray-50 p-4"
                >
                  <h3 className="font-semibold text-brand-gray">
                    {announcement.title}
                  </h3>
                  {announcement.image_url && (
                    <img
                      src={announcement.image_url}
                      alt={announcement.image_filename ?? "Ankündigung"}
                      className="mt-2 max-h-32 rounded-lg object-contain"
                    />
                  )}
                  <div
                    className="mt-2 text-sm text-gray-700"
                    dangerouslySetInnerHTML={{ __html: announcement.content }}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-base text-brand-gray">
            Angemeldete Sitzung
          </CardTitle>
          <div className="text-sm text-gray-600">
            <p>E-Mail: {user?.email ?? "–"}</p>
            <p>Rolle: {user?.role ?? "–"}</p>
          </div>
          <div className="border-t border-gray-200 pt-4">
            <PushNotificationButton />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-sm sm:text-base text-brand-gray">
              Monatsstatistik Stundenzettel
            </CardTitle>
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <label htmlFor="stats-month" className="text-xs sm:text-sm text-gray-600">
                Monat auswählen
              </label>
              <Input
                id="stats-month"
                type="month"
                value={month}
                onChange={(event) => setMonth(event.target.value)}
                className="w-full sm:w-auto"
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

          <div className="grid gap-3 sm:gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 sm:px-4 py-3 text-xs sm:text-sm">
              <p className="text-brand-gray">
                Eigene Platzierung (Arbeitsstunden):
              </p>
              <p className="mt-1 text-xl sm:text-2xl font-semibold text-brand-primary">
                {rankData?.rank ? `Platz ${rankData.rank}` : "Noch keine Daten"}
              </p>
              <p className="text-xs text-gray-500">
                Gesamt: {rankData?.total_users ?? "–"} Mitarbeitende
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 sm:px-4 py-3 text-xs sm:text-sm">
              <p className="text-brand-gray">Datenbasis:</p>
              <p className="mt-1 text-xl sm:text-2xl font-semibold text-brand-primary">
                {topStats.length}
              </p>
              <p className="text-xs text-gray-500">
                Nutzende mit erfassten Stundenzetteln im ausgewählten Monat
              </p>
            </div>
          </div>

          {/* Mobile: Card-Layout, Desktop: Tabelle */}
          <div className="block sm:hidden space-y-2">
            {statsLoading ? (
              <div className="text-center py-6 text-gray-500">Lade Statistik…</div>
            ) : topStats.length > 0 ? (
              topStats.map((stat, index) => (
                <div
                  key={stat.user_id}
                  className="rounded-lg border border-gray-200 bg-white p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-gray-600">
                        #{index + 1}
                      </span>
                      <span className="text-sm text-gray-700">{stat.user_name}</span>
                    </div>
                    <span className="text-sm font-semibold text-brand-gray">
                      {stat.total_hours.toFixed(2).replace(".", ",")} h
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-gray-500">
                Für den ausgewählten Monat liegen noch keine Daten vor.
              </div>
            )}
          </div>
          <div className="hidden sm:block overflow-x-auto rounded-lg border border-gray-200">
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

