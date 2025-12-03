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
  useCustomersQuery,
  useCreateCustomerMutation,
  useDeleteCustomerMutation,
  useUpdateCustomerMutation,
} from "../hooks/useCustomers";
import type { Customer } from "../../../services/api/customers";

interface CustomerFormState {
  name: string;
  project_name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
  active: boolean;
}

const emptyFormState: CustomerFormState = {
  name: "",
  project_name: "",
  contact_person: "",
  email: "",
  phone: "",
  address: "",
  notes: "",
  active: true,
};

export const CustomerManagementPage = () => {
  const { data: customers, isLoading, error } = useCustomersQuery();
  const createMutation = useCreateCustomerMutation();
  const deleteMutation = useDeleteCustomerMutation();
  const updateMutation = useUpdateCustomerMutation();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [createState, setCreateState] = useState<CustomerFormState>(emptyFormState);
  const [editState, setEditState] = useState<CustomerFormState>(emptyFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setMessage(null);

    if (!createState.name.trim()) {
      setFormError("Kundenname ist erforderlich");
      return;
    }

    try {
      await createMutation.mutateAsync({
        name: createState.name.trim(),
        project_name: createState.project_name.trim() || undefined,
        contact_person: createState.contact_person.trim() || undefined,
        email: createState.email.trim() || undefined,
        phone: createState.phone.trim() || undefined,
        address: createState.address.trim() || undefined,
        notes: createState.notes.trim() || undefined,
        active: createState.active,
      });
      setCreateState(emptyFormState);
      setMessage("Kunde erfolgreich erstellt");
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Fehler beim Erstellen des Kunden");
    }
  };

  const handleEdit = (customer: Customer) => {
    setEditingId(customer.id);
    setEditState({
      name: customer.name,
      project_name: customer.project_name || "",
      contact_person: customer.contact_person || "",
      email: customer.email || "",
      phone: customer.phone || "",
      address: customer.address || "",
      notes: customer.notes || "",
      active: customer.active,
    });
    setMessage(null);
    setFormError(null);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;

    setFormError(null);
    setMessage(null);

    if (!editState.name.trim()) {
      setFormError("Kundenname ist erforderlich");
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id: editingId,
        data: {
          name: editState.name.trim(),
          project_name: editState.project_name.trim() || undefined,
          contact_person: editState.contact_person.trim() || undefined,
          email: editState.email.trim() || undefined,
          phone: editState.phone.trim() || undefined,
          address: editState.address.trim() || undefined,
          notes: editState.notes.trim() || undefined,
          active: editState.active,
        },
      });
      setEditingId(null);
      setEditState(emptyFormState);
      setMessage("Kunde erfolgreich aktualisiert");
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Fehler beim Aktualisieren des Kunden");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Möchten Sie diesen Kunden wirklich löschen?")) return;

    try {
      await deleteMutation.mutateAsync(id);
      setMessage("Kunde erfolgreich gelöscht");
    } catch (err: any) {
      setFormError(err.response?.data?.detail || "Fehler beim Löschen des Kunden");
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditState(emptyFormState);
    setFormError(null);
    setMessage(null);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-6">
            <p>Lade Kunden...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          Fehler beim Laden der Kunden: {String(error)}
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-3 sm:p-6 space-y-4 sm:space-y-6">
      <Card>
        <CardContent className="p-4 sm:p-6">
          <CardTitle className="mb-4 text-base sm:text-lg">Kundenverwaltung</CardTitle>

          {message && (
            <Alert className="mb-4 bg-green-50 text-green-800 border-green-200">
              {message}
            </Alert>
          )}

          {formError && (
            <Alert variant="destructive" className="mb-4">
              {formError}
            </Alert>
          )}

          {/* Erstellen */}
          <form onSubmit={handleCreateSubmit} className="space-y-3 sm:space-y-4 mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold">Neuen Kunden erstellen</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
              <div className="space-y-2">
                <Label htmlFor="create-name">Kundenname *</Label>
                <Input
                  id="create-name"
                  value={createState.name}
                  onChange={(e) =>
                    setCreateState({ ...createState, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-project">Projektname</Label>
                <Input
                  id="create-project"
                  value={createState.project_name}
                  onChange={(e) =>
                    setCreateState({ ...createState, project_name: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-contact">Ansprechpartner</Label>
                <Input
                  id="create-contact"
                  value={createState.contact_person}
                  onChange={(e) =>
                    setCreateState({ ...createState, contact_person: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-email">E-Mail</Label>
                <Input
                  id="create-email"
                  type="email"
                  value={createState.email}
                  onChange={(e) =>
                    setCreateState({ ...createState, email: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-phone">Telefon</Label>
                <Input
                  id="create-phone"
                  value={createState.phone}
                  onChange={(e) =>
                    setCreateState({ ...createState, phone: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="create-active">Status</Label>
                <select
                  id="create-active"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                  value={createState.active ? "true" : "false"}
                  onChange={(e) =>
                    setCreateState({ ...createState, active: e.target.value === "true" })
                  }
                >
                  <option value="true">Aktiv</option>
                  <option value="false">Inaktiv</option>
                </select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="create-address">Adresse</Label>
                <Input
                  id="create-address"
                  value={createState.address}
                  onChange={(e) =>
                    setCreateState({ ...createState, address: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="create-notes">Notizen</Label>
                <textarea
                  id="create-notes"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                  value={createState.notes}
                  onChange={(e) =>
                    setCreateState({ ...createState, notes: e.target.value })
                  }
                />
              </div>
            </div>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Erstelle..." : "Kunde erstellen"}
            </Button>
          </form>

          {/* Liste */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Vorhandene Kunden</h3>
            {customers && customers.length === 0 ? (
              <p className="text-gray-500">Keine Kunden vorhanden</p>
            ) : (
              <div className="space-y-4">
                {customers?.map((customer) => (
                  <div
                    key={customer.id}
                    className="border rounded-lg p-4 space-y-2"
                  >
                    {editingId === customer.id ? (
                      <form onSubmit={handleEditSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor={`edit-name-${customer.id}`}>Kundenname *</Label>
                            <Input
                              id={`edit-name-${customer.id}`}
                              value={editState.name}
                              onChange={(e) =>
                                setEditState({ ...editState, name: e.target.value })
                              }
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`edit-project-${customer.id}`}>Projektname</Label>
                            <Input
                              id={`edit-project-${customer.id}`}
                              value={editState.project_name}
                              onChange={(e) =>
                                setEditState({ ...editState, project_name: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`edit-contact-${customer.id}`}>Ansprechpartner</Label>
                            <Input
                              id={`edit-contact-${customer.id}`}
                              value={editState.contact_person}
                              onChange={(e) =>
                                setEditState({ ...editState, contact_person: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`edit-email-${customer.id}`}>E-Mail</Label>
                            <Input
                              id={`edit-email-${customer.id}`}
                              type="email"
                              value={editState.email}
                              onChange={(e) =>
                                setEditState({ ...editState, email: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`edit-phone-${customer.id}`}>Telefon</Label>
                            <Input
                              id={`edit-phone-${customer.id}`}
                              value={editState.phone}
                              onChange={(e) =>
                                setEditState({ ...editState, phone: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor={`edit-active-${customer.id}`}>Status</Label>
                            <select
                              id={`edit-active-${customer.id}`}
                              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                              value={editState.active ? "true" : "false"}
                              onChange={(e) =>
                                setEditState({ ...editState, active: e.target.value === "true" })
                              }
                            >
                              <option value="true">Aktiv</option>
                              <option value="false">Inaktiv</option>
                            </select>
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label htmlFor={`edit-address-${customer.id}`}>Adresse</Label>
                            <Input
                              id={`edit-address-${customer.id}`}
                              value={editState.address}
                              onChange={(e) =>
                                setEditState({ ...editState, address: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label htmlFor={`edit-notes-${customer.id}`}>Notizen</Label>
                            <textarea
                              id={`edit-notes-${customer.id}`}
                              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                              value={editState.notes}
                              onChange={(e) =>
                                setEditState({ ...editState, notes: e.target.value })
                              }
                            />
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button type="submit" disabled={updateMutation.isPending}>
                            {updateMutation.isPending ? "Speichere..." : "Speichern"}
                          </Button>
                          <Button type="button" variant="outline" onClick={cancelEdit}>
                            Abbrechen
                          </Button>
                        </div>
                      </form>
                    ) : (
                      <>
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-lg">
                              {customer.name}
                              {customer.project_name && (
                                <span className="text-gray-600 ml-2">
                                  ({customer.project_name})
                                </span>
                              )}
                            </h4>
                            {customer.contact_person && (
                              <p className="text-sm text-gray-600">
                                Ansprechpartner: {customer.contact_person}
                              </p>
                            )}
                            {customer.email && (
                              <p className="text-sm text-gray-600">E-Mail: {customer.email}</p>
                            )}
                            {customer.phone && (
                              <p className="text-sm text-gray-600">Telefon: {customer.phone}</p>
                            )}
                            {customer.address && (
                              <p className="text-sm text-gray-600">Adresse: {customer.address}</p>
                            )}
                            {customer.notes && (
                              <p className="text-sm text-gray-500 mt-2">{customer.notes}</p>
                            )}
                            <p className="text-sm mt-2">
                              Status:{" "}
                              <span
                                className={
                                  customer.active
                                    ? "text-green-600 font-semibold"
                                    : "text-red-600 font-semibold"
                                }
                              >
                                {customer.active ? "Aktiv" : "Inaktiv"}
                              </span>
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEdit(customer)}
                            >
                              Bearbeiten
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(customer.id)}
                              disabled={deleteMutation.isPending}
                            >
                              Löschen
                            </Button>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

