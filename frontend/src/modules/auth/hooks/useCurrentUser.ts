import { useQuery } from "@tanstack/react-query";
import { fetchCurrentUser } from "../../../services/api/auth";
import type { User } from "../../../services/api/types";
import { useAuthStore } from "../../../store/auth-store";

export const currentUserQueryKey = ["auth", "me"];

export const useCurrentUserQuery = () => {
  const token = useAuthStore((state) => state.token);

  return useQuery<User>({
    queryKey: currentUserQueryKey,
    queryFn: fetchCurrentUser,
    enabled: Boolean(token),
    staleTime: 1000 * 60 * 5,
  });
};

