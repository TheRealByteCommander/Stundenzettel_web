import { useQuery } from "@tanstack/react-query";
import { fetchAuditLogs, type AuditLogFilters } from "../../../services/api/audit";

export const useAuditLogsQuery = (filters?: AuditLogFilters) => {
  return useQuery({
    queryKey: ["audit-logs", filters],
    queryFn: () => fetchAuditLogs(filters),
  });
};

