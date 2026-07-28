"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, LayoutDashboard, ScanSearch } from "lucide-react";

import { ThemeToggle } from "@/components/ThemeToggle";

const NAV_ITEMS = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Documents", href: "/dashboard/documents", icon: FileText },
];

function pageTitle(pathname: string): string {
  if (pathname === "/dashboard") return "Dashboard";
  if (pathname === "/dashboard/documents") return "Documents";
  if (pathname.startsWith("/dashboard/documents/")) return "Document Details";
  return "Dashboard";
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen flex-1">
      <aside className="hidden w-56 shrink-0 border-r border-black/10 px-4 py-6 dark:border-white/10 sm:block">
        <div className="mb-8 flex items-center gap-2 px-1 text-lg font-semibold">
          <ScanSearch className="h-5 w-5" />
          Contract Review
        </div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-black/5 text-foreground dark:bg-white/10"
                    : "text-foreground/80 hover:bg-black/5 dark:hover:bg-white/10"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-black/10 px-6 py-4 dark:border-white/10">
          <h1 className="text-base font-semibold">{pageTitle(pathname)}</h1>
          <ThemeToggle />
        </header>

        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
