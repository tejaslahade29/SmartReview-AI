import { ButtonHTMLAttributes } from "react";

const VARIANT_CLASSES = {
  primary:
    "bg-foreground text-background hover:bg-foreground/90 disabled:bg-foreground/40",
  secondary:
    "border border-black/15 text-foreground hover:bg-black/5 dark:border-white/20 dark:hover:bg-white/10 disabled:opacity-50",
  ghost: "text-foreground/80 hover:bg-black/5 dark:hover:bg-white/10 disabled:opacity-50",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-600/40",
} as const;

type ButtonVariant = keyof typeof VARIANT_CLASSES;

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
}

export function Button({
  children,
  variant = "primary",
  isLoading = false,
  disabled,
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    >
      {isLoading && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
}
