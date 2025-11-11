import { useQuery } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { fetchAdminUsers } from "../../../services/api/users";
import type { AdminUserSummary } from "../../../services/api/types";

const adminUsersKey = ["admin-users"] as const;

export const useAdminUsersQuery = () =>
  useQuery<AdminUserSummary[], AxiosError>({
    queryKey: adminUsersKey,
    queryFn: fetchAdminUsers,
  });

