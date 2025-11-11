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
  approveTravelExpenseReport,
  rejectTravelExpenseReport,
  submitTravelExpenseReport,
  updateTravelExpenseReport,
  uploadExpenseReportReceipt,
  uploadExpenseReportExchangeProof,
  deleteExpenseReportReceipt,
  sendTravelExpenseReportChatMessage,
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

export const useApproveExpenseReportMutation = () => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, string>({
    mutationFn: approveTravelExpenseReport,
    onSuccess: (_, reportId) => {
      client.invalidateQueries({ queryKey: travelExpenseReportsKey() });
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

export const useRejectExpenseReportMutation = () => {
  const client = useQueryClient();
  return useMutation<
    { message: string },
    AxiosError,
    { id: string; reason?: string }
  >({
    mutationFn: ({ id, reason }) => rejectTravelExpenseReport(id, reason),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: travelExpenseReportsKey() });
      client.invalidateQueries({
        queryKey: travelExpenseReportKey(variables.id),
      });
    },
  });
};

export const useUploadExpenseReportReceiptMutation = (reportId: string) => {
  const client = useQueryClient();
  return useMutation<
    { message: string; receipt_id: string },
    AxiosError,
    File
  >({
    mutationFn: (file) => uploadExpenseReportReceipt(reportId, file),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

export const useUploadExchangeProofMutation = (reportId: string) => {
  const client = useQueryClient();
  return useMutation<
    { message: string; receipt_id: string },
    AxiosError,
    { receiptId: string; file: File }
  >({
    mutationFn: ({ receiptId, file }) =>
      uploadExpenseReportExchangeProof(reportId, receiptId, file),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

export const useDeleteExpenseReceiptMutation = (reportId: string) => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: (receiptId) =>
      deleteExpenseReportReceipt(reportId, receiptId),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

export const useSendExpenseReportChatMutation = (reportId: string) => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, string>({
    mutationFn: (message) =>
      sendTravelExpenseReportChatMessage(reportId, message),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: travelExpenseReportKey(reportId) });
    },
  });
};

