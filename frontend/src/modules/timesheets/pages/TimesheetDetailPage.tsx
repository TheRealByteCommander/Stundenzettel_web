import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import {
  useApproveTimesheetMutation,
  useRejectTimesheetMutation,
  useSendTimesheetEmailMutation,
  useTimesheetQuery,
  useUploadSignedTimesheetMutation,
  useUpdateTimesheetMutation,
} from "../hooks/useTimesheets";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";
import { useAvailableVehiclesQuery } from "../hooks/useAvailableVehicles";
import { useCustomersQuery } from "../hooks/useCustomers";
import type { TimeEntry } from "../../../services/api/types";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  sent: "Gesendet",
  approved: "Genehmigt",
};

export const TimesheetDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useTimesheetQuery(id);
  const approveMutation = useApproveTimesheetMutation(id ?? "");
  const rejectMutation = useRejectTimesheetMutation(id ?? "");
  const sendMutation = useSendTimesheetEmailMutation(id ?? "");
  const uploadMutation = useUploadSignedTimesheetMutation(id ?? "");
  const updateMutation = useUpdateTimesheetMutation(id ?? "");
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [verificationMessage, setVerificationMessage] = useState<
    string | null
  >(null);
  const [verificationError, setVerificationError] = useState<string | null>(
    null
  );
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [verificationNotes, setVerificationNotes] = useState("");
  const [verificationChecked, setVerificationChecked] = useState(false);
  const [editingEntries, setEditingEntries] = useState<TimeEntry[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const { data: currentUser } = useCurrentUserQuery();
  const { data: vehicles } = useAvailableVehiclesQuery();
  const { data: customers } = useCustomersQuery();
  const isAccounting =
    currentUser?.role === "admin" || currentUser?.role === "accounting";
  const canEdit = data?.status === "draft" && (currentUser?.id === data?.user_id || isAccounting);

  const totalHours = useMemo(() => {
    if (!data || !data.entries) return 0;
    return data.entries.reduce((acc, entry) => {
      if (!entry || !entry.start_time || !entry.end_time) return acc;
      try {
        const start = new Date(`1970-01-01T${entry.start_time}:00`);
        const end = new Date(`1970-01-01T${entry.end_time}:00`);
        const diff =
          (end.getTime() - start.getTime()) / 1000 / 60 - (entry.break_minutes || 0);
        return acc + Math.max(diff, 0) / 60;
      } catch {
        return acc;
      }
    }, 0);
  }, [data]);

  useEffect(() => {
    if (!data || !data.entries) {
      return;
    }
    setVerificationNotes(data.signed_pdf_verification_notes ?? "");
    setVerificationChecked(Boolean(data.signed_pdf_verified));
    // Sicherstellen, dass entries ein Array ist und alle Einträge gültig sind
    const validEntries = Array.isArray(data.entries) ? data.entries.filter(entry => entry != null) : [];
    setEditingEntries(validEntries.length > 0 ? [...validEntries] : []);
  }, [data]);

  if (!id) {
    return (
      <Alert variant="destructive">
        Ungültige URL. Bitte kehren Sie zur Übersicht zurück.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Stundenzettel…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Alert variant="destructive">
          Stundenzettel konnte nicht geladen werden:{" "}
          {(
            error?.response?.data as { detail?: string } | undefined
          )?.detail ?? error?.message ?? "Unbekannter Fehler"}
        </Alert>
        <Button className="mt-4" variant="outline" onClick={() => navigate(-1)}>
          Zurück
        </Button>
      </div>
    );
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !id) {
      return;
    }
    setUploadMessage(null);
    setUploadError(null);

    uploadMutation.mutate(file, {
      onSuccess: async () => {
        setUploadMessage("Unterschriebener Stundenzettel wurde hochgeladen.");
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setUploadError(
          detail ??
            "Upload fehlgeschlagen. Bitte versuchen Sie es erneut."
        );
      },
    });

    event.target.value = "";
  };

  const handleSaveVerification = () => {
    if (!id) {
      return;
    }
    setVerificationMessage(null);
    setVerificationError(null);
    updateMutation.mutate(
      {
        signed_pdf_verification_notes: verificationNotes,
        signed_pdf_verified: verificationChecked,
      },
      {
        onSuccess: async () => {
          setVerificationMessage("Prüfinformationen wurden gespeichert.");
          await refetch();
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setVerificationError(
            detail ?? "Speichern der Prüfinformationen fehlgeschlagen."
          );
        },
      }
    );
  };

  const handleResetVerification = () => {
    if (!data) {
      return;
    }
    setVerificationNotes(data.signed_pdf_verification_notes ?? "");
    setVerificationChecked(Boolean(data.signed_pdf_verified));
    setVerificationMessage(null);
    setVerificationError(null);
  };

  const handleEntryChange = (
    index: number,
    field: keyof TimeEntry,
    value: string | number | boolean | null
  ) => {
    setEditingEntries((prev) =>
      prev.map((entry, idx) =>
        idx === index
          ? {
              ...entry,
              [field]: value,
            }
          : entry
      )
    );
  };

  const handleSaveEntries = () => {
    if (!id || !data) return;
    resetMessages();
    updateMutation.mutate(
      {
        entries: editingEntries,
      },
      {
        onSuccess: async () => {
          setMessage("Stundenzettel wurde aktualisiert.");
          setIsEditing(false);
          await refetch();
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setFormError(detail ?? "Stundenzettel konnte nicht aktualisiert werden.");
        },
      }
    );
  };

  const handleCancelEdit = () => {
    if (!data || !data.entries) return;
    const validEntries = Array.isArray(data.entries) ? data.entries.filter(entry => entry != null) : [];
    setEditingEntries(validEntries.length > 0 ? [...validEntries] : []);
    setIsEditing(false);
    setFormError(null);
  };

  const handleSubmitTimesheet = () => {
    if (!id) return;
    resetMessages();
    sendMutation.mutate(undefined, {
      onSuccess: async () => {
        setMessage("Stundenzettel wurde per E-Mail versendet. Sie erhalten eine Kopie als PDF.");
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setFormError(detail ?? "E-Mail-Versand fehlgeschlagen.");
      },
    });
  };

  const resetMessages = () => {
    setMessage(null);
    setFormError(null);
  };

  const vehicleOptions = useMemo(
    () =>
      vehicles?.map((vehicle) => ({
        value: vehicle.id,
        label: `${vehicle.name} (${vehicle.license_plate})${vehicle.is_pool ? " • Pool" : ""}`,
      })) ?? [],
    [vehicles]
  );

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
      <Button variant="outline" onClick={() => navigate(-1)}>
        Zurück zur Übersicht
      </Button>

      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-brand-gray">
              Stundenzettel {new Date(data.week_start).toLocaleDateString("de-DE")}{" "}
              – {new Date(data.week_end).toLocaleDateString("de-DE")}
            </h1>
            <p className="text-sm text-gray-600">
              Status: {statusLabels[data.status] ?? data.status} • Gesamtstunden:{" "}
              {totalHours.toFixed(2).replace(".", ",")}
            </p>
            {data.signed_pdf_path && (
              <p className="mt-1 text-sm text-gray-500">
                Unterschriebenes Dokument: {data.signed_pdf_path}
                {data.signed_pdf_verified !== undefined && (
                  <>
                    {" "}
                    • Verifiziert:{" "}
                    {data.signed_pdf_verified ? "Ja" : "Nein"}
                  </>
                )}
                {data.signed_pdf_verification_notes && (
                  <span className="block text-xs text-gray-500">
                    Hinweis: {data.signed_pdf_verification_notes}
                  </span>
                )}
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {canEdit && (
              <>
                {!isEditing ? (
                  <Button
                    variant="outline"
                    onClick={() => setIsEditing(true)}
                  >
                    Bearbeiten
                  </Button>
                ) : (
                  <>
                    <Button
                      onClick={handleSaveEntries}
                      disabled={updateMutation.isPending}
                    >
                      {updateMutation.isPending ? "Speichere..." : "Speichern"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleCancelEdit}
                    >
                      Abbrechen
                    </Button>
                  </>
                )}
                <Button
                  onClick={handleSubmitTimesheet}
                  disabled={sendMutation.isPending || isEditing}
                >
                  {sendMutation.isPending ? "Sende..." : "Absenden & per E-Mail senden"}
                </Button>
              </>
            )}
            {!canEdit && data.status === "draft" && (
              <Button
                onClick={handleSubmitTimesheet}
                disabled={sendMutation.isPending}
              >
                {sendMutation.isPending ? "Sende..." : "Absenden & per E-Mail senden"}
              </Button>
            )}
            {isAccounting && (
              <>
                <Button
                  variant="outline"
                  onClick={() => sendMutation.mutate()}
                  disabled={sendMutation.isPending}
                >
                  Per E-Mail senden
                </Button>
                <Button
                  variant="outline"
                  onClick={() => approveMutation.mutate()}
                  disabled={approveMutation.isPending || data.status === "approved"}
                >
                  Genehmigen
                </Button>
                <Button
                  variant="outline"
                  onClick={() => rejectMutation.mutate()}
                  disabled={rejectMutation.isPending}
                >
                  Ablehnen
                </Button>
              </>
            )}
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <h2 className="text-lg font-semibold text-brand-gray">
            Unterschriebenen Stundenzettel hochladen
          </h2>
          <p className="text-sm text-gray-600">
            Akzeptiert werden PDF-Dateien mit der unterschriebenen Version dieses
            Stundenzettels.
          </p>
          <div className="flex items-center gap-4">
            <Input
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              disabled={uploadMutation.isPending}
            />
            {uploadMutation.isPending && (
              <span className="text-sm text-gray-500">
                Upload läuft…
              </span>
            )}
          </div>
          {uploadMessage && <Alert variant="success">{uploadMessage}</Alert>}
          {uploadError && (
            <Alert variant="destructive">{uploadError}</Alert>
          )}
        </div>

        {isAccounting && (
          <div className="mt-6 space-y-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <h2 className="text-lg font-semibold text-brand-gray">
              Prüfbemerkungen & Verifikation
            </h2>
            <p className="text-sm text-gray-600">
              Notieren Sie Hinweise für QA und markieren Sie das Dokument bei
              manueller Prüfung als verifiziert.
            </p>
            <div className="space-y-2">
              <label
                className="text-sm font-medium text-brand-gray"
                htmlFor="verification-notes"
              >
                Prüfbemerkung
              </label>
              <textarea
                id="verification-notes"
                value={verificationNotes}
                onChange={(event) => setVerificationNotes(event.target.value)}
                className="min-h-[120px] w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={verificationChecked}
                onChange={(event) =>
                  setVerificationChecked(event.target.checked)
                }
              />
              Unterschrift manuell verifiziert
            </label>
            {verificationMessage && (
              <Alert variant="success">{verificationMessage}</Alert>
            )}
            {verificationError && (
              <Alert variant="destructive">{verificationError}</Alert>
            )}
            <div className="flex gap-2">
              <Button
                onClick={handleSaveVerification}
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Speichere..." : "Speichern"}
              </Button>
              <Button variant="outline" onClick={handleResetVerification}>
                Zurücksetzen
              </Button>
            </div>
          </div>
        )}

        {message && <Alert variant="success">{message}</Alert>}
        {formError && <Alert variant="destructive">{formError}</Alert>}

        <div className="mt-6 overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
              <tr>
                <th className="px-4 py-3">Datum</th>
                <th className="px-4 py-3">Start</th>
                <th className="px-4 py-3">Ende</th>
                <th className="px-4 py-3">Pause</th>
                <th className="px-4 py-3">Aufgaben</th>
                <th className="px-4 py-3">Projekt</th>
                <th className="px-4 py-3">Ort</th>
                {isEditing && <th className="px-4 py-3">Fahrzeug</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {(isEditing ? (editingEntries || []) : (data?.entries || [])).map((entry, index) => {
                // Sicherstellen, dass entry gültig ist
                if (!entry || !entry.date) return null;
                return (
                  <tr key={`${entry.date}-${index}`}>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          type="date"
                          value={entry.date || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "date", event.target.value)
                          }
                          className="w-full"
                        />
                      ) : (
                        entry.date ? new Date(entry.date).toLocaleDateString("de-DE") : ""
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          type="time"
                          value={entry.start_time || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "start_time", event.target.value)
                          }
                          className="w-full"
                        />
                      ) : (
                        entry.start_time || ""
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          type="time"
                          value={entry.end_time || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "end_time", event.target.value)
                          }
                          className="w-full"
                        />
                      ) : (
                        entry.end_time || ""
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          type="number"
                          min={0}
                          value={entry.break_minutes || 0}
                          onChange={(event) =>
                            handleEntryChange(index, "break_minutes", Number(event.target.value))
                          }
                          className="w-full"
                        />
                      ) : (
                        `${entry.break_minutes || 0} Min`
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          value={entry.tasks || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "tasks", event.target.value)
                          }
                          className="w-full"
                        />
                      ) : (
                        entry.tasks || ""
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                          value={entry.customer_project || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "customer_project", event.target.value)
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
                      ) : (
                        entry.customer_project || "-"
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {isEditing ? (
                        <Input
                          value={entry.location || ""}
                          onChange={(event) =>
                            handleEntryChange(index, "location", event.target.value)
                          }
                          className="w-full"
                        />
                      ) : (
                        entry.location || "-"
                      )}
                    </td>
                    {isEditing && (
                      <td className="px-4 py-3 text-gray-600">
                        <select
                          className="w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                          value={entry.vehicle_id ?? ""}
                          onChange={(event) =>
                            handleEntryChange(index, "vehicle_id", event.target.value || null)
                          }
                        >
                          <option value="">— Kein Fahrzeug —</option>
                          {vehicleOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

