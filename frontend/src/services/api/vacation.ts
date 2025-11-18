import { apiClient } from "./client";

export interface VacationRequest {
  id: string;
  user_id: string;
  user_name: string;
  start_date: string;
  end_date: string;
  working_days: number;
  year: number;
  status: "pending" | "approved" | "rejected";
  notes?: string | null;
  created_at?: string;
}

export interface VacationRequestCreate {
  start_date: string;
  end_date: string;
  notes?: string | null;
}

export interface VacationBalance {
  id: string;
  user_id: string;
  user_name: string;
  year: number;
  total_days: number;
  used_days: number;
}

export interface VacationBalanceUpdate {
  total_days: number;
}

export interface VacationRequirements {
  min_total_days: number;
  min_consecutive_days: number;
  deadline: string;
  meets_min_total: boolean;
  meets_min_consecutive: boolean;
  needs_reminder: boolean;
}

export const fetchVacationRequests = async (
  year?: number
): Promise<VacationRequest[]> => {
  const { data } = await apiClient.get<VacationRequest[]>("/vacation/requests", {
    params: year ? { year } : undefined,
  });
  return data;
};

export const createVacationRequest = async (
  payload: VacationRequestCreate
): Promise<VacationRequest> => {
  const { data } = await apiClient.post<VacationRequest>(
    "/vacation/requests",
    payload
  );
  return data;
};

export const deleteVacationRequest = async (id: string): Promise<void> => {
  await apiClient.delete(`/vacation/requests/${id}`);
};

export const approveVacationRequest = async (id: string): Promise<void> => {
  await apiClient.post(`/vacation/requests/${id}/approve`);
};

export const rejectVacationRequest = async (id: string): Promise<void> => {
  await apiClient.post(`/vacation/requests/${id}/reject`);
};

export const adminDeleteVacationRequest = async (id: string): Promise<void> => {
  await apiClient.delete(`/vacation/requests/${id}/admin-delete`);
};

export const fetchVacationBalance = async (
  year?: number
): Promise<VacationBalance[]> => {
  const { data } = await apiClient.get<VacationBalance[]>("/vacation/balance", {
    params: year ? { year } : undefined,
  });
  return data;
};

export const updateVacationBalance = async (
  userId: string,
  year: number,
  payload: VacationBalanceUpdate
): Promise<void> => {
  await apiClient.put(`/vacation/balance/${userId}/${year}`, payload);
};

export const fetchVacationRequirements = async (
  year: number
): Promise<VacationRequirements> => {
  const { data } = await apiClient.get<VacationRequirements>(
    `/vacation/requirements/${year}`
  );
  return data;
};

