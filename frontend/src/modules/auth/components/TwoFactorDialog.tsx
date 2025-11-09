import * as Dialog from "@radix-ui/react-dialog";
import { useState } from "react";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { cn } from "../../../lib/utils";

interface BaseProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isLoading?: boolean;
  errorMessage?: string | null;
}

interface VerifyDialogProps extends BaseProps {
  title?: string;
  description?: string;
  onSubmit: (code: string) => void;
  submitLabel?: string;
}

export const TwoFactorDialog = ({
  open,
  onOpenChange,
  isLoading,
  errorMessage,
  onSubmit,
  title = "2FA-Verifizierung",
  description = "Bitte geben Sie den 6-stelligen Code aus Ihrer Authenticator-App ein.",
  submitLabel = "Bestätigen",
}: VerifyDialogProps) => {
  const [otp, setOtp] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (otp.length === 6) {
      onSubmit(otp);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40" />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 w-[95vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-6 shadow-xl focus:outline-none"
          )}
        >
          <Dialog.Title className="text-lg font-semibold text-brand-gray">
            {title}
          </Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-gray-600">
            {description}
          </Dialog.Description>

          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="otp-input">2FA-Code</Label>
              <Input
                id="otp-input"
                autoFocus
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="000000"
                value={otp}
                onChange={(event) =>
                  setOtp(event.target.value.replace(/[^0-9]/g, ""))
                }
              />
            </div>
            {errorMessage && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {errorMessage}
              </div>
            )}
            <div className="flex items-center justify-end gap-2">
              <Dialog.Close asChild>
                <Button type="button" variant="outline">
                  Abbrechen
                </Button>
              </Dialog.Close>
              <Button
                type="submit"
                disabled={otp.length !== 6 || isLoading}
                variant="primary"
              >
                {isLoading ? "Bitte warten..." : submitLabel}
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

