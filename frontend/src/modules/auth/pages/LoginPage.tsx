import { zodResolver } from "@hookform/resolvers/zod";
import type { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { Alert } from "../../../components/ui/alert";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardTitle } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { useLoginMutation } from "../hooks/useLogin";
import {
  useFetchSetupQr,
  useInitialSetupMutation,
  useVerifyOtpMutation,
} from "../hooks/useTwoFactor";
import { useAuthStore } from "../../../store/auth-store";
import { TwoFactorDialog } from "../components/TwoFactorDialog";
import { TwoFactorSetupDialog } from "../components/TwoFactorSetupDialog";
import type { LoginResponse } from "../../../services/api/types";

const loginSchema = z.object({
  email: z
    .string()
    .min(1, "E-Mail ist erforderlich.")
    .email("Bitte geben Sie eine gültige E-Mail-Adresse ein."),
  password: z
    .string()
    .min(1, "Passwort ist erforderlich.")
    .min(8, "Passwort muss mindestens 8 Zeichen lang sein."),
});

type LoginSchema = z.infer<typeof loginSchema>;

export const LoginPage = () => {
  const defaultAdminEmail =
    import.meta.env.VITE_DEFAULT_ADMIN_EMAIL ?? "admin@schmitz-intralogistik.de";
  const defaultAdminPassword =
    import.meta.env.VITE_DEFAULT_ADMIN_PASSWORD ?? "admin123";
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [twoFaError, setTwoFaError] = useState<string | null>(null);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [showTwoFaDialog, setShowTwoFaDialog] = useState(false);
  const [showSetupDialog, setShowSetupDialog] = useState(false);

  const {
    token,
    setSession,
    setTempToken,
    setSetupToken,
    tempToken,
    setupToken,
    qrUri,
    clearSession,
  } = useAuthStore((state) => ({
    token: state.token,
    setSession: state.setSession,
    setTempToken: state.setTempToken,
    setSetupToken: state.setSetupToken,
    tempToken: state.tempToken,
    setupToken: state.setupToken,
    qrUri: state.qrUri,
    clearSession: state.clearSession,
  }));

  const loginMutation = useLoginMutation();
  const verifyMutation = useVerifyOtpMutation();
  const setupMutation = useInitialSetupMutation();
  const setupQrMutation = useFetchSetupQr();

  const form = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
    mode: "onSubmit",
  });

  useEffect(() => {
    if (token) {
      navigate("/app");
    }
  }, [token, navigate]);

  const handleLoginSuccess = (response: LoginResponse) => {
    if ("access_token" in response) {
      setSession(response.access_token, response.user);
      setErrorMessage(null);
      navigate("/app");
      return;
    }

    if ("requires_2fa" in response) {
      setTempToken(response.temp_token);
      setShowTwoFaDialog(true);
      return;
    }

    if ("requires_2fa_setup" in response) {
      const newSetupToken = response.setup_token;
      setSetupToken({ setupToken: newSetupToken, qrUri: null });
      setShowSetupDialog(true);
      setTempToken(null);
      setupQrMutation.mutate(newSetupToken, {
        onSuccess: (data) => {
          setSetupToken({ setupToken: newSetupToken, qrUri: data.otpauth_uri });
        },
        onError: (error) => {
          const axiosError = error as AxiosError<{ detail?: string }>;
          setSetupError(
            axiosError.response?.data?.detail ??
              "QR-Code konnte nicht geladen werden."
          );
        },
      });
    }
  };

  const onSubmit = async (values: LoginSchema) => {
    setErrorMessage(null);
    clearSession();
    try {
      const response = await loginMutation.mutateAsync(values);
      handleLoginSuccess(response);
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const detail =
        axiosError.response?.data?.detail ??
        axiosError.message ??
        "Anmeldung fehlgeschlagen.";
      setErrorMessage(detail);
    }
  };

  const handleVerifyOtp = async (code: string) => {
    if (!tempToken) {
      setTwoFaError("Kein gültiger 2FA-Token vorhanden. Bitte erneut anmelden.");
      return;
    }
    setTwoFaError(null);
    try {
      const response = await verifyMutation.mutateAsync({
        otp: code,
        temp_token: tempToken,
      });
      setSession(response.access_token, response.user);
      setShowTwoFaDialog(false);
      navigate("/app");
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ??
        axiosError.message ??
        "Der eingegebene Code ist ungültig.";
      setTwoFaError(message);
    }
  };

  const handleSetupOtp = async (code: string) => {
    if (!setupToken) {
      setSetupError(
        "Es ist kein Setup-Token vorhanden. Bitte erneut anmelden."
      );
      return;
    }
    setSetupError(null);
    try {
      const response = await setupMutation.mutateAsync({
        otp: code,
        temp_token: setupToken,
      });
      setSession(response.access_token, response.user);
      setShowSetupDialog(false);
      navigate("/app");
    } catch (error) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      const message =
        axiosError.response?.data?.detail ??
        axiosError.message ??
        "Der eingegebene Code konnte nicht verifiziert werden.";
      setSetupError(message);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 px-4">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-6 py-8">
          <div className="text-center">
            <CardTitle className="text-2xl font-semibold">
              Tick Guard – Zeiterfassung
            </CardTitle>
            <p className="mt-2 text-sm text-gray-600">
              Melden Sie sich mit Ihren Zugangsdaten an. 2FA ist verpflichtend.
            </p>
          </div>

          {errorMessage && (
            <Alert variant="destructive">{errorMessage}</Alert>
          )}

          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-4"
            autoComplete="off"
          >
            <div className="space-y-2">
              <Label htmlFor="email">E-Mail</Label>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                placeholder="name@firma.de"
                {...form.register("email")}
              />
              {form.formState.errors.email && (
                <p className="text-sm text-red-500">
                  {form.formState.errors.email.message}
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Passwort</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                placeholder="••••••••"
                {...form.register("password")}
              />
              {form.formState.errors.password && (
                <p className="text-sm text-red-500">
                  {form.formState.errors.password.message}
                </p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Anmeldung..." : "Anmelden"}
            </Button>
          </form>

          <div className="rounded-md bg-gray-100 px-4 py-3 text-xs text-gray-600">
            <p className="font-medium text-brand-gray">Standard Admin</p>
            <p>
              {defaultAdminEmail} / {defaultAdminPassword}
            </p>
          </div>
        </CardContent>
      </Card>

      <TwoFactorDialog
        open={showTwoFaDialog}
        onOpenChange={setShowTwoFaDialog}
        isLoading={verifyMutation.isPending}
        errorMessage={twoFaError}
        onSubmit={handleVerifyOtp}
      />

      <TwoFactorSetupDialog
        open={showSetupDialog}
        onOpenChange={setShowSetupDialog}
        qrUri={qrUri}
        errorMessage={setupError}
        isLoading={setupMutation.isPending}
        onSubmit={handleSetupOtp}
      />
    </div>
  );
};

