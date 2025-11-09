import { useMutation } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import {
  completeInitialTwoFaSetup,
  fetchTwoFaSetupQr,
  verifyOtp,
} from "../../../services/api/auth";
import type {
  OtpVerifyRequest,
  TwoFaQrResponse,
  TwoFaSetupResponse,
} from "../../../services/api/types";

export const useVerifyOtpMutation = () =>
  useMutation<TwoFaSetupResponse, AxiosError, OtpVerifyRequest>({
    mutationFn: verifyOtp,
  });

export const useInitialSetupMutation = () =>
  useMutation<TwoFaSetupResponse, AxiosError, OtpVerifyRequest>({
    mutationFn: completeInitialTwoFaSetup,
  });

export const useFetchSetupQr = () =>
  useMutation<TwoFaQrResponse, AxiosError, string>({
    mutationFn: fetchTwoFaSetupQr,
  });

