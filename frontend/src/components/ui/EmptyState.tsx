export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-black/15 px-6 py-12 text-center dark:border-white/20">
      <p className="text-sm font-medium">{title}</p>
      {description && <p className="max-w-sm text-sm text-foreground/60">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
