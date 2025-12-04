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
  useTravelExpensesQuery,
  useCreateTravelExpenseMutation,
  useDeleteTravelExpenseMutation,
  useUpdateTravelExpenseMutation,
  useUploadTravelExpenseReceiptMutation,
  useDeleteTravelExpenseReceiptMutation,
} from "../hooks/useTravelExpenses";
import { useCustomersQuery } from "../../timesheets/hooks/useCustomers";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import type { TravelExpense, TravelExpenseCreate, TravelExpenseReceipt } from "../../../services/api/types";

interface ExpenseFormState {
  date: string;
  description: string;
  customer_project: string;
}

const emptyFormState: ExpenseFormState = {
  date: new Date().toISOString().split("T")[0],
  description: "",
  customer_project: "",
};

export const TravelExpensesPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAdmin = user?.role === "admin" || user?.role === "accounting";
  const { data: expenses, isLoading } = useTravelExpensesQuery();
  const { data: customers } = useCustomersQuery();
  const createMutation = useCreateTravelExpenseMutation();
  const deleteMutation = useDeleteTravelExpenseMutation();

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formState, setFormState] = useState<ExpenseFormState>(emptyFormState);
  const [editState, setEditState] = useState<ExpenseFormState>(emptyFormState);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [receiptMessage, setReceiptMessage] = useState<string | null>(null);
  const [receiptError, setReceiptError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);
    setError(null);

    if (!formState.date || !formState.description) {
      setError("Datum und Beschreibung sind erforderlich");
      return;
    }

    try {
      const payload: TravelExpenseCreate = {
        date: formState.date,
        description: formState.description,
        kilometers: 0, // Nicht mehr vom User eingegeben
        expenses: 0, // Nicht mehr vom User eingegeben
        customer_project: formState.customer_project || "",
      };
      const createdExpense = await createMutation.mutateAsync(payload);
      setFormState(emptyFormState);
      setShowCreateForm(false);
      setMessage(`Reisekosten erfolgreich erstellt. ID: ${createdExpense.id}`);
      // Liste wird automatisch durch React Query aktualisiert
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Erstellen";
      setError(errorMessage);
    }
  };

  const handleEdit = (expense: TravelExpense) => {
    setEditingId(expense.id);
    setEditState({
      date: expense.date,
      description: expense.description,
      customer_project: expense.customer_project,
    });
    setMessage(null);
    setError(null);
  };

  const UpdateButton = ({ expenseId }: { expenseId: string }) => {
    const updateMutation = useUpdateTravelExpenseMutation(expenseId);
    
    const handleUpdateClick = async () => {
      setMessage(null);
      setError(null);

      if (!editState.date || !editState.description) {
        setError("Datum und Beschreibung sind erforderlich");
        return;
      }

      try {
        await updateMutation.mutateAsync({
          date: editState.date,
          description: editState.description,
          kilometers: 0, // Nicht mehr vom User eingegeben
          expenses: 0, // Nicht mehr vom User eingegeben
          customer_project: editState.customer_project || "",
        });
        setEditingId(null);
        setEditState(emptyFormState);
        setMessage("Reisekosten erfolgreich aktualisiert");
      } catch (err) {
        const errorMessage =
          (err as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Aktualisieren";
        setError(errorMessage);
      }
    };

    return (
      <Button
        size="sm"
        onClick={handleUpdateClick}
        disabled={updateMutation.isPending}
      >
        {updateMutation.isPending ? "Speichere..." : "Speichern"}
      </Button>
    );
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Möchten Sie diese Reisekosten wirklich löschen?")) {
      return;
    }

    try {
      await deleteMutation.mutateAsync(id);
      setMessage("Reisekosten erfolgreich gelöscht");
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Löschen";
      setError(errorMessage);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("de-DE");
  };

  const ReceiptUploadButton = ({ expense }: { expense: TravelExpense }) => {
    const uploadMutation = useUploadTravelExpenseReceiptMutation(expense.id);
    
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setReceiptMessage(null);
        setReceiptError(null);
        uploadMutation.mutate(file, {
          onSuccess: () => {
            setReceiptMessage("Beleg erfolgreich hochgeladen");
          },
          onError: (err) => {
            const errorMessage =
              (err as { response?: { data?: { detail?: string } } }).response?.data
                ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Hochladen";
            setReceiptError(errorMessage);
          },
        });
        e.target.value = "";
      }
    };

    return (
      <label className="block">
        <input
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileChange}
          disabled={uploadMutation.isPending}
        />
        <Button
          size="sm"
          variant="outline"
          className="w-full text-xs"
          asChild
          disabled={uploadMutation.isPending}
        >
          <span>{uploadMutation.isPending ? "Upload..." : "Beleg hochladen"}</span>
        </Button>
      </label>
    );
  };

  const ReceiptItem = ({ expense, receipt, onDelete }: { expense: TravelExpense; receipt: TravelExpenseReceipt; onDelete: () => void }) => {
    const deleteMutation = useDeleteTravelExpenseReceiptMutation(expense.id);
    
    const handleDelete = () => {
      if (confirm("Beleg wirklich löschen?")) {
        setReceiptMessage(null);
        setReceiptError(null);
        deleteMutation.mutate(receipt.id, {
          onSuccess: () => {
            setReceiptMessage("Beleg gelöscht");
            onDelete();
          },
          onError: (err) => {
            const errorMessage =
              (err as { response?: { data?: { detail?: string } } }).response?.data
                ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Löschen";
            setReceiptError(errorMessage);
          },
        });
      }
    };

    return (
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>{receipt.filename}</span>
        {expense.status === "draft" && (
          <Button
            size="sm"
            variant="ghost"
            className="h-6 px-2 text-xs"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            ×
          </Button>
        )}
      </div>
    );
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
            Reisekosten-Einzelausgaben
          </h1>
          <p className="text-xs sm:text-sm text-gray-600">
            Verwalten Sie einzelne Reisekosten außerhalb von Monatsberichten.
          </p>
        </div>
        {!showCreateForm && (
          <Button onClick={() => setShowCreateForm(true)} className="w-full sm:w-auto">
            Neue Ausgabe
          </Button>
        )}
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="destructive">{error}</Alert>}
      {receiptMessage && <Alert variant="success">{receiptMessage}</Alert>}
      {receiptError && <Alert variant="destructive">{receiptError}</Alert>}

      {showCreateForm && (
        <Card>
          <CardContent className="space-y-4 py-4 sm:py-6">
            <CardTitle className="text-base sm:text-lg text-brand-gray">
              Neue Reisekosten-Ausgabe
            </CardTitle>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="create-date">Datum *</Label>
                  <Input
                    id="create-date"
                    type="date"
                    value={formState.date}
                    onChange={(e) =>
                      setFormState({ ...formState, date: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-customer">Kunde/Projekt</Label>
                  <select
                    id="create-customer"
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px] sm:min-h-[40px]"
                    value={formState.customer_project}
                    onChange={(e) =>
                      setFormState({ ...formState, customer_project: e.target.value })
                    }
                  >
                    <option value="">Kein Kunde/Projekt</option>
                    {customers?.map((customer) => (
                      <option key={customer.id} value={customer.name}>
                        {customer.name}
                        {customer.project_name ? ` - ${customer.project_name}` : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="create-description">Kommentar *</Label>
                  <Input
                    id="create-description"
                    value={formState.description}
                    onChange={(e) =>
                      setFormState({ ...formState, description: e.target.value })
                    }
                    placeholder="z.B. Fahrt nach Berlin, Hotelübernachtung, etc."
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1"
                >
                  {createMutation.isPending ? "Erstelle..." : "Erstellen"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateForm(false);
                    setFormState(emptyFormState);
                    setError(null);
                  }}
                  className="flex-1"
                >
                  Abbrechen
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-3 sm:space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Alle Reisekosten-Ausgaben
          </CardTitle>

          {isLoading ? (
            <p className="text-center text-gray-500 py-6">Lade Daten…</p>
          ) : expenses && expenses.length > 0 ? (
            <>
              {/* Mobile: Card-Layout */}
              <div className="block sm:hidden space-y-3">
                {expenses.map((expense) => {
                  const isEditing = editingId === expense.id;
                  return (
                    <div
                      key={expense.id}
                      className="rounded-lg border border-gray-200 bg-white p-4"
                    >
                      {isEditing ? (
                        <div className="space-y-3">
                          <div className="space-y-2">
                            <Label className="text-sm">Datum *</Label>
                            <Input
                              type="date"
                              value={editState.date}
                              onChange={(e) =>
                                setEditState({ ...editState, date: e.target.value })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-sm">Kommentar *</Label>
                            <Input
                              value={editState.description}
                              onChange={(e) =>
                                setEditState({
                                  ...editState,
                                  description: e.target.value,
                                })
                              }
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-sm">Kunde/Projekt</Label>
                            <select
                              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 min-h-[44px]"
                              value={editState.customer_project}
                              onChange={(e) =>
                                setEditState({
                                  ...editState,
                                  customer_project: e.target.value,
                                })
                              }
                            >
                              <option value="">Kein Kunde/Projekt</option>
                              {customers?.map((customer) => (
                                <option key={customer.id} value={customer.name}>
                                  {customer.name}
                                  {customer.project_name
                                    ? ` - ${customer.project_name}`
                                    : ""}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="flex gap-2">
                            <UpdateButton expenseId={expense.id} />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setEditingId(null);
                                setEditState(emptyFormState);
                              }}
                              className="flex-1"
                            >
                              Abbrechen
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="mb-3">
                            <div className="flex items-start justify-between mb-2">
                              <div>
                                <p className="font-semibold text-brand-gray">
                                  {expense.description}
                                </p>
                                <p className="text-xs text-gray-600">
                                  {formatDate(expense.date)}
                                </p>
                              </div>
                              <span
                                className={`rounded-full px-2 py-1 text-xs ${
                                  expense.status === "approved"
                                    ? "bg-green-100 text-green-700"
                                    : expense.status === "sent"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : "bg-gray-100 text-gray-700"
                                }`}
                              >
                                {expense.status === "approved"
                                  ? "Genehmigt"
                                  : expense.status === "sent"
                                  ? "Gesendet"
                                  : "Entwurf"}
                              </span>
                            </div>
                            {expense.customer_project && (
                              <p className="text-xs text-gray-600 mb-1">
                                Kunde: {expense.customer_project}
                              </p>
                            )}
                            {expense.receipts && expense.receipts.length > 0 && (
                              <div className="mt-2 space-y-1">
                                <p className="text-xs font-semibold text-gray-700">Belege:</p>
                                {expense.receipts.map((receipt) => (
                                  <ReceiptItem
                                    key={receipt.id}
                                    expense={expense}
                                    receipt={receipt}
                                    onDelete={() => {
                                      setReceiptMessage(null);
                                      setReceiptError(null);
                                    }}
                                  />
                                ))}
                              </div>
                            )}
                            {isAdmin && expense.user_name && (
                              <p className="text-xs text-gray-500 mt-2">
                                Von: {expense.user_name}
                              </p>
                            )}
                          </div>
                          {expense.status === "draft" && (
                            <div className="space-y-2">
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEdit(expense)}
                                  className="flex-1"
                                >
                                  Bearbeiten
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => handleDelete(expense.id)}
                                  disabled={deleteMutation.isPending}
                                  className="flex-1"
                                >
                                  Löschen
                                </Button>
                              </div>
                              <ReceiptUploadButton expense={expense} />
                            </div>
                          )}
                        </>
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
                      <th className="px-4 py-3">Datum</th>
                      <th className="px-4 py-3">Kommentar</th>
                      <th className="px-4 py-3">Kunde/Projekt</th>
                      <th className="px-4 py-3">Status</th>
                      {isAdmin && <th className="px-4 py-3">Mitarbeiter</th>}
                      <th className="px-4 py-3">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {expenses.map((expense) => {
                      const isEditing = editingId === expense.id;
                      return (
                        <tr key={expense.id}>
                          {isEditing ? (
                            <>
                              <td className="px-4 py-3">
                                <Input
                                  type="date"
                                  value={editState.date}
                                  onChange={(e) =>
                                    setEditState({ ...editState, date: e.target.value })
                                  }
                                  className="w-32"
                                />
                              </td>
                              <td className="px-4 py-3">
                                <Input
                                  value={editState.description}
                                  onChange={(e) =>
                                    setEditState({
                                      ...editState,
                                      description: e.target.value,
                                    })
                                  }
                                  className="w-full"
                                />
                              </td>
                              <td className="px-4 py-3">
                                <select
                                  className="w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                                  value={editState.customer_project}
                                  onChange={(e) =>
                                    setEditState({
                                      ...editState,
                                      customer_project: e.target.value,
                                    })
                                  }
                                >
                                  <option value="">-</option>
                                  {customers?.map((customer) => (
                                    <option key={customer.id} value={customer.name}>
                                      {customer.name}
                                    </option>
                                  ))}
                                </select>
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {expense.status === "approved"
                                  ? "Genehmigt"
                                  : expense.status === "sent"
                                  ? "Gesendet"
                                  : "Entwurf"}
                              </td>
                              {isAdmin && (
                                <td className="px-4 py-3 text-gray-600">
                                  {expense.user_name}
                                </td>
                              )}
                              <td className="px-4 py-3">
                                <div className="flex gap-2">
                                  <UpdateButton expenseId={expense.id} />
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => {
                                      setEditingId(null);
                                      setEditState(emptyFormState);
                                    }}
                                  >
                                    Abbrechen
                                  </Button>
                                </div>
                              </td>
                            </>
                          ) : (
                            <>
                              <td className="px-4 py-3 text-gray-600">
                                {formatDate(expense.date)}
                              </td>
                              <td className="px-4 py-3 font-medium text-brand-gray">
                                {expense.description}
                                {expense.receipts && expense.receipts.length > 0 && (
                                  <div className="mt-1 text-xs text-gray-500">
                                    {expense.receipts.length} Beleg{expense.receipts.length !== 1 ? "e" : ""}
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-600">
                                {expense.customer_project || "-"}
                              </td>
                              <td className="px-4 py-3">
                                <span
                                  className={`rounded-full px-2 py-1 text-xs ${
                                    expense.status === "approved"
                                      ? "bg-green-100 text-green-700"
                                      : expense.status === "sent"
                                      ? "bg-yellow-100 text-yellow-700"
                                      : "bg-gray-100 text-gray-700"
                                  }`}
                                >
                                  {expense.status === "approved"
                                    ? "Genehmigt"
                                    : expense.status === "sent"
                                    ? "Gesendet"
                                    : "Entwurf"}
                                </span>
                              </td>
                              {isAdmin && (
                                <td className="px-4 py-3 text-gray-600 text-xs">
                                  {expense.user_name}
                                </td>
                              )}
                              <td className="px-4 py-3">
                                {expense.status === "draft" && (
                                  <div className="flex flex-col gap-2">
                                    <div className="flex gap-2">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleEdit(expense)}
                                      >
                                        Bearbeiten
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="destructive"
                                        onClick={() => handleDelete(expense.id)}
                                        disabled={deleteMutation.isPending}
                                      >
                                        Löschen
                                      </Button>
                                    </div>
                                    <ReceiptUploadButton expense={expense} />
                                  </div>
                                )}
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
          ) : (
            <p className="text-center text-gray-500 py-6">
              Keine Reisekosten-Ausgaben gefunden.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

