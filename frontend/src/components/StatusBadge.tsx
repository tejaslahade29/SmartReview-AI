import { Badge, BadgeVariant } from "@/components/ui/Badge";

const DOCUMENT_STATUS_CONFIG: Record<string, { label: string; variant: BadgeVariant }> = {
  processed: { label: "Processed", variant: "success" },
  processing: { label: "Processing", variant: "info" },
  failed: { label: "Failed", variant: "danger" },
};

export function DocumentStatusBadge({ status }: { status: string }) {
  const config = DOCUMENT_STATUS_CONFIG[status] ?? { label: status, variant: "neutral" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

export function ReviewStatusBadge({ reviewStatus }: { reviewStatus: string | null }) {
  if (!reviewStatus) {
    return <Badge variant="neutral">Not Reviewed</Badge>;
  }
  if (reviewStatus === "completed") {
    return <Badge variant="success">Reviewed</Badge>;
  }
  return <Badge variant="info">{reviewStatus}</Badge>;
}
