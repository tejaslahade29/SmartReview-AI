"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/lib/api/health";

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border border-black/10 p-4 dark:border-white/10">
        <h2 className="mb-2 text-sm font-semibold text-foreground/70">
          System Status
        </h2>
        {isLoading && <p className="text-sm">Checking backend...</p>}
        {isError && (
          <p className="text-sm text-red-600 dark:text-red-400">
            Backend is unreachable.
          </p>
        )}
        {data && (
          <dl className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-foreground/60">API</dt>
              <dd className="font-medium">{data.status}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Environment</dt>
              <dd className="font-medium">{data.environment}</dd>
            </div>
            <div>
              <dt className="text-foreground/60">Database</dt>
              <dd className="font-medium">{data.database}</dd>
            </div>
          </dl>
        )}
      </div>
    </div>
  );
}
