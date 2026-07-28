"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download,
  FileOutput,
  FileSearch,
  FileX,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { fetchDocument } from "@/lib/api/documents";
import { fetchReviewsForDocument, startReview, ReviewFinding } from "@/lib/api/reviews";
import {
  fetchReviewedDocumentsForDocument,
  generateReviewedDocument,
  downloadReviewedDocument,
} from "@/lib/api/reviewedDocuments";
import { getErrorMessage } from "@/lib/api/errors";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SkeletonRows, Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { SidePanel } from "@/components/ui/SidePanel";
import { DocumentStatusBadge, ReviewStatusBadge } from "@/components/StatusBadge";
import { FindingsTable } from "@/components/FindingsTable";
import { FindingDetailPanel } from "@/components/FindingDetailPanel";
import { formatBytes, formatDate } from "@/lib/format";

const fadeUp = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
};

export function DocumentDetailClient({ documentId }: { documentId: string }) {
  const queryClient = useQueryClient();
  const [selectedFinding, setSelectedFinding] = useState<ReviewFinding | null>(null);
  const [confirmGenerateOpen, setConfirmGenerateOpen] = useState(false);

  const documentQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => fetchDocument(documentId),
  });
  const reviewsQuery = useQuery({
    queryKey: ["reviews", documentId],
    queryFn: () => fetchReviewsForDocument(documentId),
  });
  const reviewedDocumentsQuery = useQuery({
    queryKey: ["reviewedDocuments", documentId],
    queryFn: () => fetchReviewedDocumentsForDocument(documentId),
  });

  const latestReview = reviewsQuery.data?.[0] ?? null;
  const reviewedDocuments = reviewedDocumentsQuery.data ?? [];

  const startReviewMutation = useMutation({
    mutationFn: () => startReview(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("AI review complete.");
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "The review could not be completed."));
    },
  });

  const generateMutation = useMutation({
    mutationFn: (reviewId: string) => generateReviewedDocument(reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviewedDocuments", documentId] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success("Reviewed document generated.");
      setConfirmGenerateOpen(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Could not generate the reviewed document."));
      setConfirmGenerateOpen(false);
    },
  });

  const downloadMutation = useMutation({
    mutationFn: ({ id, filename }: { id: string; filename: string }) =>
      downloadReviewedDocument(id, filename),
    onError: (error) => {
      toast.error(getErrorMessage(error, "Download failed."));
    },
  });

  if (documentQuery.isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (documentQuery.isError || !documentQuery.data) {
    return (
      <EmptyState
        icon={<FileX className="h-5 w-5" />}
        title="Document not found"
        description="It may have been removed, or the link is incorrect."
        action={
          <Link href="/dashboard/documents">
            <Button variant="secondary">Back to Documents</Button>
          </Link>
        }
      />
    );
  }

  const document = documentQuery.data;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col gap-6"
    >
      <div>
        <Link
          href="/dashboard/documents"
          className="inline-flex items-center gap-1 text-xs font-medium text-foreground/60 hover:underline"
        >
          <ArrowLeft className="h-3 w-3" />
          Back to Documents
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <h1 className="text-lg font-semibold">{document.original_filename}</h1>
          <DocumentStatusBadge status={document.status} />
          <ReviewStatusBadge reviewStatus={latestReview?.status ?? null} />
        </div>
        {latestReview && (
          <p className="mt-1 text-sm text-foreground/60">Agreement type: {latestReview.agreement_type}</p>
        )}
      </div>

      <motion.div {...fadeUp} transition={{ duration: 0.25, delay: 0.05 }}>
        <Card>
          <CardHeader title="Document Information" />
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-foreground/60">Uploaded</dt>
              <dd className="mt-0.5 font-medium">{formatDate(document.created_at)}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Size</dt>
              <dd className="mt-0.5 font-medium">{formatBytes(document.size_bytes)}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Paragraphs</dt>
              <dd className="mt-0.5 font-medium">{document.paragraph_count}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Tables</dt>
              <dd className="mt-0.5 font-medium">{document.table_count}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Sections</dt>
              <dd className="mt-0.5 font-medium">{document.section_count}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Word count</dt>
              <dd className="mt-0.5 font-medium">{document.word_count}</dd>
            </div>
          </dl>

          <div className="mt-5 flex flex-wrap gap-2 border-t border-black/10 pt-4 dark:border-white/10">
            <Button
              variant={latestReview ? "secondary" : "primary"}
              onClick={() => startReviewMutation.mutate()}
              isLoading={startReviewMutation.isPending}
              disabled={document.status !== "processed"}
            >
              {latestReview ? (
                <RefreshCw className="h-4 w-4" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {latestReview ? "Re-run AI Review" : "Start AI Review"}
            </Button>
            <Button
              variant="primary"
              onClick={() => setConfirmGenerateOpen(true)}
              disabled={!latestReview || latestReview.findings.length === 0}
            >
              <FileOutput className="h-4 w-4" />
              Generate Reviewed Document
            </Button>
          </div>
        </Card>
      </motion.div>

      <motion.div {...fadeUp} transition={{ duration: 0.25, delay: 0.1 }}>
        <Card>
          <CardHeader
            title="Review Findings"
            description={latestReview ? `${latestReview.findings.length} finding(s) found` : undefined}
          />
          {reviewsQuery.isLoading && <SkeletonRows rows={3} />}
          {!reviewsQuery.isLoading && !latestReview && (
            <EmptyState
              icon={<FileSearch className="h-5 w-5" />}
              title="No review yet"
              description="Start an AI review to see clause-by-clause findings here."
            />
          )}
          {latestReview && latestReview.findings.length === 0 && (
            <EmptyState
              icon={<ShieldCheck className="h-5 w-5" />}
              title="No issues found"
              description="The AI did not flag any clauses in this document."
            />
          )}
          {latestReview && latestReview.findings.length > 0 && (
            <FindingsTable findings={latestReview.findings} onSelect={setSelectedFinding} />
          )}
        </Card>
      </motion.div>

      <motion.div {...fadeUp} transition={{ duration: 0.25, delay: 0.15 }}>
        <Card>
          <CardHeader title="Reviewed Documents" description="Every generation is kept as a new version." />
          {reviewedDocumentsQuery.isLoading && <SkeletonRows rows={2} />}
          {!reviewedDocumentsQuery.isLoading && reviewedDocuments.length === 0 && (
            <EmptyState
              icon={<FileOutput className="h-5 w-5" />}
              title="No reviewed document yet"
              description="Generate one from the findings above once you're ready."
            />
          )}
          {reviewedDocuments.length > 0 && (
            <ul className="flex flex-col divide-y divide-black/5 dark:divide-white/5">
              {reviewedDocuments.map((rd) => (
                <li key={rd.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <p className="text-sm font-medium">Version {rd.version}</p>
                    <p className="text-xs text-foreground/60">
                      {formatDate(rd.created_at)} · {rd.comment_count} comments · {rd.tracked_change_count}{" "}
                      tracked changes
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    isLoading={downloadMutation.isPending && downloadMutation.variables?.id === rd.id}
                    onClick={() =>
                      downloadMutation.mutate({
                        id: rd.id,
                        filename: `reviewed_v${rd.version}_${document.original_filename}`,
                      })
                    }
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </motion.div>

      <ConfirmDialog
        open={confirmGenerateOpen}
        title="Generate reviewed document?"
        description="This creates a new DOCX with comments, highlights, and tracked changes applied from the current findings. Previous versions are kept."
        confirmLabel="Generate"
        isLoading={generateMutation.isPending}
        onCancel={() => setConfirmGenerateOpen(false)}
        onConfirm={() => {
          if (latestReview) generateMutation.mutate(latestReview.id);
        }}
      />

      <SidePanel
        open={selectedFinding !== null}
        title="Finding Details"
        onClose={() => setSelectedFinding(null)}
      >
        {selectedFinding && <FindingDetailPanel finding={selectedFinding} />}
      </SidePanel>
    </motion.div>
  );
}
