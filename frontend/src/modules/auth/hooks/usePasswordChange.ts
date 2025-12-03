import { useMutation } from "@tanstack/react-query";
import { changePassword } from "../../../services/api/auth";
import type { ChangePasswordRequest } from "../../../services/api/types";

export const useChangePasswordMutation = () => {
  return useMutation({
    mutationFn: (payload: ChangePasswordRequest) => changePassword(payload),
  });
};

