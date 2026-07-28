import { Quote } from "lucide-react";

import { ReviewFinding } from "@/lib/api/reviews";
import { SeverityBadge } from "@/components/SeverityBadge";
import { formatPercent } from "@/lib/format";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-foreground/50">{label}</p>
      <div className="mt-1 text-sm">{children}</div>
    </div>
  );
}

export function FindingDetailPanel({ finding }: { finding: ReviewFinding }) {
  return (
    <div className="flex flex-col gap-5">
      <Field label="Severity">
        <SeverityBadge severity={finding.severity} />
      </Field>

      <Field label="Issue Type">
        <span className="font-medium capitalize">{finding.issue_type.replaceAll("_", " ")}</span>
      </Field>

      <Field label="Explanation">
        <p className="text-foreground/80">{finding.explanation}</p>
      </Field>

      {finding.suggested_text && (
        <Field label="Suggested Replacement">
          <blockquote className="relative rounded-md border-l-2 border-foreground/30 bg-black/5 py-2 pl-8 pr-3 text-foreground/80 dark:bg-white/5">
            <Quote className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-foreground/30" />
            {finding.suggested_text}
          </blockquote>
        </Field>
      )}

      <Field label="Confidence">
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-32 overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
            <div
              className="h-full rounded-full bg-foreground"
              style={{ width: `${Math.round(finding.confidence * 100)}%` }}
            />
          </div>
          <span>{formatPercent(finding.confidence)}</span>
        </div>
      </Field>

      <Field label="Paragraph ID">
        <code className="rounded bg-black/5 px-1.5 py-0.5 text-xs dark:bg-white/10">
          {finding.paragraph_id}
        </code>
      </Field>
    </div>
  );
}
