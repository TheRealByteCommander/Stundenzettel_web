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
  fetchTravelExpenses,
  rejectTravelExpense,
  updateTravelExpense,
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

