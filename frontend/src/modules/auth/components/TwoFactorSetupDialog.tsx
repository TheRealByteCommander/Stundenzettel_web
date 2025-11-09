import * as Dialog from "@radix-ui/react-dialog";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Label } from "../../../components/ui/label";
import { cn } from "../../../lib/utils";
import { useState } from "react";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  qrUri: string | null;
  onSubmit: (code: string) => void;
  isLoading?: boolean;
  errorMessage?: string | null;
}

export const TwoFactorSetupDialog = ({
  open,
  onOpenChange,
  qrUri,
  onSubmit,
  isLoading,
  errorMessage,
}: Props) => {
  const [code, setCode] = useState("");

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (code.length === 6) {
      onSubmit(code);
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/40" />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 w-[95vw] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl bg-white p-6 shadow-xl focus:outline-none"
          )}
        >
          <Dialog.Title className="text-lg font-semibold text-brand-gray">
            2FA Einrichtung erforderlich
          </Dialog.Title>
          <Dialog.Description className="mt-1 text-sm text-gray-600">
            Scannen Sie den QR-Code mit Google Authenticator und geben Sie den
            sechsstelligen Code ein.
          </Dialog.Description>

          <div className="mt-4 space-y-4">
            {qrUri ? (
              <div className="flex justify-center">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(
                    qrUri
                  )}`}
                  alt="2FA QR-Code"
                  className="rounded-lg border border-gray-200 shadow-sm"
                />
              </div>
            ) : (
              <div className="rounded-md border border-yellow-200 bg-yellow-50 px-3 py-2 text-sm text-yellow-900">
                QR-Code wird geladen…
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="setup-otp">Authenticator-Code</Label>
                <Input
                  id="setup-otp"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  placeholder="000000"
                  value={code}
                  onChange={(event) =>
                    setCode(event.target.value.replace(/[^0-9]/g, ""))
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
                  disabled={code.length !== 6 || isLoading}
                >
                  {isLoading ? "Aktiviere..." : "2FA aktivieren"}
                </Button>
              </div>
            </form>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

