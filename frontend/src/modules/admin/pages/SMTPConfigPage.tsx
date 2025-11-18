import { useState, useEffect } from "react";
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
  useSMTPConfigQuery,
  useUpdateSMTPConfigMutation,
} from "../hooks/useAdminSettings";

export const SMTPConfigPage = () => {
  const { data: config, isLoading } = useSMTPConfigQuery();
  const updateMutation = useUpdateSMTPConfigMutation();
  const [formData, setFormData] = useState({
    smtp_server: "",
    smtp_port: 587,
    smtp_username: "",
    smtp_password: "",
    admin_email: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (config) {
      setFormData({
        smtp_server: config.smtp_server || "",
        smtp_port: config.smtp_port || 587,
        smtp_username: config.smtp_username || "",
        smtp_password: "", // Passwort wird nicht angezeigt
        admin_email: config.admin_email || "",
      });
    }
  }, [config]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setFormError(null);

    if (
      !formData.smtp_server ||
      !formData.smtp_username ||
      !formData.admin_email
    ) {
      setFormError("Bitte füllen Sie alle Pflichtfelder aus.");
      return;
    }

    try {
      await updateMutation.mutateAsync(formData);
      setMessage("SMTP-Konfiguration wurde erfolgreich gespeichert.");
      setFormData((prev) => ({ ...prev, smtp_password: "" })); // Passwort-Feld leeren
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail ?? "Fehler beim Speichern der SMTP-Konfiguration."
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
        Lade SMTP-Konfiguration…
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-brand-gray">
          SMTP-Konfiguration
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Konfigurieren Sie die E-Mail-Einstellungen für den Versand von
          Benachrichtigungen und Stundenzetteln.
        </p>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {formError && <Alert variant="destructive">{formError}</Alert>}

      <Card>
        <CardContent className="space-y-4 py-6">
          <CardTitle className="text-lg text-brand-gray">
            E-Mail-Server-Einstellungen
          </CardTitle>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="smtp_server">SMTP-Server *</Label>
                <Input
                  id="smtp_server"
                  type="text"
                  value={formData.smtp_server}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, smtp_server: e.target.value }))
                  }
                  placeholder="z.B. smtp.gmail.com"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_port">SMTP-Port *</Label>
                <Input
                  id="smtp_port"
                  type="number"
                  min="1"
                  max="65535"
                  value={formData.smtp_port}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      smtp_port: Number(e.target.value),
                    }))
                  }
                  required
                />
                <p className="text-xs text-gray-500">
                  Üblich: 587 (TLS) oder 465 (SSL)
                </p>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_username">SMTP-Benutzername *</Label>
              <Input
                id="smtp_username"
                type="text"
                value={formData.smtp_username}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, smtp_username: e.target.value }))
                }
                placeholder="Ihre E-Mail-Adresse"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_password">SMTP-Passwort *</Label>
              <Input
                id="smtp_password"
                type="password"
                value={formData.smtp_password}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, smtp_password: e.target.value }))
                }
                placeholder={
                  config ? "Leer lassen, um nicht zu ändern" : "Ihr E-Mail-Passwort"
                }
                required={!config}
              />
              <p className="text-xs text-gray-500">
                {config
                  ? "Nur ausfüllen, wenn Sie das Passwort ändern möchten."
                  : "Für Gmail: Verwenden Sie ein App-Passwort, nicht Ihr normales Passwort."}
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="admin_email">Admin-E-Mail *</Label>
              <Input
                id="admin_email"
                type="email"
                value={formData.admin_email}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, admin_email: e.target.value }))
                }
                placeholder="admin@example.com"
                required
              />
              <p className="text-xs text-gray-500">
                Diese E-Mail-Adresse wird als Absender für System-E-Mails verwendet.
              </p>
            </div>
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Speichere…" : "Konfiguration speichern"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

