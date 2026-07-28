"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Activity, CheckCircle2, Clock, FileStack, Inbox } from "lucide-react";

import { fetchDocuments } from "@/lib/api/documents";
import { fetchHealth } from "@/lib/api/health";
import { Card, CardHeader } from "@/components/ui/Card";
import { Skeleton, SkeletonRows } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { DocumentStatusBadge, ReviewStatusBadge } from "@/components/StatusBadge";
import { formatRelativeTime } from "@/lib/format";

const STAT_ICON_CLASSES: Record<string, string> = {
  total: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  reviewed: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  pending: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

function StatCard({
  label,
  value,
  isLoading,
  icon,
  tone,
  delay,
}: {
  label: string;
  value: number;
  isLoading: boolean;
  icon: React.ReactNode;
  tone: keyof typeof STAT_ICON_CLASSES;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
    >
      <Card className="flex items-center gap-4">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${STAT_ICON_CLASSES[tone]}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs font-medium text-foreground/60">{label}</p>
          {isLoading ? (
            <Skeleton className="mt-2 h-7 w-12" />
          ) : (
            <p className="mt-0.5 text-2xl font-semibold">{value}</p>
          )}
        </div>
      </Card>
    </motion.div>
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
        <StatCard
          label="Total Documents"
          value={total}
          isLoading={documentsQuery.isLoading}
          icon={<FileStack className="h-5 w-5" />}
          tone="total"
          delay={0}
        />
        <StatCard
          label="Reviewed"
          value={reviewed}
          isLoading={documentsQuery.isLoading}
          icon={<CheckCircle2 className="h-5 w-5" />}
          tone="reviewed"
          delay={0.05}
        />
        <StatCard
          label="Pending Review"
          value={pending}
          isLoading={documentsQuery.isLoading}
          icon={<Clock className="h-5 w-5" />}
          tone="pending"
          delay={0.1}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.15 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader
              title="Recent Activity"
              icon={<Activity className="h-4 w-4" />}
              action={
                <Link
                  href="/dashboard/documents"
                  className="text-xs font-medium text-foreground/70 hover:underline"
                >
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
                icon={<Inbox className="h-5 w-5" />}
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
                  <li
                    key={doc.id}
                    className="flex items-center justify-between gap-3 rounded-md py-3 transition-colors hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
                  >
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
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.2 }}
        >
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
                  <dd className="flex items-center gap-1.5 font-medium">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    {healthQuery.data.status}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-foreground/60">Environment</dt>
                  <dd className="font-medium">{healthQuery.data.environment}</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-foreground/60">Database</dt>
                  <dd className="flex items-center gap-1.5 font-medium">
                    <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    {healthQuery.data.database}
                  </dd>
                </div>
              </dl>
            )}
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
