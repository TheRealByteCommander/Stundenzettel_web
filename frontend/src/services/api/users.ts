import { apiClient } from "./client";
import type {
  AdminUserSummary,
  UserCreateRequest,
  UserUpdateRequest,
} from "./types";

export const fetchAdminUsers = async (): Promise<AdminUserSummary[]> => {
  const { data } = await apiClient.get<AdminUserSummary[]>("/users");
  return data;
};

export const createUser = async (
  payload: UserCreateRequest
): Promise<{ message: string; user_id: string }> => {
  const { data } = await apiClient.post<{ message: string; user_id: string }>(
    "/auth/register",
    payload
  );
  return data;
};

export const updateUser = async (
  userId: string,
  payload: UserUpdateRequest
): Promise<{ message: string }> => {
  const { data } = await apiClient.put<{ message: string }>(
    `/users/${userId}`,
    payload
  );
  return data;
};

export const deleteUser = async (userId: string): Promise<{ message: string }> => {
  const { data } = await apiClient.delete<{ message: string }>(
    `/users/${userId}`
  );
  return data;
};

