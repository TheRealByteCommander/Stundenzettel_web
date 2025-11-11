import { apiClient } from "./client";
import type {
  ExpenseReportMonthOption,
  TravelExpenseReport,
  TravelExpenseReportChatMessage,
  TravelExpenseReportUpdate,
} from "./types";

export interface TravelExpenseReportListParams {
  month?: string;
}

export const fetchTravelExpenseReports = async (
  params: TravelExpenseReportListParams = {}
): Promise<TravelExpenseReport[]> => {
  const { data } = await apiClient.get<TravelExpenseReport[]>(
    "/travel-expense-reports",
    { params }
  );
  return data;
};

export const fetchAvailableExpenseReportMonths = async (): Promise<
  ExpenseReportMonthOption[]
> => {
  const { data } = await apiClient.get<ExpenseReportMonthOption[]>(
    "/travel-expense-reports/available-months"
  );
  return data;
};

export const initializeTravelExpenseReport = async (
  month: string
): Promise<TravelExpenseReport> => {
  const { data } = await apiClient.post<TravelExpenseReport>(
    `/travel-expense-reports/initialize/${month}`
  );
  return data;
};

export const fetchTravelExpenseReport = async (
  id: string
): Promise<TravelExpenseReport> => {
  const { data } = await apiClient.get<TravelExpenseReport>(
    `/travel-expense-reports/${id}`
  );
  return data;
};

export const updateTravelExpenseReport = async (
  id: string,
  payload: TravelExpenseReportUpdate
): Promise<TravelExpenseReport> => {
  const { data } = await apiClient.put<TravelExpenseReport>(
    `/travel-expense-reports/${id}`,
    payload
  );
  return data;
};

export const submitTravelExpenseReport = async (
  id: string
): Promise<{ message: string }> => {
  const { data } = await apiClient.post<{ message: string }>(
    `/travel-expense-reports/${id}/submit`
  );
  return data;
};

export const uploadExpenseReportReceipt = async (
  reportId: string,
  file: File
): Promise<{ message: string; receipt_id: string }> => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<{ message: string; receipt_id: string }>(
    `/travel-expense-reports/${reportId}/upload-receipt`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
};

export const uploadExpenseReportExchangeProof = async (
  reportId: string,
  receiptId: string,
  file: File
): Promise<{ message: string; receipt_id: string }> => {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<{ message: string; receipt_id: string }>(
    `/travel-expense-reports/${reportId}/receipts/${receiptId}/upload-exchange-proof`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
};

export const deleteExpenseReportReceipt = async (
  reportId: string,
  receiptId: string
): Promise<void> => {
  await apiClient.delete(
    `/travel-expense-reports/${reportId}/receipts/${receiptId}`
  );
};

export const deleteTravelExpenseReport = async (
  id: string
): Promise<void> => {
  await apiClient.delete(`/travel-expense-reports/${id}`);
};

export const fetchTravelExpenseReportChat = async (
  reportId: string
): Promise<TravelExpenseReportChatMessage[]> => {
  const { data } = await apiClient.get<TravelExpenseReportChatMessage[]>(
    `/travel-expense-reports/${reportId}/chat`
  );
  return data;
};

export const sendTravelExpenseReportChatMessage = async (
  reportId: string,
  message: string
): Promise<{ message: string }> => {
  const formData = new FormData();
  formData.append("message", message);

  const { data } = await apiClient.post<{ message: string }>(
    `/travel-expense-reports/${reportId}/chat`,
    formData
  );
  return data;
};

