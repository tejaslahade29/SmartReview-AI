import { Inbox } from "lucide-react";

export function EmptyState({
  title,
  description,
  icon,
  action,
}: {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-black/15 px-6 py-12 text-center dark:border-white/20">
      <div className="mb-1 flex h-10 w-10 items-center justify-center rounded-full bg-black/5 text-foreground/40 dark:bg-white/10">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <p className="text-sm font-medium">{title}</p>
      {description && <p className="max-w-sm text-sm text-foreground/60">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
