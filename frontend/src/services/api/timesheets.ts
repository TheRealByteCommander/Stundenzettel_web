import { apiClient } from "./client";
import type {
  CreateTimesheetRequest,
  SendTimesheetEmailRequest,
  UpdateTimesheetRequest,
  WeeklyTimesheet,
} from "./types";

export const fetchTimesheets = async (): Promise<WeeklyTimesheet[]> => {
  const { data } = await apiClient.get<WeeklyTimesheet[]>("/timesheets");
  return data;
};

export const fetchTimesheetById = async (
  id: string
): Promise<WeeklyTimesheet> => {
  const { data } = await apiClient.get<WeeklyTimesheet>(`/timesheets/${id}`);
  return data;
};

export const createTimesheet = async (payload: CreateTimesheetRequest) => {
  const { data } = await apiClient.post<WeeklyTimesheet>(
    "/timesheets",
    payload
  );
  return data;
};

export const updateTimesheet = async (
  id: string,
  payload: UpdateTimesheetRequest
) => {
  const { data } = await apiClient.put<WeeklyTimesheet>(
    `/timesheets/${id}`,
    payload
  );
  return data;
};

export const deleteTimesheet = async (id: string) => {
  await apiClient.delete(`/timesheets/${id}`);
};

export const sendTimesheetEmail = async (
  id: string,
  payload: SendTimesheetEmailRequest = {}
) => {
  await apiClient.post(`/timesheets/${id}/send-email`, payload);
};

export const downloadAndEmailTimesheet = async (id: string) => {
  await apiClient.post(`/timesheets/${id}/download-and-email`);
};

export const approveTimesheet = async (id: string) => {
  await apiClient.post(`/timesheets/${id}/approve`);
};

export const rejectTimesheet = async (id: string) => {
  await apiClient.post(`/timesheets/${id}/reject`);
};

export const uploadSignedTimesheet = async (id: string, file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  await apiClient.post(`/timesheets/${id}/upload-signed`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

