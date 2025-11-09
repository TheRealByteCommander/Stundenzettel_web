import { apiClient } from "./client";
import type {
  ChangePasswordRequest,
  LoginRequest,
  LoginResponse,
  OtpVerifyRequest,
  TwoFaQrResponse,
  TwoFaSetupResponse,
  User,
} from "./types";

export const login = async (payload: LoginRequest): Promise<LoginResponse> => {
  const { data } = await apiClient.post<LoginResponse>("/auth/login", payload);
  return data;
};

export const fetchCurrentUser = async (): Promise<User> => {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
};

export const verifyOtp = async (payload: OtpVerifyRequest) => {
  const { data } = await apiClient.post<TwoFaSetupResponse>(
    "/auth/2fa/verify",
    payload
  );
  return data;
};

export const completeInitialTwoFaSetup = async (payload: OtpVerifyRequest) => {
  const { data } = await apiClient.post<TwoFaSetupResponse>(
    "/auth/2fa/initial-setup",
    payload
  );
  return data;
};

export const fetchTwoFaSetupQr = async (setupToken: string) => {
  const { data } = await apiClient.get<TwoFaQrResponse>("/auth/2fa/setup-qr", {
    params: { setup_token: setupToken },
  });
  return data;
};

export const changePassword = async (payload: ChangePasswordRequest) => {
  await apiClient.post("/auth/change-password", payload);
};

