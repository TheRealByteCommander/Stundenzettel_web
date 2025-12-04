import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  approveTravelExpense,
  createTravelExpense,
  deleteTravelExpense,
  deleteTravelExpenseReceipt,
  fetchTravelExpenses,
  rejectTravelExpense,
  updateTravelExpense,
  uploadTravelExpenseReceipt,
} from "../../../services/api/travel-expenses";
import type {
  TravelExpense,
  TravelExpenseCreate,
  TravelExpenseUpdate,
} from "../../../services/api/types";

export const travelExpensesQueryKey = ["travel-expenses"];

export const useTravelExpensesQuery = () =>
  useQuery<TravelExpense[], AxiosError>({
    queryKey: travelExpensesQueryKey,
    queryFn: fetchTravelExpenses,
  });

export const useCreateTravelExpenseMutation = () => {
  const client = useQueryClient();
  return useMutation<TravelExpense, AxiosError, TravelExpenseCreate>({
    mutationFn: createTravelExpense,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useUpdateTravelExpenseMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<TravelExpense, AxiosError, TravelExpenseUpdate>({
    mutationFn: (payload) => updateTravelExpense(id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useDeleteTravelExpenseMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: deleteTravelExpense,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useApproveTravelExpenseMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: approveTravelExpense,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useRejectTravelExpenseMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: rejectTravelExpense,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useUploadTravelExpenseReceiptMutation = (expenseId: string) => {
  const client = useQueryClient();
  return useMutation<
    { message: string; receipt: { id: string; filename: string; local_path: string; uploaded_at: string; file_size: number } },
    AxiosError,
    File
  >({
    mutationFn: (file) => uploadTravelExpenseReceipt(expenseId, file),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

export const useDeleteTravelExpenseReceiptMutation = (expenseId: string) => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, string>({
    mutationFn: (receiptId) => deleteTravelExpenseReceipt(expenseId, receiptId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpensesQueryKey });
    },
  });
};

