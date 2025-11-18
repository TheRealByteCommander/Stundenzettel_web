import { useMutation } from "@tanstack/react-query";
import { changePassword, type ChangePasswordRequest } from "../../../services/api/auth";

export const useChangePasswordMutation = () => {
  return useMutation({
    mutationFn: (payload: ChangePasswordRequest) => changePassword(payload),
  });
};

