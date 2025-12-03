import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
  "disabled:pointer-events-none disabled:opacity-50",
  "touch-manipulation", // Optimiert für Touch
  "min-h-[44px] sm:min-h-[40px]", // Mindestgröße für Touch (iOS: 44px)
  {
    variants: {
      variant: {
        primary:
          "bg-brand-primary text-white hover:bg-brand-primary/90 focus-visible:ring-brand-primary",
        secondary:
          "bg-white text-brand-gray border border-gray-200 hover:bg-gray-100 focus-visible:ring-brand-primary",
        outline:
          "border border-gray-300 bg-transparent text-brand-gray hover:bg-gray-50 focus-visible:ring-brand-primary",
        ghost:
          "bg-transparent text-brand-gray hover:bg-gray-100 focus-visible:ring-brand-primary",
        destructive:
          "bg-red-500 text-white hover:bg-red-600 focus-visible:ring-red-500",
      },
      size: {
        sm: "h-11 px-3 sm:h-9", // Mobile: min 44px
        md: "h-11 px-4 sm:h-10", // Mobile: min 44px
        lg: "h-12 px-6 text-base sm:h-11", // Mobile: min 44px
        icon: "h-11 w-11 sm:h-10 sm:w-10", // Mobile: min 44px
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        aria-label={props["aria-label"] || (typeof props.children === "string" ? props.children : undefined)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

