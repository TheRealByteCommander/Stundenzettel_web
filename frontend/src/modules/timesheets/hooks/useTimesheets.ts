import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  approveTimesheet,
  createTimesheet,
  deleteTimesheet,
  fetchTimesheetById,
  fetchTimesheets,
  rejectTimesheet,
  sendTimesheetEmail,
  updateTimesheet,
  uploadSignedTimesheet,
} from "../../../services/api/timesheets";
import type {
  CreateTimesheetRequest,
  UpdateTimesheetRequest,
  WeeklyTimesheet,
} from "../../../services/api/types";

export const timesheetsQueryKey = ["timesheets"];

export const useTimesheetsQuery = () =>
  useQuery<WeeklyTimesheet[], AxiosError>({
    queryKey: timesheetsQueryKey,
    queryFn: fetchTimesheets,
  });

export const useTimesheetQuery = (id: string | undefined) =>
  useQuery<WeeklyTimesheet, AxiosError>({
    queryKey: [...timesheetsQueryKey, id],
    queryFn: () => fetchTimesheetById(id!),
    enabled: Boolean(id),
  });

export const useCreateTimesheetMutation = () => {
  const client = useQueryClient();
  return useMutation<
    WeeklyTimesheet,
    AxiosError,
    CreateTimesheetRequest
  >({
    mutationFn: createTimesheet,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
    },
  });
};

export const useUpdateTimesheetMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<
    WeeklyTimesheet,
    AxiosError,
    UpdateTimesheetRequest
  >({
    mutationFn: (payload) => updateTimesheet(id, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
      client.invalidateQueries({ queryKey: [...timesheetsQueryKey, id] });
    },
  });
};

export const useDeleteTimesheetMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, string>({
    mutationFn: deleteTimesheet,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
    },
  });
};

export const useSendTimesheetEmailMutation = (id: string) =>
  useMutation<void, AxiosError>({
    mutationFn: () => sendTimesheetEmail(id),
  });

export const useApproveTimesheetMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<void, AxiosError>({
    mutationFn: () => approveTimesheet(id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
      client.invalidateQueries({ queryKey: [...timesheetsQueryKey, id] });
    },
  });
};

export const useRejectTimesheetMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<void, AxiosError>({
    mutationFn: () => rejectTimesheet(id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
      client.invalidateQueries({ queryKey: [...timesheetsQueryKey, id] });
    },
  });
};

export const useUploadSignedTimesheetMutation = (id: string) => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, File>({
    mutationFn: (file) => uploadSignedTimesheet(id, file),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: timesheetsQueryKey });
      client.invalidateQueries({ queryKey: [...timesheetsQueryKey, id] });
    },
  });
};

