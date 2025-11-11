import { apiClient } from "./client";
import type {
  TravelExpense,
  TravelExpenseCreate,
  TravelExpenseUpdate,
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

