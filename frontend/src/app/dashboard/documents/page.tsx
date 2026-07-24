"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { DocumentListItem, fetchDocuments, uploadDocument } from "@/lib/api/documents";
import { getErrorMessage } from "@/lib/api/errors";
import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileDropzone } from "@/components/FileDropzone";
import { DocumentStatusBadge, ReviewStatusBadge } from "@/components/StatusBadge";
import { formatBytes, formatDate } from "@/lib/format";

function DocumentsTable({ documents }: { documents: DocumentListItem[] }) {
  if (documents.length === 0) {
    return (
      <EmptyState
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
          {documents.map((doc) => (
            <tr key={doc.id}>
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
              <td className="py-3 pr-0 text-right">
                <Link
                  href={`/dashboard/documents/${doc.id}`}
                  className="text-sm font-medium text-foreground hover:underline"
                >
                  View
                </Link>
              </td>
            </tr>
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
      toast.success(`"${document.original_filename}" uploaded and parsed.`, {
        action: {
          label: "View",
          onClick: () => router.push(`/dashboard/documents/${document.id}`),
        },
      });
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Upload failed. Please try again."));
    },
    onSettled: () => setUploadProgress(0),
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
            <input
              type="search"
              placeholder="Search by filename…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-56 rounded-md border border-black/15 bg-background px-3 py-1.5 text-sm outline-none focus:border-foreground/40 dark:border-white/20"
            />
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
        {documentsQuery.isSuccess && documents.length > 0 && <DocumentsTable documents={filtered} />}
      </Card>
    </div>
  );
}
