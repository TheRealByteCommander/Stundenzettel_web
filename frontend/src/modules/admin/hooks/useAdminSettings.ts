import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchSMTPConfig,
  updateSMTPConfig,
  fetchAccountingMonthlyStats,
  downloadAccountingMonthlyReportPDF,
  type SMTPConfigCreate,
} from "../../../services/api/admin";

export const useSMTPConfigQuery = () => {
  return useQuery({
    queryKey: ["admin", "smtp-config"],
    queryFn: () => fetchSMTPConfig(),
  });
};

export const useUpdateSMTPConfigMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SMTPConfigCreate) => updateSMTPConfig(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "smtp-config"] });
    },
  });
};

export const useAccountingMonthlyStatsQuery = (month: string) => {
  return useQuery({
    queryKey: ["accounting", "monthly-stats", month],
    queryFn: () => fetchAccountingMonthlyStats(month),
    enabled: !!month,
  });
};

export const useDownloadAccountingReportMutation = () => {
  return useMutation({
    mutationFn: (month: string) => downloadAccountingMonthlyReportPDF(month),
  });
};

