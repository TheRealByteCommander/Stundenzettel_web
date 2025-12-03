import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import {
  useCreateTimesheetMutation,
  useTimesheetsQuery,
} from "../hooks/useTimesheets";
import { useAvailableVehiclesQuery } from "../hooks/useAvailableVehicles";
import { useCustomersQuery } from "../hooks/useCustomers";
import type { TimeEntry } from "../../../services/api/types";

const defaultEntry: TimeEntry = {
  date: new Date().toISOString().split("T")[0],
  start_time: "",
  end_time: "",
  break_minutes: 0,
  tasks: "",
  customer_project: "",
  location: "",
  absence_type: null,
  travel_time_minutes: 0,
  include_travel_time: false,
  vehicle_id: null,
};

// Helper function to get Monday of a given date
const getMonday = (date: Date): Date => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
  return new Date(d.setDate(diff));
};

// Helper function to generate week entries (Monday to Friday only)
const generateWeekEntries = (weekStartDate: string, weekVehicleId: string | null): TimeEntry[] => {
  const start = new Date(weekStartDate);
  const entries: TimeEntry[] = [];
  
  // Nur Montag bis Freitag (5 Tage)
  for (let i = 0; i < 5; i++) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    entries.push({
      ...defaultEntry,
      date: date.toISOString().split("T")[0],
      vehicle_id: weekVehicleId,
    });
  }
  
  return entries;
};

// Helper function to get Saturday date
const getSaturday = (weekStartDate: string): string => {
  const start = new Date(weekStartDate);
  start.setDate(start.getDate() + 5); // Samstag ist 5 Tage nach Montag
  return start.toISOString().split("T")[0];
};

// Helper function to get Sunday date
const getSunday = (weekStartDate: string): string => {
  const start = new Date(weekStartDate);
  start.setDate(start.getDate() + 6); // Sonntag ist 6 Tage nach Montag
  return start.toISOString().split("T")[0];
};

export const TimesheetCreatePage = () => {
  const navigate = useNavigate();
  const { refetch } = useTimesheetsQuery();
  const createMutation = useCreateTimesheetMutation();
  const { data: vehicles, isLoading: vehiclesLoading, error: vehiclesError } =
    useAvailableVehiclesQuery();
  const { data: customers, isLoading: customersLoading } = useCustomersQuery();
  
  // Initialize with Monday of current week
  const initialMonday = getMonday(new Date()).toISOString().split("T")[0];
  const [weekStart, setWeekStart] = useState(initialMonday);
  const [weekVehicleId, setWeekVehicleId] = useState<string>("");
  const [entries, setEntries] = useState<TimeEntry[]>(() => 
    generateWeekEntries(initialMonday, null)
  );
  const [error, setError] = useState<string | null>(null);
  const vehicleOptions = useMemo(
    () =>
      vehicles?.map((vehicle) => ({
        value: vehicle.id,
        label: `${vehicle.name} (${vehicle.license_plate})${
          vehicle.is_pool ? " • Pool" : ""
        }`,
      })) ?? [],
    [vehicles]
  );

  // Check if Saturday is already in entries
  const hasSaturday = useMemo(() => {
    const saturdayDate = getSaturday(weekStart);
    return entries.some(entry => entry.date === saturdayDate);
  }, [entries, weekStart]);

  // Check if Sunday is already in entries
  const hasSunday = useMemo(() => {
    const sundayDate = getSunday(weekStart);
    return entries.some(entry => entry.date === sundayDate);
  }, [entries, weekStart]);

  // Update entries when week start changes
  const handleWeekStartChange = (newWeekStart: string) => {
    setWeekStart(newWeekStart);
    // Regenerate week entries for the new week (only Mo-Fr)
    const newEntries = generateWeekEntries(newWeekStart, weekVehicleId || null);
    // Behalte Samstag/Sonntag falls vorhanden (mit neuem Datum)
    const saturdayDate = getSaturday(newWeekStart);
    const sundayDate = getSunday(newWeekStart);
    const existingSaturday = entries.find(e => {
      const oldSaturday = getSaturday(weekStart);
      return e.date === oldSaturday;
    });
    const existingSunday = entries.find(e => {
      const oldSunday = getSunday(weekStart);
      return e.date === oldSunday;
    });
    
    if (existingSaturday) {
      newEntries.push({
        ...existingSaturday,
        date: saturdayDate,
      });
    }
    if (existingSunday) {
      newEntries.push({
        ...existingSunday,
        date: sundayDate,
      });
    }
    
    setEntries(newEntries);
  };

  const handleEntryChange = (
    date: string,
    field: keyof TimeEntry,
    value: string | number | boolean | null
  ) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.date === date
          ? {
              ...entry,
              [field]: value,
            }
          : entry
      )
    );
  };

  // Helper: Berechne Arbeitszeit für einen Eintrag
  const calculateWorkHours = (entry: TimeEntry): number => {
    if (!entry.start_time || !entry.end_time) return 0;
    try {
      const start = new Date(`1970-01-01T${entry.start_time}:00`);
      const end = new Date(`1970-01-01T${entry.end_time}:00`);
      const diff = (end.getTime() - start.getTime()) / 1000 / 60 - (entry.break_minutes || 0);
      return Math.max(diff, 0) / 60;
    } catch {
      return 0;
    }
  };

  // Helper: Kopiere Zeiten vom vorherigen Tag
  const copyFromPreviousDay = (currentDate: string) => {
    const sortedEntries = [...entries].sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return dateA - dateB;
    });
    const currentIndex = sortedEntries.findIndex(e => e.date === currentDate);
    if (currentIndex === 0) return; // Erster Tag hat keinen Vorgänger
    const previousEntry = sortedEntries[currentIndex - 1];
    
    setEntries((prev) =>
      prev.map((entry) =>
        entry.date === currentDate
          ? {
              ...entry,
              start_time: previousEntry.start_time || "",
              end_time: previousEntry.end_time || "",
              break_minutes: previousEntry.break_minutes || 0,
            }
          : entry
      )
    );
  };

  // Helper: Setze gleiche Zeiten für alle Tage
  const applyToAllDays = (sourceDate: string) => {
    const sourceEntry = entries.find(e => e.date === sourceDate);
    if (!sourceEntry || !sourceEntry.start_time || !sourceEntry.end_time) return;
    
    setEntries((prev) =>
      prev.map((entry) => ({
        ...entry,
        start_time: sourceEntry.start_time,
        end_time: sourceEntry.end_time,
        break_minutes: sourceEntry.break_minutes || 0,
      }))
    );
  };

  // Quick-Time Presets
  const quickTimePresets = [
    { label: "8:00 - 17:00 (30min Pause)", start: "08:00", end: "17:00", break: 30 },
    { label: "9:00 - 18:00 (30min Pause)", start: "09:00", end: "18:00", break: 30 },
    { label: "8:00 - 16:00 (30min Pause)", start: "08:00", end: "16:00", break: 30 },
    { label: "7:00 - 16:00 (30min Pause)", start: "07:00", end: "16:00", break: 30 },
  ];

  const applyQuickTime = (date: string, preset: typeof quickTimePresets[0]) => {
    setEntries((prev) =>
      prev.map((entry) =>
        entry.date === date
          ? {
              ...entry,
              start_time: preset.start,
              end_time: preset.end,
              break_minutes: preset.break,
            }
          : entry
      )
    );
  };

  // Add Saturday entry
  const addSaturday = () => {
    const saturdayDate = getSaturday(weekStart);
    const newEntry: TimeEntry = {
      ...defaultEntry,
      date: saturdayDate,
      vehicle_id: weekVehicleId || null,
    };
    setEntries((prev) => [...prev, newEntry]);
  };

  // Add Sunday entry
  const addSunday = () => {
    const sundayDate = getSunday(weekStart);
    const newEntry: TimeEntry = {
      ...defaultEntry,
      date: sundayDate,
      vehicle_id: weekVehicleId || null,
    };
    setEntries((prev) => [...prev, newEntry]);
  };

  // Remove entry by date
  const removeEntry = (date: string) => {
    setEntries((prev) => prev.filter(entry => entry.date !== date));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await createMutation.mutateAsync({
        week_start: weekStart,
        week_vehicle_id: weekVehicleId || undefined,
        entries: entries.map((entry) => ({
          ...entry,
          vehicle_id: entry.vehicle_id || null,
        })),
      });
      await refetch();
      navigate("/app/timesheets");
    } catch (err) {
      const error =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ??
        (err as { message?: string }).message ??
        "Stundenzettel konnte nicht angelegt werden.";
      setError(error);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Button variant="outline" onClick={() => navigate(-1)}>
        Zurück
      </Button>

      <Card className="mt-6">
        <CardContent className="space-y-6 py-6">
          <CardTitle className="text-xl text-brand-gray">
            Stundenzettel anlegen
          </CardTitle>

          {vehiclesError && (
            <Alert variant="destructive">
              Fahrzeuge konnten nicht geladen werden:{" "}
              {(vehiclesError.response?.data as { detail?: string } | undefined)
                ?.detail ?? vehiclesError.message}
            </Alert>
          )}

          {error && <Alert variant="destructive">{error}</Alert>}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="week-start">Wochenbeginn (Montag)</Label>
              <Input
                id="week-start"
                type="date"
                value={weekStart}
                onChange={(event) => {
                  const selectedDate = new Date(event.target.value);
                  const monday = getMonday(selectedDate);
                  const mondayStr = monday.toISOString().split("T")[0];
                  handleWeekStartChange(mondayStr);
                }}
              />
              <p className="text-xs text-gray-500">
                Die Woche wird automatisch auf den Montag der ausgewählten Woche gesetzt. Alle 7 Tage (Mo-So) werden automatisch erstellt.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Fahrzeug für die Woche</Label>
              <select
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                value={weekVehicleId}
                onChange={(event) => {
                  const newVehicleId = event.target.value;
                  setWeekVehicleId(newVehicleId);
                  // Update all entries that don't have a specific vehicle assigned
                  setEntries((prev) =>
                    prev.map((entry) => ({
                      ...entry,
                      vehicle_id: entry.vehicle_id || newVehicleId || null,
                    }))
                  );
                }}
                disabled={vehiclesLoading}
              >
                <option value="">— Kein Fahrzeug / später wählen —</option>
                {vehicleOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500">
                Wählen Sie das standardmäßig genutzte Fahrzeug für diese Woche.
                Die Auswahl kann für einzelne Tage überschrieben werden.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-brand-gray">
                  Wocheneinträge (Montag - Freitag)
                </h2>
              </div>
              <p className="text-sm text-gray-600">
                Die Arbeitstage Montag bis Freitag sind automatisch erstellt. Samstag und Sonntag können bei Bedarf manuell hinzugefügt werden.
              </p>

              {/* Buttons zum Hinzufügen von Samstag/Sonntag */}
              <div className="flex gap-2">
                {!hasSaturday && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addSaturday}
                  >
                    + Samstag hinzufügen
                  </Button>
                )}
                {!hasSunday && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={addSunday}
                  >
                    + Sonntag hinzufügen
                  </Button>
                )}
              </div>

              {entries
                .sort((a, b) => {
                  // Sortiere nach Datum: Mo-Fr zuerst, dann Sa-So
                  const dateA = new Date(a.date).getTime();
                  const dateB = new Date(b.date).getTime();
                  return dateA - dateB;
                })
                .map((entry, index) => {
                const workHours = calculateWorkHours(entry);
                const entryDate = new Date(entry.date);
                const dayOfWeek = entryDate.getDay();
                const dayNames = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
                const dayName = dayNames[dayOfWeek];
                const isWeekend = dayOfWeek === 0 || dayOfWeek === 6; // Sonntag oder Samstag
                const sortedEntries = [...entries].sort((a, b) => {
                  const dateA = new Date(a.date).getTime();
                  const dateB = new Date(b.date).getTime();
                  return dateA - dateB;
                });
                const currentIndex = sortedEntries.findIndex(e => e.date === entry.date);
                const previousEntry = currentIndex > 0 ? sortedEntries[currentIndex - 1] : null;
                
                return (
                  <div
                    key={entry.date}
                    className="rounded-lg border border-gray-200 p-4 shadow-sm"
                  >
                    <div className="mb-4 flex items-center justify-between border-b pb-2">
                    <h3 className="font-semibold text-brand-gray">
                      {dayName}
                      {isWeekend && <span className="ml-2 text-xs text-gray-500">(Wochenende)</span>}
                    </h3>
                    <div className="flex gap-2">
                      {previousEntry && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => copyFromPreviousDay(entry.date)}
                          title="Zeiten vom vorherigen Tag kopieren"
                        >
                          ← Vom Vortag
                        </Button>
                      )}
                      {entry.start_time && entry.end_time && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => applyToAllDays(entry.date)}
                          title="Diese Zeiten für alle Tage übernehmen"
                        >
                          Für alle Tage
                        </Button>
                      )}
                      {isWeekend && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => removeEntry(entry.date)}
                          title="Wochenendtag entfernen"
                          className="text-red-600 hover:text-red-700"
                        >
                          Entfernen
                        </Button>
                      )}
                    </div>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2 md:col-span-2">
                        <Label>Fahrzeug</Label>
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                          value={entry.vehicle_id ?? ""}
                          onChange={(event) =>
                            handleEntryChange(
                              entry.date,
                              "vehicle_id",
                              event.target.value
                            )
                          }
                          disabled={vehiclesLoading}
                        >
                          <option value="">
                            {weekVehicleId
                              ? "Wochenfahrzeug verwenden"
                              : "Kein Fahrzeug"}
                          </option>
                          {vehicleOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <Label>Datum</Label>
                        <Input
                          type="date"
                          value={entry.date}
                          onChange={(event) =>
                            handleEntryChange(entry.date, "date", event.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Ort</Label>
                        <Input
                          value={entry.location}
                          onChange={(event) =>
                            handleEntryChange(entry.date, "location", event.target.value)
                          }
                          placeholder="z.B. Büro, Kunde vor Ort"
                        />
                      </div>
                      <div className="space-y-2 md:col-span-2">
                      <Label>Zeiten</Label>
                      <div className="flex flex-wrap gap-2 mb-2">
                        {quickTimePresets.map((preset) => (
                          <Button
                            key={preset.label}
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => applyQuickTime(entry.date, preset)}
                            className="text-xs"
                          >
                            {preset.label}
                          </Button>
                        ))}
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="space-y-2">
                          <Label className="text-xs">Startzeit</Label>
                          <Input
                            type="time"
                            value={entry.start_time}
                            onChange={(event) =>
                              handleEntryChange(
                                entry.date,
                                "start_time",
                                event.target.value
                              )
                            }
                            placeholder="08:00"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs">Endzeit</Label>
                          <Input
                            type="time"
                            value={entry.end_time}
                            onChange={(event) =>
                              handleEntryChange(entry.date, "end_time", event.target.value)
                            }
                            placeholder="17:00"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-xs">Pause (Min)</Label>
                          <Input
                            type="number"
                            min={0}
                            value={entry.break_minutes || ""}
                            onChange={(event) =>
                              handleEntryChange(
                                entry.date,
                                "break_minutes",
                                parseInt(event.target.value) || 0
                              )
                            }
                            placeholder="30"
                          />
                        </div>
                      </div>
                      {workHours > 0 && (
                        <p className="text-sm text-green-600 font-semibold mt-1">
                          Arbeitszeit: {workHours.toFixed(2)} Stunden
                        </p>
                      )}
                      </div>
                      <div className="space-y-2">
                        <Label>Projekt / Kunde</Label>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                          value={entry.customer_project || ""}
                          onChange={(event) =>
                            handleEntryChange(
                              entry.date,
                              "customer_project",
                              event.target.value
                            )
                          }
                        >
                          <option value="">-- Kunde auswählen --</option>
                          {customers?.map((customer) => (
                            <option key={customer.id} value={customer.name}>
                              {customer.name}
                              {customer.project_name ? ` - ${customer.project_name}` : ""}
                            </option>
                          ))}
                        </select>
                        {customersLoading && (
                          <p className="text-xs text-gray-500">Lade Kunden...</p>
                        )}
                      </div>
                      <div className="md:col-span-2 space-y-2">
                        <Label>Aufgaben</Label>
                        <Input
                          value={entry.tasks}
                          onChange={(event) =>
                            handleEntryChange(entry.date, "tasks", event.target.value)
                          }
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="submit"
                disabled={createMutation.isPending || entries.length === 0}
              >
                {createMutation.isPending
                  ? "Speichere..."
                  : "Stundenzettel speichern"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

