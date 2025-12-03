import { useState, useEffect } from "react";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardTitle,
} from "../../../components/ui/card";
import { Label } from "../../../components/ui/label";
import {
  useNotificationPreferencesQuery,
  useUpdateNotificationPreferencesMutation,
} from "../hooks/useNotificationPreferences";
import type { NotificationPreferences, NotificationPreferencesUpdate } from "../../../services/api/notifications";
import type { NotificationPreferences } from "../../../services/api/notifications";

export const NotificationSettingsPage = () => {
  const { data: preferences, isLoading } = useNotificationPreferencesQuery();
  const updateMutation = useUpdateNotificationPreferencesMutation();
  
  const [localPrefs, setLocalPrefs] = useState<NotificationPreferences | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Update local state when preferences load
  useEffect(() => {
    if (preferences) {
      setLocalPrefs(preferences);
    }
  }, [preferences]);

  const handleToggle = (key: keyof NotificationPreferences) => {
    if (!localPrefs) return;
    setLocalPrefs({
      ...localPrefs,
      [key]: !localPrefs[key],
    });
  };

  const handleSave = async () => {
    if (!localPrefs || !preferences) return;
    
    setMessage(null);
    setError(null);

    const updates: Partial<NotificationPreferences> = {};
    if (localPrefs.email_notifications !== preferences.email_notifications) {
      updates.email_notifications = localPrefs.email_notifications;
    }
    if (localPrefs.push_notifications !== preferences.push_notifications) {
      updates.push_notifications = localPrefs.push_notifications;
    }
    if (localPrefs.timesheet_reminders !== preferences.timesheet_reminders) {
      updates.timesheet_reminders = localPrefs.timesheet_reminders;
    }
    if (localPrefs.vacation_reminders !== preferences.vacation_reminders) {
      updates.vacation_reminders = localPrefs.vacation_reminders;
    }
    if (localPrefs.expense_reminders !== preferences.expense_reminders) {
      updates.expense_reminders = localPrefs.expense_reminders;
    }
    if (localPrefs.admin_notifications !== undefined && preferences.admin_notifications !== undefined &&
        localPrefs.admin_notifications !== preferences.admin_notifications) {
      updates.admin_notifications = localPrefs.admin_notifications;
    }

    if (Object.keys(updates).length === 0) {
      setMessage("Keine Änderungen vorgenommen");
      return;
    }

    try {
      await updateMutation.mutateAsync(updates);
      setMessage("Benachrichtigungseinstellungen erfolgreich aktualisiert");
    } catch (err) {
      const errorMessage =
        (err as { response?: { data?: { detail?: string } } }).response?.data
          ?.detail ?? (err as { message?: string }).message ?? "Fehler beim Speichern";
      setError(errorMessage);
    }
  };

  if (isLoading || !localPrefs) {
    return (
      <div className="mx-auto flex max-w-4xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
        <p className="text-center text-gray-500 py-6">Lade Einstellungen…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-4 sm:gap-6 px-3 sm:px-4 py-4 sm:py-8">
      <div>
        <h1 className="text-xl sm:text-2xl font-semibold text-brand-gray">
          Benachrichtigungseinstellungen
        </h1>
        <p className="text-xs sm:text-sm text-gray-600">
          Verwalten Sie Ihre Benachrichtigungspräferenzen.
        </p>
      </div>

      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="destructive">{error}</Alert>}

      <Card>
        <CardContent className="space-y-4 py-4 sm:py-6">
          <CardTitle className="text-base sm:text-lg text-brand-gray">
            Benachrichtigungstypen
          </CardTitle>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex-1">
                <Label htmlFor="email-notifications" className="text-sm font-medium text-brand-gray">
                  E-Mail-Benachrichtigungen
                </Label>
                <p className="text-xs text-gray-600 mt-1">
                  Erhalten Sie Benachrichtigungen per E-Mail.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  id="email-notifications"
                  checked={localPrefs.email_notifications}
                  onChange={() => handleToggle("email_notifications")}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex-1">
                <Label htmlFor="push-notifications" className="text-sm font-medium text-brand-gray">
                  Push-Benachrichtigungen
                </Label>
                <p className="text-xs text-gray-600 mt-1">
                  Erhalten Sie Push-Benachrichtigungen im Browser.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  id="push-notifications"
                  checked={localPrefs.push_notifications}
                  onChange={() => handleToggle("push_notifications")}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex-1">
                <Label htmlFor="timesheet-reminders" className="text-sm font-medium text-brand-gray">
                  Stundenzettel-Erinnerungen
                </Label>
                <p className="text-xs text-gray-600 mt-1">
                  Erinnerungen für ausstehende Stundenzettel.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  id="timesheet-reminders"
                  checked={localPrefs.timesheet_reminders}
                  onChange={() => handleToggle("timesheet_reminders")}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex-1">
                <Label htmlFor="vacation-reminders" className="text-sm font-medium text-brand-gray">
                  Urlaubs-Erinnerungen
                </Label>
                <p className="text-xs text-gray-600 mt-1">
                  Erinnerungen für Urlaubsplanung und -anforderungen.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  id="vacation-reminders"
                  checked={localPrefs.vacation_reminders}
                  onChange={() => handleToggle("vacation_reminders")}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex-1">
                <Label htmlFor="expense-reminders" className="text-sm font-medium text-brand-gray">
                  Reisekosten-Erinnerungen
                </Label>
                <p className="text-xs text-gray-600 mt-1">
                  Erinnerungen für ausstehende Reisekostenabrechnungen.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  id="expense-reminders"
                  checked={localPrefs.expense_reminders}
                  onChange={() => handleToggle("expense_reminders")}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
              </label>
            </div>

            {localPrefs.admin_notifications !== undefined && (
              <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4">
                <div className="flex-1">
                  <Label htmlFor="admin-notifications" className="text-sm font-medium text-brand-gray">
                    Admin-Benachrichtigungen
                  </Label>
                  <p className="text-xs text-gray-600 mt-1">
                    Benachrichtigungen für administrative Aufgaben.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    id="admin-notifications"
                    checked={localPrefs.admin_notifications}
                    onChange={() => handleToggle("admin_notifications")}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-brand-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
                </label>
              </div>
            )}
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="flex-1"
            >
              {updateMutation.isPending ? "Speichere..." : "Einstellungen speichern"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

