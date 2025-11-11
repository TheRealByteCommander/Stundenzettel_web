import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
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
import { fetchVehicles } from "../../../services/api/vehicles";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  sent: "Gesendet",
  approved: "Genehmigt",
};

export const TimesheetDetailPage = () => {
  const { id } = useParams();
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
  const [verificationNotes, setVerificationNotes] = useState("");
  const [verificationChecked, setVerificationChecked] = useState(false);
  const { data: currentUser } = useCurrentUserQuery();
  const isAccounting =
    currentUser?.role === "admin" || currentUser?.role === "accounting";
  const { data: availableVehicles } = useAvailableVehiclesQuery();
  const { data: adminVehicles } = useQuery({
    queryKey: ["all-vehicles-admin"],
    queryFn: fetchVehicles,
    enabled: isAccounting,
  });
  const vehicleLookup = useMemo(() => {
    const map = new Map<string, string>();
    availableVehicles?.forEach((vehicle) => {
      map.set(
        vehicle.id,
        `${vehicle.name} (${vehicle.license_plate})${
          vehicle.is_pool ? " • Pool" : ""
        }`
      );
    });
    if (isAccounting && adminVehicles) {
      adminVehicles.forEach((vehicle) => {
        map.set(
          vehicle.id,
          `${vehicle.name} (${vehicle.license_plate})${
            vehicle.is_pool ? " • Pool" : ""
          }`
        );
      });
    }
    return map;
  }, [availableVehicles, adminVehicles, isAccounting]);
  const resolveVehicleLabel = useCallback(
    (vehicleId?: string | null) => {
      if (!vehicleId) {
        return "—";
      }
      return vehicleLookup.get(vehicleId) ?? "Unbekanntes Fahrzeug";
    },
    [vehicleLookup]
  );

  const totalHours = useMemo(() => {
    if (!data) return 0;
    return data.entries.reduce((acc, entry) => {
      const start = new Date(`1970-01-01T${entry.start_time}:00`);
      const end = new Date(`1970-01-01T${entry.end_time}:00`);
      const diff =
        (end.getTime() - start.getTime()) / 1000 / 60 - entry.break_minutes;
      return acc + Math.max(diff, 0) / 60;
    }, 0);
  }, [data]);

  useEffect(() => {
    if (!data) {
      return;
    }
    setVerificationNotes(data.signed_pdf_verification_notes ?? "");
    setVerificationChecked(Boolean(data.signed_pdf_verified));
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

  const weekVehicleLabel = resolveVehicleLabel(data.week_vehicle_id);

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
            <p className="text-xs text-gray-500">
              Fahrzeug (Woche): {weekVehicleLabel}
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
                <th className="px-4 py-3">Fahrzeug</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.entries.map((entry, index) => (
                <tr key={`${entry.date}-${index}`}>
                  <td className="px-4 py-3 text-gray-600">
                    {new Date(entry.date).toLocaleDateString("de-DE")}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{entry.start_time}</td>
                  <td className="px-4 py-3 text-gray-600">{entry.end_time}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {entry.break_minutes} Min
                  </td>
                  <td className="px-4 py-3 text-gray-600">{entry.tasks}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {entry.customer_project || "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {resolveVehicleLabel(entry.vehicle_id ?? data.week_vehicle_id)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

