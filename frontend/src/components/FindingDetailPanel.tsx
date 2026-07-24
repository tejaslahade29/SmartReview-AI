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
          <blockquote className="rounded-md border-l-2 border-foreground/30 bg-black/5 px-3 py-2 text-foreground/80 dark:bg-white/5">
            {finding.suggested_text}
          </blockquote>
        </Field>
      )}

      <Field label="Confidence">{formatPercent(finding.confidence)}</Field>

      <Field label="Paragraph ID">
        <code className="rounded bg-black/5 px-1.5 py-0.5 text-xs dark:bg-white/10">
          {finding.paragraph_id}
        </code>
      </Field>
    </div>
  );
}
