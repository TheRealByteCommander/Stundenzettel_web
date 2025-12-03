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
import { useAdminUsersQuery } from "../hooks/useAdminUsers";
import {
  useVacationBalanceQuery,
  useUpdateVacationBalanceMutation,
} from "../../vacation/hooks/useVacation";
import type { VacationBalance } from "../../../services/api/vacation";

const getCurrentYear = () => new Date().getFullYear();

export const VacationBalancePage = () => {
  const [year, setYear] = useState(getCurrentYear());
  const { data: users, isLoading: usersLoading } = useAdminUsersQuery();
  const { data: balances, isLoading: balancesLoading } = useVacationBalanceQuery();
  const updateMutation = useUpdateVacationBalanceMutation();
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, number>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filter balances for current year
  const yearBalances = balances?.filter((b) => b.year === year) || [];

  // Create a map of user_id -> balance for easy lookup
  const balanceMap = new Map<string, VacationBalance>();
  yearBalances.forEach((b) => {
    balanceMap.set(b.user_id, b);
  });

  const handleEdit = (userId: string, currentTotalDays: number) => {
    setEditingId(userId);
    setEditValues({ [userId]: currentTotalDays });
    setMessage(null);
    setError(null);
  };

  const handleSave = async (userId: string) => {
    const newTotalDays = editValues[userId];
    if (newTotalDays === undefined || newTotalDays < 0) {
      setError("Ungültige Anzahl von Urlaubstagen");
      return;
    }

    try {
      await updateMutation.mutateAsync({
        userId,
        year,
        payload: { total_days: newTotalDays },
      });
      setEditingId(null);
      setEditValues({});
      setMessage("Urlaubsguthaben erfolgreich aktualisiert");
      setError(null);
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Aktualisieren";
      setError(errorMessage);
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditValues({});
    setError(null);
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
            Urlaubsguthaben-Verwaltung
          </h1>
          <p className="text-xs sm:text-sm text-gray-600">
            Verwalten Sie die Urlaubstage für alle Mitarbeiter pro Jahr.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="year-select" className="text-sm">Jahr:</Label>
          <Input
            id="year-select"
            type="number"
            min="2020"
            max="2100"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24"
          />
        </div>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="destructive">{error}</Alert>}

      <Card>
        <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Urlaubsguthaben für {year}
          </CardTitle>

          {usersLoading || balancesLoading ? (
            <p className="text-center text-gray-500 py-6">Lade Daten…</p>
          ) : (
            <>
              {/* Mobile: Card-Layout */}
              <div className="block sm:hidden space-y-3">
                {users?.map((user) => {
                  const balance = balanceMap.get(user.id);
                  const isEditing = editingId === user.id;
                  const currentTotalDays = balance?.total_days ?? 0;
                  const usedDays = balance?.used_days ?? 0;
                  const availableDays = currentTotalDays - usedDays;

                  return (
                    <div
                      key={user.id}
                      className="rounded-lg border border-gray-200 bg-white p-4"
                    >
                      <div className="mb-3">
                        <p className="font-semibold text-brand-gray">{user.name}</p>
                        <p className="text-xs text-gray-600">{user.email}</p>
                      </div>
                      {isEditing ? (
                        <div className="space-y-2">
                          <Label className="text-sm">Gesamttage:</Label>
                          <Input
                            type="number"
                            min="0"
                            value={editValues[user.id] ?? currentTotalDays}
                            onChange={(e) =>
                              setEditValues({
                                ...editValues,
                                [user.id]: Number(e.target.value),
                              })
                            }
                          />
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              onClick={() => handleSave(user.id)}
                              disabled={updateMutation.isPending}
                              className="flex-1"
                            >
                              Speichern
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={handleCancel}
                              className="flex-1"
                            >
                              Abbrechen
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div className="text-sm text-gray-600">
                            <p>Gesamt: <strong>{currentTotalDays}</strong> Tage</p>
                            <p>Verbraucht: <strong>{usedDays}</strong> Tage</p>
                            <p>Verfügbar: <strong className="text-brand-primary">{availableDays}</strong> Tage</p>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(user.id, currentTotalDays)}
                            className="w-full"
                          >
                            Bearbeiten
                          </Button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Desktop: Tabelle */}
              <div className="hidden sm:block overflow-x-auto rounded-lg border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                    <tr>
                      <th className="px-4 py-3">Mitarbeiter</th>
                      <th className="px-4 py-3">E-Mail</th>
                      <th className="px-4 py-3">Gesamttage</th>
                      <th className="px-4 py-3">Verbraucht</th>
                      <th className="px-4 py-3">Verfügbar</th>
                      <th className="px-4 py-3">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users?.map((user) => {
                      const balance = balanceMap.get(user.id);
                      const isEditing = editingId === user.id;
                      const currentTotalDays = balance?.total_days ?? 0;
                      const usedDays = balance?.used_days ?? 0;
                      const availableDays = currentTotalDays - usedDays;

                      return (
                        <tr key={user.id}>
                          <td className="px-4 py-3 font-medium text-brand-gray">
                            {user.name}
                          </td>
                          <td className="px-4 py-3 text-gray-600 text-xs">
                            {user.email}
                          </td>
                          {isEditing ? (
                            <>
                              <td className="px-4 py-3">
                                <Input
                                  type="number"
                                  min="0"
                                  value={editValues[user.id] ?? currentTotalDays}
                                  onChange={(e) =>
                                    setEditValues({
                                      ...editValues,
                                      [user.id]: Number(e.target.value),
                                    })
                                  }
                                  className="w-24"
                                />
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {usedDays}
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {(editValues[user.id] ?? currentTotalDays) - usedDays}
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => handleSave(user.id)}
                                    disabled={updateMutation.isPending}
                                  >
                                    Speichern
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={handleCancel}
                                  >
                                    Abbrechen
                                  </Button>
                                </div>
                              </td>
                            </>
                          ) : (
                            <>
                              <td className="px-4 py-3 text-gray-600">
                                {currentTotalDays}
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {usedDays}
                              </td>
                              <td className="px-4 py-3 font-semibold text-brand-primary">
                                {availableDays}
                              </td>
                              <td className="px-4 py-3">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEdit(user.id, currentTotalDays)}
                                >
                                  Bearbeiten
                                </Button>
                              </td>
                            </>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

