import { Suspense, ReactNode } from "react";

interface LazySuspenseProps {
  children: ReactNode;
}

export const LazySuspense = ({ children }: LazySuspenseProps) => {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gray-100 text-brand-gray">
          Lade Seite…
        </div>
      }
    >
      {children}
    </Suspense>
  );
};

