import { cn } from "../../lib/utils";

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "destructive" | "success";
}

export const Alert = ({
  className,
  variant = "default",
  ...props
}: AlertProps) => {
  const variants: Record<NonNullable<AlertProps["variant"]>, string> = {
    default: "border-blue-200 bg-blue-50 text-blue-900",
    destructive: "border-red-200 bg-red-50 text-red-900",
    success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  };

  return (
    <div
      role="alert"
      className={cn(
        "rounded-lg border px-4 py-3 text-sm leading-6",
        variants[variant],
        className
      )}
      {...props}
    />
  );
};

