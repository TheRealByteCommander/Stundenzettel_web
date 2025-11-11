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
import type { TimeEntry } from "../../../services/api/types";

const defaultEntry: TimeEntry = {
  date: new Date().toISOString().split("T")[0],
  start_time: "08:00",
  end_time: "17:00",
  break_minutes: 30,
  tasks: "",
  customer_project: "",
  location: "",
  absence_type: null,
  travel_time_minutes: 0,
  include_travel_time: false,
  vehicle_id: null,
};

export const TimesheetCreatePage = () => {
  const navigate = useNavigate();
  const { refetch } = useTimesheetsQuery();
  const createMutation = useCreateTimesheetMutation();
  const { data: vehicles, isLoading: vehiclesLoading, error: vehiclesError } =
    useAvailableVehiclesQuery();
  const [weekStart, setWeekStart] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [weekVehicleId, setWeekVehicleId] = useState<string>("");
  const [entries, setEntries] = useState<TimeEntry[]>([{ ...defaultEntry }]);
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

  const handleEntryChange = (
    index: number,
    field: keyof TimeEntry,
    value: string
  ) => {
    setEntries((prev) =>
      prev.map((entry, idx) =>
        idx === index
          ? {
              ...entry,
              [field]:
                field === "break_minutes" || field === "travel_time_minutes"
                  ? Number(value)
                  : field === "vehicle_id"
                  ? value || null
                  : value,
            }
          : entry
      )
    );
  };

  const handleAddEntry = () => {
    setEntries((prev) => [
      ...prev,
      { ...defaultEntry, vehicle_id: weekVehicleId || null },
    ]);
  };

  const handleRemoveEntry = (index: number) => {
    setEntries((prev) => prev.filter((_, idx) => idx !== index));
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
                onChange={(event) => setWeekStart(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Fahrzeug für die Woche</Label>
              <select
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                value={weekVehicleId}
                onChange={(event) => {
                  const newVehicleId = event.target.value;
                  const previousVehicleId = weekVehicleId;
                  setWeekVehicleId(newVehicleId);
                  setEntries((prev) =>
                    prev.map((entry) => {
                      if (
                        entry.vehicle_id === previousVehicleId ||
                        entry.vehicle_id === null
                      ) {
                        return {
                          ...entry,
                          vehicle_id: newVehicleId || null,
                        };
                      }
                      return entry;
                    })
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
                  Einträge
                </h2>
                <Button type="button" variant="outline" onClick={handleAddEntry}>
                  Eintrag hinzufügen
                </Button>
              </div>

              {entries.map((entry, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-gray-200 p-4 shadow-sm"
                >
                  <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2 md:col-span-2">
                        <Label>Fahrzeug</Label>
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                          value={entry.vehicle_id ?? ""}
                          onChange={(event) =>
                            handleEntryChange(
                              index,
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
                          handleEntryChange(index, "date", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Ort</Label>
                      <Input
                        value={entry.location}
                        onChange={(event) =>
                          handleEntryChange(index, "location", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Startzeit</Label>
                      <Input
                        type="time"
                        value={entry.start_time}
                        onChange={(event) =>
                          handleEntryChange(
                            index,
                            "start_time",
                            event.target.value
                          )
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Endzeit</Label>
                      <Input
                        type="time"
                        value={entry.end_time}
                        onChange={(event) =>
                          handleEntryChange(index, "end_time", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Pausen (Minuten)</Label>
                      <Input
                        type="number"
                        min={0}
                        value={entry.break_minutes}
                        onChange={(event) =>
                          handleEntryChange(
                            index,
                            "break_minutes",
                            event.target.value
                          )
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Projekt / Kunde</Label>
                      <Input
                        value={entry.customer_project}
                        onChange={(event) =>
                          handleEntryChange(
                            index,
                            "customer_project",
                            event.target.value
                          )
                        }
                      />
                    </div>
                    <div className="md:col-span-2 space-y-2">
                      <Label>Aufgaben</Label>
                      <Input
                        value={entry.tasks}
                        onChange={(event) =>
                          handleEntryChange(index, "tasks", event.target.value)
                        }
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => handleRemoveEntry(index)}
                      disabled={entries.length === 1}
                    >
                      Eintrag entfernen
                    </Button>
                  </div>
                </div>
              ))}
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

