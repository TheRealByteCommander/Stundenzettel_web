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
  useVacationRequestsQuery,
  useVacationBalanceQuery,
  useVacationRequirementsQuery,
  useCreateVacationRequestMutation,
  useDeleteVacationRequestMutation,
  useApproveVacationRequestMutation,
  useRejectVacationRequestMutation,
  useAdminDeleteVacationRequestMutation,
} from "../hooks/useVacation";
import { useCurrentUserQuery } from "../../auth/hooks/useCurrentUser";

const getCurrentYear = () => new Date().getFullYear();

export const VacationPage = () => {
  const { data: user } = useCurrentUserQuery();
  const isAdmin = user?.role === "admin" || user?.role === "accounting";
  const [year, setYear] = useState(getCurrentYear());
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    start_date: "",
    end_date: "",
    notes: "",
  });

  const { data: requests, isLoading: requestsLoading } = useVacationRequestsQuery(
    isAdmin ? undefined : year
  );
  const { data: balance } = useVacationBalanceQuery(year);
  const { data: requirements } = useVacationRequirementsQuery(year);
  const createMutation = useCreateVacationRequestMutation();
  const deleteMutation = useDeleteVacationRequestMutation();
  const approveMutation = useApproveVacationRequestMutation();
  const rejectMutation = useRejectVacationRequestMutation();
  // const updateBalanceMutation = useUpdateVacationBalanceMutation();
  const adminDeleteMutation = useAdminDeleteVacationRequestMutation();

  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const userBalance = balance?.find((b) => b.user_id === user?.id);

  const handleCreateRequest = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setFormError(null);

    if (!formData.start_date || !formData.end_date) {
      setFormError("Bitte geben Sie Start- und Enddatum an.");
      return;
    }

    try {
      await createMutation.mutateAsync({
        start_date: formData.start_date,
        end_date: formData.end_date,
        notes: formData.notes || undefined,
      });
      setMessage("Urlaubsantrag wurde erstellt.");
      setFormData({ start_date: "", end_date: "", notes: "" });
      setShowCreateForm(false);
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail ?? "Fehler beim Erstellen des Antrags."
      );
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Urlaubsantrag wirklich löschen?")) return;
    try {
      await deleteMutation.mutateAsync(id);
      setMessage("Antrag wurde gelöscht.");
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Fehler beim Löschen.");
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await approveMutation.mutateAsync(id);
      setMessage("Antrag wurde genehmigt.");
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Fehler beim Genehmigen.");
    }
  };

  const handleReject = async (id: string) => {
    try {
      await rejectMutation.mutateAsync(id);
      setMessage("Antrag wurde abgelehnt.");
    } catch (err: any) {
      setFormError(err.response?.data?.detail ?? "Fehler beim Ablehnen.");
    }
  };

  const statusLabels: Record<string, string> = {
    pending: "Ausstehend",
    approved: "Genehmigt",
    rejected: "Abgelehnt",
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-gray">Urlaubsverwaltung</h1>
          <p className="text-sm text-gray-600">
            {isAdmin
              ? "Verwalten Sie Urlaubsanträge und Guthaben."
              : "Stellen Sie Urlaubsanträge und sehen Sie Ihr Guthaben."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Label htmlFor="year-select">Jahr:</Label>
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
      {formError && <Alert variant="destructive">{formError}</Alert>}

      {userBalance && (
        <Card>
          <CardContent className="space-y-2 py-6">
            <CardTitle className="text-base text-brand-gray">
              Urlaubsguthaben {year}
            </CardTitle>
            <div className="text-sm text-gray-600">
              <p>
                Gesamt: <strong>{userBalance.total_days}</strong> Tage
              </p>
              <p>
                Verbraucht: <strong>{userBalance.used_days}</strong> Tage
              </p>
              <p>
                Verfügbar:{" "}
                <strong className="text-brand-primary">
                  {userBalance.total_days - userBalance.used_days}
                </strong>{" "}
                Tage
              </p>
            </div>
            {requirements && (
              <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs">
                <p className="font-medium text-brand-gray">Anforderungen:</p>
                <ul className="mt-1 list-disc space-y-1 pl-4 text-gray-600">
                  <li>
                    Mindestens {requirements.min_total_days} Tage insgesamt
                    {requirements.meets_min_total ? " ✓" : " ✗"}
                  </li>
                  <li>
                    Mindestens {requirements.min_consecutive_days} Tage am Stück
                    {requirements.meets_min_consecutive ? " ✓" : " ✗"}
                  </li>
                  <li>Deadline: {new Date(requirements.deadline).toLocaleDateString("de-DE")}</li>
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!isAdmin && !showCreateForm && (
        <Button onClick={() => setShowCreateForm(true)}>
          Neuer Urlaubsantrag
        </Button>
      )}

      {!isAdmin && showCreateForm && (
        <Card>
          <CardContent className="space-y-4 py-6">
            <CardTitle className="text-lg text-brand-gray">
              Neuer Urlaubsantrag
            </CardTitle>
            <form className="space-y-4" onSubmit={handleCreateRequest}>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="start_date">Startdatum *</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">Enddatum *</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={formData.end_date}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, end_date: e.target.value }))
                    }
                    required
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="notes">Notizen (optional)</Label>
                <textarea
                  id="notes"
                  className="min-h-[100px] w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, notes: e.target.value }))
                  }
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? "Erstelle…" : "Antrag stellen"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateForm(false);
                    setFormData({ start_date: "", end_date: "", notes: "" });
                  }}
                >
                  Abbrechen
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            Urlaubsanträge {year}
          </CardTitle>
          {requestsLoading ? (
            <p className="text-center text-gray-500">Lade Anträge…</p>
          ) : requests && requests.length > 0 ? (
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-600">
                  <tr>
                    <th className="px-4 py-3">Mitarbeiter</th>
                    <th className="px-4 py-3">Von</th>
                    <th className="px-4 py-3">Bis</th>
                    <th className="px-4 py-3">Tage</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Aktionen</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {requests.map((request) => (
                    <tr key={request.id}>
                      <td className="px-4 py-3 text-gray-600">
                        {request.user_name}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(request.start_date).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(request.end_date).toLocaleDateString("de-DE")}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {request.working_days}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-1 text-xs ${
                            request.status === "approved"
                              ? "bg-green-100 text-green-800"
                              : request.status === "rejected"
                              ? "bg-red-100 text-red-800"
                              : "bg-yellow-100 text-yellow-800"
                          }`}
                        >
                          {statusLabels[request.status]}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          {request.status === "pending" && !isAdmin && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDelete(request.id)}
                              disabled={deleteMutation.isPending}
                            >
                              Löschen
                            </Button>
                          )}
                          {isAdmin && request.status === "pending" && (
                            <>
                              <Button
                                size="sm"
                                onClick={() => handleApprove(request.id)}
                                disabled={approveMutation.isPending}
                              >
                                Genehmigen
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleReject(request.id)}
                                disabled={rejectMutation.isPending}
                              >
                                Ablehnen
                              </Button>
                            </>
                          )}
                          {isAdmin && request.status !== "pending" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => adminDeleteMutation.mutateAsync(request.id)}
                              disabled={adminDeleteMutation.isPending}
                            >
                              Löschen
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-center text-gray-500">
              Keine Urlaubsanträge für {year} vorhanden.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

