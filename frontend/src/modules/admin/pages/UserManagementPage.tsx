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
import {
  useAdminUsersQuery,
  useCreateUserMutation,
  useDeleteUserMutation,
  useUpdateUserMutation,
} from "../hooks/useAdminUsers";
import type { AdminUserSummary, Role } from "../../../services/api/types";

interface UserFormState {
  email: string;
  name: string;
  password: string;
  role: Role;
  weekly_hours: number;
}

const emptyFormState: UserFormState = {
  email: "",
  name: "",
  password: "",
  role: "user",
  weekly_hours: 40.0,
};

const roleLabels: Record<Role, string> = {
  user: "Benutzer",
  admin: "Administrator",
  accounting: "Buchhaltung",
};

export const UserManagementPage = () => {
  const { data: users, isLoading, error } = useAdminUsersQuery();
  const createMutation = useCreateUserMutation();
  const deleteMutation = useDeleteUserMutation();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [createState, setCreateState] = useState<UserFormState>(emptyFormState);
  const [editState, setEditState] = useState<UserFormState>(emptyFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const updateMutation = useUpdateUserMutation(editingId ?? "");

  const resetMessages = () => {
    setMessage(null);
    setFormError(null);
  };

  const handleCreateSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    resetMessages();

    if (!createState.email || !createState.name || !createState.password) {
      setFormError("Bitte füllen Sie alle Pflichtfelder aus.");
      return;
    }

    createMutation.mutate(
      {
        email: createState.email,
        name: createState.name,
        password: createState.password,
        role: createState.role,
        weekly_hours: createState.weekly_hours,
      },
      {
        onSuccess: () => {
          setMessage("Benutzer wurde erfolgreich angelegt.");
          setCreateState(emptyFormState);
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setFormError(
            detail ?? "Benutzer konnte nicht angelegt werden. Bitte erneut versuchen."
          );
        },
      }
    );
  };

  const startEdit = (user: AdminUserSummary) => {
    resetMessages();
    setEditingId(user.id);
    setEditState({
      email: user.email,
      name: user.name,
      password: "", // Passwort wird nicht angezeigt
      role: user.role,
      weekly_hours: user.weekly_hours ?? 40.0,
    });
  };

  const handleEditChange = <K extends keyof UserFormState>(
    key: K,
    value: UserFormState[K]
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

    const updatePayload: {
      email?: string;
      name?: string;
      role?: Role;
      weekly_hours?: number;
    } = {};

    if (editState.email) updatePayload.email = editState.email;
    if (editState.name) updatePayload.name = editState.name;
    if (editState.role) updatePayload.role = editState.role;
    if (editState.weekly_hours !== undefined)
      updatePayload.weekly_hours = editState.weekly_hours;

    updateMutation.mutate(updatePayload, {
      onSuccess: () => {
        setMessage("Benutzer wurde aktualisiert.");
        setEditingId(null);
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setFormError(detail ?? "Benutzer konnte nicht aktualisiert werden.");
      },
    });
  };

  const handleDelete = (user: AdminUserSummary) => {
    resetMessages();
    if (
      !window.confirm(
        `Benutzer "${user.name}" (${user.email}) wirklich löschen? Dieser Vorgang kann nicht rückgängig gemacht werden.`
      )
    ) {
      return;
    }
    deleteMutation.mutate(user.id, {
      onSuccess: () => {
        setMessage("Benutzer wurde gelöscht.");
        if (editingId === user.id) {
          setEditingId(null);
        }
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setFormError(detail ?? "Benutzer konnte nicht gelöscht werden.");
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
            Benutzerverwaltung
          </h1>
          <p className="text-sm text-gray-600">
            Verwalten Sie Benutzer, Rollen und Wochenstunden.
          </p>
        </div>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {formError && <Alert variant="destructive">{formError}</Alert>}
      {error && (
        <Alert variant="destructive">
          Benutzer konnten nicht geladen werden:{" "}
          {(error.response?.data as { detail?: string } | undefined)?.detail ??
            error.message}
        </Alert>
      )}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Neuen Benutzer anlegen
          </CardTitle>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={handleCreateSubmit}
          >
            <div className="space-y-2">
              <Label htmlFor="create-email">E-Mail *</Label>
              <Input
                id="create-email"
                type="email"
                value={createState.email}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    email: event.target.value,
                  }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-name">Name *</Label>
              <Input
                id="create-name"
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
              <Label htmlFor="create-password">Passwort *</Label>
              <Input
                id="create-password"
                type="password"
                value={createState.password}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    password: event.target.value,
                  }))
                }
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-role">Rolle</Label>
              <select
                id="create-role"
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                value={createState.role}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    role: event.target.value as Role,
                  }))
                }
              >
                <option value="user">Benutzer</option>
                <option value="admin">Administrator</option>
                <option value="accounting">Buchhaltung</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="create-weekly-hours">Wochenstunden</Label>
              <Input
                id="create-weekly-hours"
                type="number"
                min="0"
                max="168"
                step="0.5"
                value={createState.weekly_hours}
                onChange={(event) =>
                  setCreateState((prev) => ({
                    ...prev,
                    weekly_hours: Number(event.target.value),
                  }))
                }
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending
                  ? "Speichere…"
                  : "Benutzer anlegen"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Bestehende Benutzer
          </CardTitle>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">E-Mail</th>
                  <th className="px-4 py-3">Rolle</th>
                  <th className="px-4 py-3">Wochenstunden</th>
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
                      Lade Benutzer…
                    </td>
                  </tr>
                ) : users && users.length > 0 ? (
                  users.map((user) => {
                    const isEditing = editingId === user.id;
                    return (
                      <tr key={user.id}>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <Input
                              value={editState.name}
                              onChange={(event) =>
                                handleEditChange("name", event.target.value)
                              }
                            />
                          ) : (
                            user.name
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <Input
                              type="email"
                              value={editState.email}
                              onChange={(event) =>
                                handleEditChange("email", event.target.value)
                              }
                            />
                          ) : (
                            user.email
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <select
                              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                              value={editState.role}
                              onChange={(event) =>
                                handleEditChange("role", event.target.value as Role)
                              }
                            >
                              <option value="user">Benutzer</option>
                              <option value="admin">Administrator</option>
                              <option value="accounting">Buchhaltung</option>
                            </select>
                          ) : (
                            roleLabels[user.role] ?? user.role
                          )}
                        </td>
                        <td className="px-4 py-3 text-gray-700">
                          {isEditing ? (
                            <Input
                              type="number"
                              min="0"
                              max="168"
                              step="0.5"
                              value={editState.weekly_hours}
                              onChange={(event) =>
                                handleEditChange(
                                  "weekly_hours",
                                  Number(event.target.value)
                                )
                              }
                            />
                          ) : (
                            user.weekly_hours?.toFixed(1) ?? "40.0"
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
                                  onClick={() => startEdit(user)}
                                >
                                  Bearbeiten
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDelete(user)}
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
                      Noch keine Benutzer vorhanden.
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

