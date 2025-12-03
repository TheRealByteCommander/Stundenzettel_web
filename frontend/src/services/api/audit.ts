import { apiClient } from "./client";

export interface AuditLog {
  timestamp: string;
  action: string;
  user_id: string;
  resource_type: string;
  resource_id: string;
  details?: Record<string, unknown>;
}

export interface AuditLogsResponse {
  logs: AuditLog[];
  count: number;
}

export interface AuditLogFilters {
  limit?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
}

export const fetchAuditLogs = async (
  filters?: AuditLogFilters
): Promise<AuditLogsResponse> => {
  const { data } = await apiClient.get<AuditLogsResponse>("/admin/audit-logs", {
    params: filters,
  });
  return data;
};

