import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  approveTimesheet,
  fetchAccountingTimesheets,
  rejectTimesheet,
  updateTimesheet,
  type AccountingTimesheetParams,
} from "../../../services/api/timesheets";
import type { WeeklyTimesheet } from "../../../services/api/types";

export const accountingTimesheetsKey = (params: AccountingTimesheetParams) => [
  "timesheets",
  "accounting",
  params.month ?? "all",
  params.userId ?? "all",
];

export const useAccountingTimesheetsQuery = (
  params: AccountingTimesheetParams
) =>
  useQuery<WeeklyTimesheet[], AxiosError>({
    queryKey: accountingTimesheetsKey(params),
    queryFn: () => fetchAccountingTimesheets(params),
  });

export const useAccountingApproveMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, { id: string; params: AccountingTimesheetParams }>({
    mutationFn: ({ id }) => approveTimesheet(id),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: accountingTimesheetsKey(variables.params) });
      client.invalidateQueries({ queryKey: ["timesheets"] });
    },
  });
};

export const useAccountingRejectMutation = () => {
  const client = useQueryClient();
  return useMutation<void, AxiosError, { id: string; params: AccountingTimesheetParams }>({
    mutationFn: ({ id }) => rejectTimesheet(id),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: accountingTimesheetsKey(variables.params) });
      client.invalidateQueries({ queryKey: ["timesheets"] });
    },
  });
};

export const useAccountingUpdateVerificationMutation = () => {
  const client = useQueryClient();
  return useMutation<
    WeeklyTimesheet,
    AxiosError,
    {
      id: string;
      params: AccountingTimesheetParams;
      notes: string;
      verified: boolean;
    }
  >({
    mutationFn: ({ id, notes, verified }) =>
      updateTimesheet(id, {
        signed_pdf_verification_notes: notes,
        signed_pdf_verified: verified,
      }),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: accountingTimesheetsKey(variables.params) });
      client.invalidateQueries({ queryKey: ["timesheets"] });
    },
  });
};

