import { apiClient } from "./client";

export interface NotificationPreferences {
  user_id: string;
  email_notifications: boolean;
  push_notifications: boolean;
  timesheet_reminders: boolean;
  vacation_reminders: boolean;
  expense_reminders: boolean;
  admin_notifications: boolean;
  updated_at?: string;
}

export interface NotificationPreferencesUpdate {
  email_notifications?: boolean;
  push_notifications?: boolean;
  timesheet_reminders?: boolean;
  vacation_reminders?: boolean;
  expense_reminders?: boolean;
  admin_notifications?: boolean;
}

export const fetchNotificationPreferences = async (): Promise<NotificationPreferences> => {
  const { data } = await apiClient.get<NotificationPreferences>("/user/notification-preferences");
  return data;
};

export const updateNotificationPreferences = async (
  payload: NotificationPreferencesUpdate
): Promise<NotificationPreferences> => {
  const { data } = await apiClient.put<NotificationPreferences>(
    "/user/notification-preferences",
    payload
  );
  return data;
};

