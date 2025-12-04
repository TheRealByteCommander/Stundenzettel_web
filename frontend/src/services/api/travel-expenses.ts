import { apiClient } from "./client";
import type {
  TravelExpense,
  TravelExpenseCreate,
  TravelExpenseUpdate,
  TravelExpenseReceipt,
} from "./types";

export const fetchTravelExpenses = async (): Promise<TravelExpense[]> => {
  const { data } = await apiClient.get<TravelExpense[]>("/travel-expenses");
  return data;
};

export const createTravelExpense = async (
  payload: TravelExpenseCreate
): Promise<TravelExpense> => {
  const { data } = await apiClient.post<TravelExpense>(
    "/travel-expenses",
    payload
  );
  return data;
};

export const updateTravelExpense = async (
  id: string,
  payload: TravelExpenseUpdate
): Promise<TravelExpense> => {
  const { data } = await apiClient.put<TravelExpense>(
    `/travel-expenses/${id}`,
    payload
  );
  return data;
};

export const deleteTravelExpense = async (id: string): Promise<void> => {
  await apiClient.delete(`/travel-expenses/${id}`);
};

export const approveTravelExpense = async (id: string): Promise<void> => {
  await apiClient.post(`/travel-expenses/${id}/approve`);
};

export const rejectTravelExpense = async (id: string): Promise<void> => {
  await apiClient.post(`/travel-expenses/${id}/reject`);
};

export const uploadTravelExpenseReceipt = async (
  expenseId: string,
  file: File
): Promise<{ message: string; receipt: TravelExpenseReceipt }> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<{ message: string; receipt: TravelExpenseReceipt }>(
    `/travel-expenses/${expenseId}/upload-receipt`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return data;
};

export const deleteTravelExpenseReceipt = async (
  expenseId: string,
  receiptId: string
): Promise<{ message: string }> => {
  const { data } = await apiClient.delete<{ message: string }>(
    `/travel-expenses/${expenseId}/receipts/${receiptId}`
  );
  return data;
};

