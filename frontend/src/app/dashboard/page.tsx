"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { fetchDocuments } from "@/lib/api/documents";
import { fetchHealth } from "@/lib/api/health";
import { Card, CardHeader } from "@/components/ui/Card";
import { Skeleton, SkeletonRows } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { DocumentStatusBadge, ReviewStatusBadge } from "@/components/StatusBadge";
import { formatRelativeTime } from "@/lib/format";

function StatCard({ label, value, isLoading }: { label: string; value: number; isLoading: boolean }) {
  return (
    <Card>
      <p className="text-xs font-medium text-foreground/60">{label}</p>
      {isLoading ? (
        <Skeleton className="mt-2 h-8 w-16" />
      ) : (
        <p className="mt-1 text-2xl font-semibold">{value}</p>
      )}
    </Card>
  );
}

export default function DashboardPage() {
  const documentsQuery = useQuery({ queryKey: ["documents"], queryFn: fetchDocuments });
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 30_000 });

  const documents = documentsQuery.data ?? [];
  const total = documents.length;
  const reviewed = documents.filter((d) => d.latest_review_id !== null).length;
  const pending = total - reviewed;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Total Documents" value={total} isLoading={documentsQuery.isLoading} />
        <StatCard label="Reviewed" value={reviewed} isLoading={documentsQuery.isLoading} />
        <StatCard label="Pending Review" value={pending} isLoading={documentsQuery.isLoading} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Recent Activity"
            action={
              <Link href="/dashboard/documents" className="text-xs font-medium text-foreground/70 hover:underline">
                View all
              </Link>
            }
          />
          {documentsQuery.isLoading && <SkeletonRows rows={4} />}
          {documentsQuery.isError && (
            <p className="text-sm text-red-600 dark:text-red-400">Could not load recent activity.</p>
          )}
          {documentsQuery.isSuccess && documents.length === 0 && (
            <EmptyState
              title="No documents yet"
              description="Upload your first contract to get started."
              action={
                <Link href="/dashboard/documents">
                  <Button>Upload a document</Button>
                </Link>
              }
            />
          )}
          {documentsQuery.isSuccess && documents.length > 0 && (
            <ul className="flex flex-col divide-y divide-black/10 dark:divide-white/10">
              {documents.slice(0, 5).map((doc) => (
                <li key={doc.id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <Link
                      href={`/dashboard/documents/${doc.id}`}
                      className="block truncate text-sm font-medium hover:underline"
                    >
                      {doc.original_filename}
                    </Link>
                    <p className="text-xs text-foreground/60">{formatRelativeTime(doc.created_at)}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <DocumentStatusBadge status={doc.status} />
                    <ReviewStatusBadge reviewStatus={doc.review_status} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <CardHeader title="System Status" />
          {healthQuery.isLoading && <p className="text-sm">Checking backend…</p>}
          {healthQuery.isError && (
            <p className="text-sm text-red-600 dark:text-red-400">Backend is unreachable.</p>
          )}
          {healthQuery.data && (
            <dl className="flex flex-col gap-3 text-sm">
              <div className="flex items-center justify-between">
                <dt className="text-foreground/60">API</dt>
                <dd className="font-medium">{healthQuery.data.status}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-foreground/60">Environment</dt>
                <dd className="font-medium">{healthQuery.data.environment}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-foreground/60">Database</dt>
                <dd className="font-medium">{healthQuery.data.database}</dd>
              </div>
            </dl>
          )}
        </Card>
      </div>
    </div>
  );
}
