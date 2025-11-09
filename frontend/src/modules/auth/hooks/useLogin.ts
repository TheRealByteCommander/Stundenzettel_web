import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { login } from "../../../services/api/auth";
import type { LoginRequest, LoginResponse } from "../../../services/api/types";

export const useLoginMutation = () =>
  useMutation<LoginResponse, AxiosError, LoginRequest>({
    mutationFn: login,
  });

