import { CheckCircle2, CircleDashed, Loader2, XCircle } from "lucide-react";
import { Badge, BadgeVariant } from "@/components/ui/Badge";

const DOCUMENT_STATUS_CONFIG: Record<
  string,
  { label: string; variant: BadgeVariant; icon: React.ReactNode }
> = {
  processed: { label: "Processed", variant: "success", icon: <CheckCircle2 className="h-3 w-3" /> },
  processing: { label: "Processing", variant: "info", icon: <Loader2 className="h-3 w-3 animate-spin" /> },
  failed: { label: "Failed", variant: "danger", icon: <XCircle className="h-3 w-3" /> },
};

export function DocumentStatusBadge({ status }: { status: string }) {
  const config = DOCUMENT_STATUS_CONFIG[status] ?? {
    label: status,
    variant: "neutral" as const,
    icon: undefined,
  };
  return (
    <Badge variant={config.variant} icon={config.icon}>
      {config.label}
    </Badge>
  );
}

export function ReviewStatusBadge({ reviewStatus }: { reviewStatus: string | null }) {
  if (!reviewStatus) {
    return (
      <Badge variant="neutral" icon={<CircleDashed className="h-3 w-3" />}>
        Not Reviewed
      </Badge>
    );
  }
  if (reviewStatus === "completed") {
    return (
      <Badge variant="success" icon={<CheckCircle2 className="h-3 w-3" />}>
        Reviewed
      </Badge>
    );
  }
  return <Badge variant="info">{reviewStatus}</Badge>;
}
