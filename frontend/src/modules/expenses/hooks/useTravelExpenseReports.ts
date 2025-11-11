import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  fetchAvailableExpenseReportMonths,
  fetchTravelExpenseReport,
  fetchTravelExpenseReports,
  initializeTravelExpenseReport,
  submitTravelExpenseReport,
  updateTravelExpenseReport,
  type TravelExpenseReportListParams,
} from "../../../services/api/travel-expense-reports";
import type {
  ExpenseReportMonthOption,
  TravelExpenseReport,
  TravelExpenseReportUpdate,
} from "../../../services/api/types";

export const travelExpenseReportsKey = (
  params: TravelExpenseReportListParams = {}
) => ["travel-expense-reports", params] as const;

export const travelExpenseReportKey = (id: string | undefined) =>
  ["travel-expense-report", id] as const;

export const expenseReportMonthsKey = ["travel-expense-report-months"] as const;

export const useTravelExpenseReportsQuery = (
  params: TravelExpenseReportListParams = {}
) =>
  useQuery<TravelExpenseReport[], AxiosError>({
    queryKey: travelExpenseReportsKey(params),
    queryFn: () => fetchTravelExpenseReports(params),
  });

export const useTravelExpenseReportQuery = (id: string | undefined) =>
  useQuery<TravelExpenseReport, AxiosError>({
    queryKey: travelExpenseReportKey(id ?? ""),
    queryFn: () => fetchTravelExpenseReport(id ?? ""),
    enabled: Boolean(id),
  });

export const useExpenseReportMonthsQuery = () =>
  useQuery<ExpenseReportMonthOption[], AxiosError>({
    queryKey: expenseReportMonthsKey,
    queryFn: fetchAvailableExpenseReportMonths,
  });

export const useInitializeExpenseReportMutation = () => {
  const client = useQueryClient();
  return useMutation<TravelExpenseReport, AxiosError, string>({
    mutationFn: initializeTravelExpenseReport,
    onSuccess: (report) => {
      client.invalidateQueries({ queryKey: travelExpenseReportsKey() });
      client.invalidateQueries({ queryKey: travelExpenseReportKey(report.id) });
    },
  });
};

export const useUpdateExpenseReportMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<TravelExpenseReport, AxiosError, TravelExpenseReportUpdate>({
    mutationFn: (payload) => updateTravelExpenseReport(id, payload),
    onSuccess: (report) => {
      client.invalidateQueries({ queryKey: travelExpenseReportsKey() });
      client.invalidateQueries({ queryKey: travelExpenseReportKey(report.id) });
    },
  });
};

export const useSubmitExpenseReportMutation = () => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, string>({
    mutationFn: submitTravelExpenseReport,
    onSuccess: (_, reportId) => {
      client.invalidateQueries({ queryKey: travelExpenseReportsKey() });
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

