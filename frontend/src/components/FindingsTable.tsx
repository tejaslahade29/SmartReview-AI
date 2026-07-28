import { motion } from "framer-motion";
import { ChevronRight } from "lucide-react";

import { ReviewFinding } from "@/lib/api/reviews";
import { SeverityBadge } from "@/components/SeverityBadge";
import { formatPercent } from "@/lib/format";

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

// Mirrors backend/app/services/severity_styles.py — keep in sync.
const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-l-red-500",
  high: "border-l-orange-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

export function FindingsTable({
  findings,
  onSelect,
}: {
  findings: ReviewFinding[];
  onSelect: (finding: ReviewFinding) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-black/10 text-left text-xs text-foreground/60 dark:border-white/10">
            <th className="py-2 pr-4 font-medium">Severity</th>
            <th className="py-2 pr-4 font-medium">Issue Type</th>
            <th className="py-2 pr-4 font-medium">Explanation</th>
            <th className="py-2 pr-4 font-medium">Confidence</th>
            <th className="py-2 pr-4 font-medium">Paragraph</th>
            <th className="py-2 pr-0" />
          </tr>
        </thead>
        <tbody className="divide-y divide-black/5 dark:divide-white/5">
          {findings.map((finding, index) => (
            <motion.tr
              key={finding.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.2, delay: Math.min(index * 0.04, 0.3) }}
              onClick={() => onSelect(finding)}
              className={`cursor-pointer border-l-2 ${
                SEVERITY_BORDER[finding.severity] ?? "border-l-transparent"
              } hover:bg-black/5 dark:hover:bg-white/5`}
            >
              <td className="py-3 pr-4 pl-2">
                <SeverityBadge severity={finding.severity} />
              </td>
              <td className="py-3 pr-4 font-medium capitalize">
                {finding.issue_type.replaceAll("_", " ")}
              </td>
              <td className="max-w-md py-3 pr-4 text-foreground/70">
                {truncate(finding.explanation, 90)}
              </td>
              <td className="py-3 pr-4 text-foreground/70">{formatPercent(finding.confidence)}</td>
              <td className="py-3 pr-4 font-mono text-xs text-foreground/50">
                {finding.paragraph_id.slice(0, 8)}…
              </td>
              <td className="py-3 pr-2 text-foreground/30">
                <ChevronRight className="h-4 w-4" />
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
