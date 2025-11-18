import { apiClient } from "./client";

export interface SMTPConfig {
  id?: string;
  smtp_server: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  admin_email: string;
  updated_at?: string;
}

export interface SMTPConfigCreate {
  smtp_server: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  admin_email: string;
}

export interface AccountingMonthlyStat {
  user_id: string;
  user_name: string;
  month: string;
  total_hours: number;
  hours_on_timesheets: number;
  travel_hours: number;
  travel_hours_on_timesheets: number;
  travel_kilometers: number;
  travel_expenses: number;
  timesheets_count: number;
}

export const fetchSMTPConfig = async (): Promise<SMTPConfig | null> => {
  try {
    const { data } = await apiClient.get<SMTPConfig>("/admin/smtp-config");
    return data;
  } catch (error) {
    return null;
  }
};

export const updateSMTPConfig = async (
  payload: SMTPConfigCreate
): Promise<void> => {
  await apiClient.post("/admin/smtp-config", payload);
};

export const fetchAccountingMonthlyStats = async (
  month: string
): Promise<AccountingMonthlyStat[]> => {
  const { data } = await apiClient.get<AccountingMonthlyStat[]>(
    "/accounting/monthly-stats",
    {
      params: { month },
    }
  );
  return data;
};

export const downloadAccountingMonthlyReportPDF = async (
  month: string
): Promise<Blob> => {
  const { data } = await apiClient.get(`/accounting/monthly-report-pdf`, {
    params: { month },
    responseType: "blob",
  });
  return data;
};

