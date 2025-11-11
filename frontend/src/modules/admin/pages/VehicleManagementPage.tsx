import { useMemo, useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import {
  useAdminUsersQuery,
} from "../hooks/useAdminUsers";
import {
  useCreateVehicleMutation,
  useDeleteVehicleMutation,
  useUpdateVehicleMutation,
  useVehiclesQuery,
} from "../hooks/useVehicles";
import type { Vehicle } from "../../../services/api/types";

interface VehicleFormState {
  name: string;
  licensePlate: string;
  isPool: boolean;
  assignedUserId: string;
}

const emptyFormState: VehicleFormState = {
  name: "",
  licensePlate: "",
  isPool: false,
  assignedUserId: "",
};

export const VehicleManagementPage = () => {
  const { data: vehicles, isLoading, error } = useVehiclesQuery();
  const { data: users } = useAdminUsersQuery();
  const createMutation = useCreateVehicleMutation();
  const deleteMutation = useDeleteVehicleMutation();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [createState, setCreateState] = useState<VehicleFormState>(
    emptyFormState
  );
  const [editState, setEditState] = useState<VehicleFormState>(emptyFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const updateMutation = useUpdateVehicleMutation(editingId ?? "");

  const assignedUserOptions = useMemo(
    () =>
      users
        ?.sort((a, b) => a.name.localeCompare(b.name, "de-DE"))
        .map((user) => ({
          label: `${user.name} (${user.email})`,
          value: user.id,
        })) ?? [],
    [users]
  );

  const resetMessages = () => {
    setMessage(null);
    setFormError(null);
  };

  const handleCreateSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetMessages();
    createMutation.mutate(
      {
        name: createState.name,
        license_plate: createState.licensePlate,
        is_pool: createState.isPool,
        assigned_user_id: createState.isPool
          ? undefined
          : createState.assignedUserId || undefined,
      },
      {
        onSuccess: () => {
          setMessage("Fahrzeug wurde angelegt.");
          setCreateState(emptyFormState);
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setFormError(
            detail ?? "Fahrzeug konnte nicht angelegt werden. Bitte erneut versuchen."
          );
        },
      }
    );
  };

  const startEdit = (vehicle: Vehicle) => {
    resetMessages();
    setEditingId(vehicle.id);
    setEditState({
      name: vehicle.name,
      licensePlate: vehicle.license_plate,
      isPool: vehicle.is_pool,
      assignedUserId: vehicle.assigned_user_id ?? "",
    });
  };

  const handleEditChange = <K extends keyof VehicleFormState>(
    key: K,
    value: VehicleFormState[K]
  ) => {
    setEditState((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleUpdate = (event: React.FormEvent) => {
    event.preventDefault();
    if (!editingId) return;
    resetMessages();
    updateMutation.mutate(
      {
        name: editState.name,
        license_plate: editState.licensePlate,
        is_pool: editState.isPool,
        assigned_user_id: editState.isPool
          ? null
          : editState.assignedUserId || null,
      },
      {
        onSuccess: () => {
          setMessage("Fahrzeug wurde aktualisiert.");
          setEditingId(null);
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setFormError(detail ?? "Fahrzeug konnte nicht aktualisiert werden.");
        },
      }
    );
  };

  const handleDelete = (vehicle: Vehicle) => {
    resetMessages();
    if (
      !window.confirm(
        `Fahrzeug "${vehicle.name}" wirklich löschen? Dieser Vorgang kann nicht rückgängig gemacht werden.`
      )
    ) {
      return;
    }
    deleteMutation.mutate(vehicle.id, {
      onSuccess: () => {
        setMessage("Fahrzeug wurde gelöscht.");
        if (editingId === vehicle.id) {
          setEditingId(null);
        }
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setFormError(detail ?? "Fahrzeug konnte nicht gelöscht werden.");
      },
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setFormError(null);
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Fahrzeugverwaltung
          </h1>
          <p className="text-sm text-gray-600">
            Legen Sie Firmenfahrzeuge an und weisen Sie diese optional einzelnen
            Mitarbeitenden zu. Poolfahrzeuge stehen mehreren Personen zur
            Verfügung.
          </p>
        </div>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {formError && <Alert variant="destructive">{formError}</Alert>}
      {error && (
        <Alert variant="destructive">
          Fahrzeuge konnten nicht geladen werden:{" "}
          {(error.response?.data as { detail?: string } | undefined)?.detail ??
            error.message}
        </Alert>
      )}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Neues Fahrzeug anlegen
          </CardTitle>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={handleCreateSubmit}
          >
            <div className="space-y-2">
              <label className="text-sm text-gray-600">Bezeichnung</label>
              <Input
                value={createState.name}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    name: event.target.value,
                  }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-gray-600">Kennzeichen</label>
              <Input
                value={createState.licensePlate}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    licensePlate: event.target.value,
                  }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={createState.isPool}
                  onChange={(event) =>
                    setCreateState((prev) => ({
                      ...prev,
                      isPool: event.target.checked,
                      assignedUserId: event.target.checked
                        ? ""
                        : prev.assignedUserId,
                    }))
                  }
                />
                Poolfahrzeug (keiner Person fest zugeordnet)
              </label>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-gray-600">
                Zugeordnete Person (optional)
              </label>
              <select
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                value={createState.assignedUserId}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    assignedUserId: event.target.value,
                  }))
                }
                disabled={createState.isPool}
              >
                <option value="">— Keine Zuordnung / Pool —</option>
                {assignedUserOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? "Speichere…" : "Fahrzeug speichern"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Bestehende Fahrzeuge
          </CardTitle>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Bezeichnung</th>
                  <th className="px-4 py-3">Kennzeichen</th>
                  <th className="px-4 py-3">Zuordnung</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Aktionen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {isLoading ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Lade Fahrzeuge…
                    </td>
                  </tr>
                ) : vehicles && vehicles.length > 0 ? (
                  vehicles.map((vehicle) => {
                    const isEditing = editingId === vehicle.id;
                    return (
                      <tr key={vehicle.id}>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <Input
                              value={editState.name}
                              onChange={(event) =>
                                handleEditChange("name", event.target.value)
                              }
                            />
                          ) : (
                            vehicle.name
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <Input
                              value={editState.licensePlate}
                              onChange={(event) =>
                                handleEditChange(
                                  "licensePlate",
                                  event.target.value
                                )
                              }
                            />
                          ) : (
                            vehicle.license_plate
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <select
                              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                              value={editState.assignedUserId}
                              onChange={(event) =>
                                handleEditChange(
                                  "assignedUserId",
                                  event.target.value
                                )
                              }
                              disabled={editState.isPool}
                            >
                              <option value="">
                                — Keine Zuordnung / Pool —
                              </option>
                              {assignedUserOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          ) : vehicle.is_pool ? (
                            "Poolfahrzeug"
                          ) : vehicle.assigned_user_name ? (
                            vehicle.assigned_user_name
                          ) : (
                            "—"
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <label className="flex items-center gap-2 text-xs text-gray-600">
                              <input
                                type="checkbox"
                                checked={editState.isPool}
                                onChange={(event) =>
                                  handleEditChange("isPool", event.target.checked)
                                }
                              />
                              Poolfahrzeug
                            </label>
                          ) : vehicle.is_pool ? (
                            <span className="text-xs uppercase tracking-wide text-gray-500">
                              Pool
                            </span>
                          ) : (
                            <span className="text-xs uppercase tracking-wide text-brand-gray">
                              Personalisiert
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            {isEditing ? (
                              <>
                                <Button
                                  size="sm"
                                  onClick={handleUpdate}
                                  disabled={updateMutation.isPending}
                                >
                                  {updateMutation.isPending
                                    ? "Speichere…"
                                    : "Speichern"}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={cancelEdit}
                                >
                                  Abbrechen
                                </Button>
                              </>
                            ) : (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => startEdit(vehicle)}
                                >
                                  Bearbeiten
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDelete(vehicle)}
                                  disabled={deleteMutation.isPending}
                                >
                                  Löschen
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Noch keine Fahrzeuge hinterlegt.
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

