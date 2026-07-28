"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Eye, FileSearch, Search, Sparkles } from "lucide-react";

import { DocumentListItem, fetchDocuments, uploadDocument } from "@/lib/api/documents";
import { startReview } from "@/lib/api/reviews";
import { getErrorMessage } from "@/lib/api/errors";
import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileDropzone } from "@/components/FileDropzone";
import { DocumentStatusBadge, ReviewStatusBadge } from "@/components/StatusBadge";
import { formatBytes, formatDate } from "@/lib/format";

function DocumentsTable({
  documents,
  onQuickReview,
  reviewingDocumentId,
}: {
  documents: DocumentListItem[];
  onQuickReview: (documentId: string) => void;
  reviewingDocumentId: string | undefined;
}) {
  if (documents.length === 0) {
    return (
      <EmptyState
        icon={<FileSearch className="h-5 w-5" />}
        title="No matching documents"
        description="Try a different search, or upload a new contract above."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-black/10 text-left text-xs text-foreground/60 dark:border-white/10">
            <th className="py-2 pr-4 font-medium">Filename</th>
            <th className="py-2 pr-4 font-medium">Agreement Type</th>
            <th className="py-2 pr-4 font-medium">Status</th>
            <th className="py-2 pr-4 font-medium">Review</th>
            <th className="py-2 pr-4 font-medium">Uploaded</th>
            <th className="py-2 pr-4 font-medium">Size</th>
            <th className="py-2 pr-0 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-black/5 dark:divide-white/5">
          {documents.map((doc, index) => (
            <motion.tr
              key={doc.id}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(index * 0.03, 0.3) }}
              className="hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
            >
              <td className="max-w-xs truncate py-3 pr-4 font-medium">{doc.original_filename}</td>
              <td className="py-3 pr-4 text-foreground/70">{doc.agreement_type ?? "—"}</td>
              <td className="py-3 pr-4">
                <DocumentStatusBadge status={doc.status} />
              </td>
              <td className="py-3 pr-4">
                <ReviewStatusBadge reviewStatus={doc.review_status} />
              </td>
              <td className="py-3 pr-4 text-foreground/70">{formatDate(doc.created_at)}</td>
              <td className="py-3 pr-4 text-foreground/70">{formatBytes(doc.size_bytes)}</td>
              <td className="py-3 pr-0">
                <div className="flex items-center justify-end gap-3">
                  {!doc.review_status && doc.status === "processed" && (
                    <button
                      onClick={() => onQuickReview(doc.id)}
                      disabled={reviewingDocumentId === doc.id}
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-foreground/80 hover:text-foreground disabled:opacity-50"
                      title="Start AI review without opening the document"
                    >
                      {reviewingDocumentId === doc.id ? (
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      ) : (
                        <Sparkles className="h-3.5 w-3.5" />
                      )}
                      Review
                    </button>
                  )}
                  <Link
                    href={`/dashboard/documents/${doc.id}`}
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-foreground hover:underline"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    View
                  </Link>
                </div>
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const queryClient = useQueryClient();
  const router = useRouter();

  const documentsQuery = useQuery({ queryKey: ["documents"], queryFn: fetchDocuments });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, setUploadProgress),
    onSuccess: (document) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      toast.success(`"${document.original_filename}" uploaded and parsed.`);
      // Go straight to the document instead of leaving the user to find it
      // in the list and open it themselves — this was the main friction
      // point flagged after the first demo.
      router.push(`/dashboard/documents/${document.id}`);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Upload failed. Please try again."));
    },
    onSettled: () => setUploadProgress(0),
  });

  const quickReviewMutation = useMutation({
    mutationFn: (documentId: string) => startReview(documentId),
    onSuccess: (_review, documentId) => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      queryClient.invalidateQueries({ queryKey: ["reviews", documentId] });
      toast.success("AI review complete.", {
        action: {
          label: "View findings",
          onClick: () => router.push(`/dashboard/documents/${documentId}`),
        },
      });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "The review could not be completed."));
    },
  });

  const documents = documentsQuery.data ?? [];
  const filtered = search.trim()
    ? documents.filter((doc) => doc.original_filename.toLowerCase().includes(search.trim().toLowerCase()))
    : documents;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader title="Upload a contract" description="DOCX files only, up to 25MB." />
        <FileDropzone
          onFileSelected={(file) => uploadMutation.mutate(file)}
          isUploading={uploadMutation.isPending}
          progress={uploadProgress}
        />
      </Card>

      <Card>
        <CardHeader
          title="All Documents"
          action={
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-foreground/40" />
              <input
                type="search"
                placeholder="Search by filename…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-56 rounded-md border border-black/15 bg-background py-1.5 pl-8 pr-3 text-sm outline-none focus:border-foreground/40 dark:border-white/20"
              />
            </div>
          }
        />
        {documentsQuery.isLoading && <SkeletonRows rows={5} />}
        {documentsQuery.isError && (
          <p className="text-sm text-red-600 dark:text-red-400">Could not load documents.</p>
        )}
        {documentsQuery.isSuccess && documents.length === 0 && (
          <EmptyState
            title="No documents uploaded yet"
            description="Drag a DOCX contract into the box above to get started."
          />
        )}
        {documentsQuery.isSuccess && documents.length > 0 && (
          <DocumentsTable
            documents={filtered}
            onQuickReview={(id) => quickReviewMutation.mutate(id)}
            reviewingDocumentId={quickReviewMutation.isPending ? quickReviewMutation.variables : undefined}
          />
        )}
      </Card>
    </div>
  );
}
