import { useState } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { useChangePasswordMutation } from "../hooks/usePasswordChange";

interface ChangePasswordDialogProps {
  onClose: () => void;
}

export const ChangePasswordDialog = ({ onClose }: ChangePasswordDialogProps) => {
  const [formData, setFormData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [message, setMessage] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const changePasswordMutation = useChangePasswordMutation();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setFormError(null);

    if (!formData.current_password || !formData.new_password) {
      setFormError("Bitte füllen Sie alle Felder aus.");
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setFormError("Die neuen Passwörter stimmen nicht überein.");
      return;
    }

    if (formData.new_password.length < 8) {
      setFormError("Das neue Passwort muss mindestens 8 Zeichen lang sein.");
      return;
    }

    try {
      await changePasswordMutation.mutateAsync({
        current_password: formData.current_password,
        new_password: formData.new_password,
      });
      setMessage("Passwort wurde erfolgreich geändert.");
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail ?? "Fehler beim Ändern des Passworts."
      );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-xl font-semibold text-brand-gray">
          Passwort ändern
        </h2>
        {message && <Alert variant="success">{message}</Alert>}
        {formError && <Alert variant="destructive">{formError}</Alert>}
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="current_password">Aktuelles Passwort *</Label>
            <Input
              id="current_password"
              type="password"
              value={formData.current_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  current_password: e.target.value,
                }))
              }
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new_password">Neues Passwort *</Label>
            <Input
              id="new_password"
              type="password"
              value={formData.new_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  new_password: e.target.value,
                }))
              }
              required
              minLength={8}
            />
            <p className="text-xs text-gray-500">
              Mindestens 8 Zeichen
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm_password">Neues Passwort bestätigen *</Label>
            <Input
              id="confirm_password"
              type="password"
              value={formData.confirm_password}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  confirm_password: e.target.value,
                }))
              }
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Abbrechen
            </Button>
            <Button
              type="submit"
              disabled={changePasswordMutation.isPending}
            >
              {changePasswordMutation.isPending ? "Ändere…" : "Passwort ändern"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

