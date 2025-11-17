import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  createUser,
  deleteUser,
  fetchAdminUsers,
  updateUser,
} from "../../../services/api/users";
import type {
  AdminUserSummary,
  UserCreateRequest,
  UserUpdateRequest,
} from "../../../services/api/types";

const adminUsersKey = ["admin-users"] as const;

export const useAdminUsersQuery = () =>
  useQuery<AdminUserSummary[], AxiosError>({
    queryKey: adminUsersKey,
    queryFn: fetchAdminUsers,
  });

export const useCreateUserMutation = () => {
  const client = useQueryClient();
  return useMutation<
    { message: string; user_id: string },
    AxiosError,
    UserCreateRequest
  >({
    mutationFn: createUser,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: adminUsersKey });
    },
  });
};

export const useUpdateUserMutation = (userId: string) => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, UserUpdateRequest>({
    mutationFn: (payload) => updateUser(userId, payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: adminUsersKey });
    },
  });
};

export const useDeleteUserMutation = () => {
  const client = useQueryClient();
  return useMutation<{ message: string }, AxiosError, string>({
    mutationFn: deleteUser,
    onSuccess: () => {
      client.invalidateQueries({ queryKey: adminUsersKey });
    },
  });
};

