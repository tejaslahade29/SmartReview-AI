const VARIANT_CLASSES = {
  neutral: "bg-black/5 text-foreground/70 dark:bg-white/10",
  info: "bg-blue-500/10 text-blue-700 dark:text-blue-400",
  success: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
  warning: "bg-amber-500/10 text-amber-700 dark:text-amber-400",
  orange: "bg-orange-500/10 text-orange-700 dark:text-orange-400",
  danger: "bg-red-500/10 text-red-700 dark:text-red-400",
} as const;

export type BadgeVariant = keyof typeof VARIANT_CLASSES;

export function Badge({
  children,
  variant = "neutral",
  className = "",
}: {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
