import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchNotificationPreferences,
  updateNotificationPreferences,
  type NotificationPreferencesUpdate,
} from "../../../services/api/notifications";

export const useNotificationPreferencesQuery = () => {
  return useQuery({
    queryKey: ["notification-preferences"],
    queryFn: fetchNotificationPreferences,
  });
};

export const useUpdateNotificationPreferencesMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: NotificationPreferencesUpdate) =>
      updateNotificationPreferences(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notification-preferences"] });
    },
  });
};

