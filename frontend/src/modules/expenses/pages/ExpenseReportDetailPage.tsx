import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import {
  useApproveExpenseReportMutation,
  useDeleteExpenseReceiptMutation,
  useRejectExpenseReportMutation,
  useSendExpenseReportChatMutation,
  useSubmitExpenseReportMutation,
  useTravelExpenseReportQuery,
  useUploadExchangeProofMutation,
  useUploadExpenseReportReceiptMutation,
} from "../hooks/useTravelExpenseReports";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";

const statusLabels: Record<string, string> = {
  draft: "Entwurf",
  in_review: "In Prüfung",
  approved: "Freigegeben",
  rejected: "Zurückgewiesen",
  submitted: "Übermittelt",
};

export const ExpenseReportDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const reportId = id ?? "";
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useTravelExpenseReportQuery(id);
  const submitMutation = useSubmitExpenseReportMutation();
  const approveMutation = useApproveExpenseReportMutation();
  const rejectMutation = useRejectExpenseReportMutation();
  const uploadReceiptMutation = useUploadExpenseReportReceiptMutation(reportId);
  const uploadExchangeProofMutation = useUploadExchangeProofMutation(reportId);
  const deleteReceiptMutation = useDeleteExpenseReceiptMutation(reportId);
  const sendChatMutation = useSendExpenseReportChatMutation(reportId);
  const { data: currentUser } = useCurrentUserQuery();

  const isAccounting =
    currentUser?.role === "admin" || currentUser?.role === "accounting";

  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [receiptMessage, setReceiptMessage] = useState<string | null>(null);
  const [receiptError, setReceiptError] = useState<string | null>(null);
  const [exchangeMessage, setExchangeMessage] = useState<string | null>(null);
  const [exchangeError, setExchangeError] = useState<string | null>(null);
  const [chatSuccess, setChatSuccess] = useState<string | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [approvalMessage, setApprovalMessage] = useState<string | null>(null);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [chatDraft, setChatDraft] = useState("");
  const [rejectReason, setRejectReason] = useState("");

  const receiptAnalyses = useMemo(() => {
    const map: Record<string, any> = {};
    data?.document_analyses?.forEach((entry) => {
      if (!entry) return;
      const receiptId =
        (entry as { receipt_id?: string }).receipt_id ??
        (entry as { receiptId?: string }).receiptId;
      if (receiptId) {
        map[receiptId] = (entry as { analysis?: unknown }).analysis ?? entry;
      }
    });
    return map;
  }, [data?.document_analyses]);

  if (!id) {
    return (
      <Alert variant="destructive">
        Ungültige URL – keine Reisekostenabrechnung ausgewählt.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade Reisekostenabrechnung…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <Alert variant="destructive">
          Reisekostenabrechnung konnte nicht geladen werden:{" "}
          {(error?.response?.data as { detail?: string } | undefined)?.detail ??
            error?.message ??
            "Unbekannter Fehler"}
        </Alert>
        <Button className="mt-4" variant="outline" onClick={() => navigate(-1)}>
          Zurück
        </Button>
      </div>
    );
  }

  const handleSubmit = () => {
    setSubmitMessage(null);
    setSubmitError(null);
    submitMutation.mutate(data.id, {
      onSuccess: async (response) => {
        setSubmitMessage(response.message);
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setSubmitError(
          detail ?? "Einreichen der Reisekostenabrechnung fehlgeschlagen."
        );
      },
    });
  };

  const handleReceiptUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    setReceiptMessage(null);
    setReceiptError(null);
    uploadReceiptMutation.mutate(file, {
      onSuccess: async (response) => {
        setReceiptMessage(response.message);
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setReceiptError(
          detail ?? "Beleg konnte nicht hochgeladen werden. Bitte erneut versuchen."
        );
      },
    });
  };

  const handleExchangeProofUpload =
    (receiptId: string) => async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) {
        return;
      }
      setExchangeMessage(null);
      setExchangeError(null);
      uploadExchangeProofMutation.mutate(
        { receiptId, file },
        {
          onSuccess: async (response) => {
            setExchangeMessage(response.message);
            await refetch();
          },
          onError: (err) => {
            const detail =
              (err.response?.data as { detail?: string } | undefined)?.detail ??
              err.message;
            setExchangeError(
              detail ??
                "Fremdwährungsnachweis konnte nicht hochgeladen werden."
            );
          },
        }
      );
    };

  const handleDeleteReceipt = (receiptId: string) => {
    if (
      !window.confirm(
        "Beleg wirklich entfernen? Dieser Schritt kann nicht rückgängig gemacht werden."
      )
    ) {
      return;
    }
    setReceiptMessage(null);
    setReceiptError(null);
    deleteReceiptMutation.mutate(receiptId, {
      onSuccess: async () => {
        setReceiptMessage("Beleg wurde entfernt.");
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setReceiptError(
          detail ?? "Beleg konnte nicht entfernt werden. Bitte erneut versuchen."
        );
      },
    });
  };

  const handleApprove = () => {
    setApprovalMessage(null);
    setApprovalError(null);
    approveMutation.mutate(data.id, {
      onSuccess: async (response) => {
        setApprovalMessage(response.message);
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setApprovalError(detail ?? "Genehmigung fehlgeschlagen.");
      },
    });
  };

  const handleReject = (event: React.FormEvent) => {
    event.preventDefault();
    setApprovalMessage(null);
    setApprovalError(null);
    rejectMutation.mutate(
      { id: data.id, reason: rejectReason || undefined },
      {
        onSuccess: async (response) => {
          setApprovalMessage(response.message);
          setRejectReason("");
          await refetch();
        },
        onError: (err) => {
          const detail =
            (err.response?.data as { detail?: string } | undefined)?.detail ??
            err.message;
          setApprovalError(detail ?? "Zurückweisung fehlgeschlagen.");
        },
      }
    );
  };

  const handleSendChatMessage = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = chatDraft.trim();
    if (!trimmed) {
      return;
    }
    setChatSuccess(null);
    setChatError(null);
    sendChatMutation.mutate(trimmed, {
      onSuccess: async () => {
        setChatSuccess("Nachricht wurde gesendet.");
        setChatDraft("");
        await refetch();
      },
      onError: (err) => {
        const detail =
          (err.response?.data as { detail?: string } | undefined)?.detail ??
          err.message;
        setChatError(detail ?? "Nachricht konnte nicht gesendet werden.");
      },
    });
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">
            Reisekostenabrechnung {data.month}
          </h1>
          <p className="text-sm text-gray-600">
            Status: {statusLabels[data.status] ?? data.status} • Einträge:{" "}
            {data.entries.length}
          </p>
        </div>
        <Button variant="outline" onClick={() => navigate(-1)}>
          Zur Übersicht
        </Button>
      </div>

      {submitMessage && <Alert variant="success">{submitMessage}</Alert>}
      {submitError && <Alert variant="destructive">{submitError}</Alert>}
      {approvalMessage && <Alert variant="success">{approvalMessage}</Alert>}
      {approvalError && <Alert variant="destructive">{approvalError}</Alert>}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Reiseeinträge
          </CardTitle>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                <tr>
                  <th className="px-4 py-3">Datum</th>
                  <th className="px-4 py-3">Ort</th>
                  <th className="px-4 py-3">Projekt</th>
                  <th className="px-4 py-3">Fahrzeit</th>
                  <th className="px-4 py-3">Arbeitsstunden</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.entries.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-6 text-center text-gray-500"
                    >
                      Noch keine Reiseeinträge vorhanden. Bericht wurde
                      vermutlich frisch initialisiert.
                    </td>
                  </tr>
                ) : (
                  data.entries.map((entry) => (
                    <tr key={entry.date}>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(entry.date).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.location || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.customer_project || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {(entry.travel_time_minutes / 60).toLocaleString(
                          "de-DE",
                          { minimumFractionDigits: 1, maximumFractionDigits: 1 }
                        )}{" "}
                        h
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {entry.working_hours.toLocaleString("de-DE", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        })}{" "}
                        h
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-500">
            Einträge werden automatisch aus freigegebenen Stundenzetteln
            generiert. Ergänzungen (z. B. zusätzliche Reisetage) folgen in einem
            späteren Schritt.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Belege & Dokumente (Preview)
          </CardTitle>
          <p className="text-sm text-gray-600">
            Die Backend-API unterstützt bereits das Hochladen verschlüsselter
            PDFs und optionaler Fremdwährungsnachweise. Die UI-Anbindung erfolgt
            in den nächsten Schritten. Aktueller Status:
          </p>
          {data.status === "draft" && (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Input
                type="file"
                accept="application/pdf"
                onChange={handleReceiptUpload}
                disabled={uploadReceiptMutation.isPending}
              />
              {uploadReceiptMutation.isPending && (
                <span className="text-sm text-gray-500">Upload läuft…</span>
              )}
            </div>
          )}
          {receiptMessage && <Alert variant="success">{receiptMessage}</Alert>}
          {receiptError && <Alert variant="destructive">{receiptError}</Alert>}
          {exchangeMessage && <Alert variant="success">{exchangeMessage}</Alert>}
          {exchangeError && <Alert variant="destructive">{exchangeError}</Alert>}
          {data.receipts.length === 0 ? (
            <Alert>
              Noch keine Belege vorhanden. Nutzen Sie in Kürze den Upload-Dialog,
              um Dokumente anzuhängen.
            </Alert>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Dateiname</th>
                    <th className="px-4 py-3">Größe</th>
                    <th className="px-4 py-3">Fremdwährung</th>
                    <th className="px-4 py-3">Nachweis</th>
                    <th className="px-4 py-3">Hinweise</th>
                    <th className="px-4 py-3">Aktionen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {data.receipts.map((receipt) => (
                    <tr key={receipt.id}>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.filename}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {(receipt.file_size / 1024).toLocaleString("de-DE", {
                          minimumFractionDigits: 1,
                          maximumFractionDigits: 1,
                        })}{" "}
                        KB
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.currency ?? "EUR"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {receipt.exchange_proof_filename
                          ? "Nachweis vorhanden"
                          : receipt.needs_exchange_proof
                          ? "Nachweis erforderlich"
                          : "–"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {Array.isArray(
                          receiptAnalyses[receipt.id]?.validation_issues
                        ) &&
                        receiptAnalyses[receipt.id]?.validation_issues?.length >
                          0 ? (
                          <ul className="list-disc space-y-1 pl-4">
                            {(
                              receiptAnalyses[receipt.id]
                                ?.validation_issues as string[]
                            ).map((issue, index) => (
                              <li key={`${receipt.id}-issue-${index}`}>
                                {issue}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <span className="text-sm text-gray-500">
                            Keine Hinweise
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                          {receipt.needs_exchange_proof &&
                            data.status === "draft" && (
                              <label className="flex flex-col text-xs text-gray-500">
                                Fremdwährungsnachweis
                                <Input
                                  type="file"
                                  accept="application/pdf"
                                  onChange={handleExchangeProofUpload(
                                    receipt.id
                                  )}
                                  disabled={uploadExchangeProofMutation.isPending}
                                />
                              </label>
                            )}
                          {data.status === "draft" && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteReceipt(receipt.id)}
                              disabled={deleteReceiptMutation.isPending}
                            >
                              Entfernen
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Bericht einreichen
          </CardTitle>
          <p className="text-sm text-gray-600">
            Vor dem Einreichen müssen alle zugehörigen Stundenzettel freigegeben
            und unterschrieben sein. Das Backend validiert dies automatisch.
          </p>
          <Button
            onClick={handleSubmit}
            disabled={
              submitMutation.isPending ||
              data.status !== "draft" ||
              data.entries.length === 0
            }
          >
            {submitMutation.isPending ? "Reicht ein…" : "Bericht einreichen"}
          </Button>
          {data.status !== "draft" && (
            <p className="text-xs text-gray-500">
              Der Bericht befindet sich bereits im Status „
              {statusLabels[data.status] ?? data.status}“.
            </p>
          )}
        </CardContent>
      </Card>

      {(isAccounting || data.chat_messages?.length) && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Chat & Prüf-Hinweise
            </CardTitle>
            <div className="max-h-64 overflow-y-auto rounded-lg border border-gray-200 bg-white">
              {data.chat_messages && data.chat_messages.length > 0 ? (
                <ul className="divide-y divide-gray-100 text-sm">
                  {data.chat_messages.map((message) => (
                    <li key={message.id} className="px-4 py-3">
                      <p className="font-medium text-brand-gray">
                        {message.sender}
                        {message.role ? ` (${message.role})` : ""}
                      </p>
                      <p className="mt-1 whitespace-pre-line text-gray-700">
                        {message.message}
                      </p>
                      {message.created_at && (
                        <p className="mt-1 text-xs text-gray-500">
                          {new Date(message.created_at).toLocaleString("de-DE")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="px-4 py-6 text-center text-sm text-gray-500">
                  Noch keine Chat-Nachrichten vorhanden.
                </div>
              )}
            </div>
            {chatSuccess && <Alert variant="success">{chatSuccess}</Alert>}
            {chatError && <Alert variant="destructive">{chatError}</Alert>}
            <form className="space-y-3" onSubmit={handleSendChatMessage}>
              <label className="text-sm font-medium text-brand-gray" htmlFor="chat-message">
                Neue Nachricht
              </label>
              <textarea
                id="chat-message"
                value={chatDraft}
                onChange={(event) => setChatDraft(event.target.value)}
                className="min-h-[120px] w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                placeholder="Nachricht an Buchhaltung oder Agenten…"
              />
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={sendChatMutation.isPending || !chatDraft.trim()}
                >
                  {sendChatMutation.isPending ? "Sende…" : "Nachricht senden"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {isAccounting && data.status === "in_review" && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Prüfung (Buchhaltung/Admin)
            </CardTitle>
            <p className="text-sm text-gray-600">
              Überprüfen Sie die Belege und bestätigen Sie die Reisekosten oder
              geben Sie einen Ablehnungsgrund an.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                onClick={handleApprove}
                disabled={approveMutation.isPending}
              >
                {approveMutation.isPending ? "Genehmige…" : "Bericht genehmigen"}
              </Button>
              <form
                className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center"
                onSubmit={handleReject}
              >
                <textarea
                  value={rejectReason}
                  onChange={(event) => setRejectReason(event.target.value)}
                  className="min-h-[80px] flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                  placeholder="Begründung für Zurückweisung (optional)"
                />
                <Button
                  type="submit"
                  variant="outline"
                  disabled={rejectMutation.isPending}
                >
                  {rejectMutation.isPending ? "Weise zurück…" : "Zurückweisen"}
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

