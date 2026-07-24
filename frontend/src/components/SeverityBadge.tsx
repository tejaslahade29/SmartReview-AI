import { Badge, BadgeVariant } from "@/components/ui/Badge";

// Mirrors backend/app/services/severity_styles.py — keep in sync.
const SEVERITY_CONFIG: Record<string, { label: string; variant: BadgeVariant }> = {
  critical: { label: "Critical", variant: "danger" },
  high: { label: "High", variant: "orange" },
  medium: { label: "Medium", variant: "warning" },
  low: { label: "Low", variant: "info" },
};

export function SeverityBadge({ severity }: { severity: string }) {
  const config = SEVERITY_CONFIG[severity] ?? { label: severity, variant: "neutral" as const };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
