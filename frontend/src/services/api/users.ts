import { apiClient } from "./client";
import type { AdminUserSummary } from "./types";

export const fetchAdminUsers = async (): Promise<AdminUserSummary[]> => {
  const { data } = await apiClient.get<AdminUserSummary[]>("/users");
  return data;
};

