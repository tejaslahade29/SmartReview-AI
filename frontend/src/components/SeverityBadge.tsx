import { AlertCircle, AlertOctagon, AlertTriangle, Info } from "lucide-react";
import { Badge, BadgeVariant } from "@/components/ui/Badge";

// Mirrors backend/app/services/severity_styles.py — keep in sync.
const SEVERITY_CONFIG: Record<string, { label: string; variant: BadgeVariant; icon: React.ReactNode }> = {
  critical: { label: "Critical", variant: "danger", icon: <AlertOctagon className="h-3 w-3" /> },
  high: { label: "High", variant: "orange", icon: <AlertTriangle className="h-3 w-3" /> },
  medium: { label: "Medium", variant: "warning", icon: <AlertCircle className="h-3 w-3" /> },
  low: { label: "Low", variant: "info", icon: <Info className="h-3 w-3" /> },
};

export function SeverityBadge({ severity }: { severity: string }) {
  const config = SEVERITY_CONFIG[severity] ?? {
    label: severity,
    variant: "neutral" as const,
    icon: undefined,
  };
  return (
    <Badge variant={config.variant} icon={config.icon}>
      {config.label}
    </Badge>
  );
}
